#!/usr/bin/env python3
"""Isolated, target-blind runtime experiments using the unchanged official harness.

External source trees must be explicitly supplied and reviewed before execution.
Each invocation runs one arm in a fresh process; no production policy is edited.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import re
import statistics
import sys
import time

from evaluator import local_evaluator as official
from starter.agent import Agent as Baseline


ARMS = ("baseline", "cold_start_reviews", "strict_top1", "lossless_slots", "catalog_category")


def paraphrase(message: str) -> str:
    """Change envelopes only; retain every catalog-derived value verbatim."""
    match = re.fullmatch(r"I'm looking for (.+)\. A key requirement is: (.+)\.", message)
    if match:
        return f"Help me find {match[1]}. It must have: {match[2]}."
    match = re.fullmatch(r"I'm looking for (.+), but I'm still exploring\.", message)
    if match:
        return f"I'm shopping for {match[1]}. I haven't decided on the details yet."
    match = re.fullmatch(r"I'm looking for (.+?)\. (.+)", message)
    if match:
        return f"Help me find {match[1]}. For now, I prefer {match[2]}"
    if message.startswith("For that, what matters is: "):
        return "My priorities are: " + message.removeprefix("For that, what matters is: ")
    if message.startswith("Actually, ignore my earlier preference. What I need is: "):
        return "Change of plan. Replace my earlier preference with: " + message.split("What I need is: ", 1)[1]
    match = re.fullmatch(r"I don't have a preference for (.+); please use your judgment\.", message)
    if match:
        return f"Any {match[1]} is fine with me."
    return message


class ObservedAgent:
    def __init__(self, agent: object, catalog_ids: set[str], wording: str):
        self.agent = agent
        self.catalog_ids = catalog_ids
        self.wording = wording
        self.latencies: list[float] = []
        self.errors = 0
        self.invalid_outputs = 0
        self.response_hash = hashlib.sha256()

    def reset(self, session_id: str, user_profile: dict) -> None:
        self.agent.reset(session_id, user_profile)

    def respond(self, session_id: str, user_message: str, turn: int, top_k: int) -> dict:
        message = paraphrase(user_message) if self.wording == "paraphrase" else user_message
        started = time.perf_counter()
        try:
            result = self.agent.respond(session_id, message, turn, top_k)
        except Exception:
            self.errors += 1
            raise
        finally:
            self.latencies.append(time.perf_counter() - started)
        recs = result.get("recommendations", []) if isinstance(result, dict) else []
        ids = [item.get("parent_asin") if isinstance(item, dict) else item for item in recs]
        if (not isinstance(result, dict) or not isinstance(result.get("message"), str)
                or result.get("ask_attribute") not in official.ALLOWED_ATTRIBUTES | {None}
                or len(ids) > top_k or len(set(ids)) != len(ids)
                or any(value not in self.catalog_ids for value in ids)):
            self.invalid_outputs += 1
        self.response_hash.update(json.dumps(result, sort_keys=True).encode())
        return result


def local_agent(arm: str, catalog: Path) -> object:
    if arm == "catalog_category":
        from conversational_search.decision import ProtocolObservation, recognize_protocol_observation
        from conversational_search.intent import apply_user_message
        categories = {}
        for row in official.load_jsonl(catalog):
            category = official.coarse_category(row.get("categories") or [])
            key = tuple(re.findall(r"\w+", category.casefold()))
            categories.setdefault(key, set()).add(category)
        lengths = sorted({len(key) for key in categories}, reverse=True)

        class CategoryGrounding(Baseline):
            def respond(self, session_id, user_message, turn, top_k):
                state = self._sessions[session_id]
                if (turn == 1 and state.category is None
                        and recognize_protocol_observation(user_message, turn)
                        is ProtocolObservation.UNSUPPORTED
                        and apply_user_message(state, user_message, turn).category is None):
                    # Only use an explicit catalog phrase in the first clause.
                    # Do not rewrite the transcript into an official template.
                    clause = re.split(r"[.;!?]", user_message, maxsplit=1)[0]
                    tokens = tuple(re.findall(r"\w+", clause.casefold()))
                    negative = {"not", "no", "without", "avoid", "instead", "except"}
                    if len(tokens) <= 60 and not negative.intersection(tokens):
                        for length in lengths:
                            matches = set().union(*(
                                categories.get(tokens[i:i+length], set())
                                for i in range(max(0, len(tokens)-length+1))
                            ))
                            if matches:
                                if len(matches) == 1:
                                    self._sessions[session_id] = replace(state, category=next(iter(matches)))
                                break
                return super().respond(session_id, user_message, turn, top_k)

        return CategoryGrounding(catalog)
    if arm == "cold_start_reviews":
        # Independent implementation of the published cold-start idea. No
        # labels, fitted coefficients, or product-specific exceptions.
        counts = {row["parent_asin"]: int(row.get("rating_number") or 0)
                  for row in official.load_jsonl(catalog)}

        class ColdStart(Baseline):
            def _apply_exact_evidence_ranking(self, state, ranked_ids, **kwargs):
                if (state.last_turn == 1 and not state.requirements
                        and not state.excluded and state.category):
                    ranked_ids = tuple(sorted(ranked_ids, key=lambda asin: -counts.get(asin, 0)))
                return super()._apply_exact_evidence_ranking(state, ranked_ids, **kwargs)

        return ColdStart(catalog)
    if arm == "strict_top1":
        # Change width before the service records shown/refuted IDs. Trimming
        # respond() afterwards would incorrectly refute unshown products.
        from conversational_search import exposure
        original = exposure.plan_evidence_gated_exposure

        def top1(*args, **kwargs):
            result = original(*args, **kwargs)
            if (kwargs["current_turn"] < 10 and result.width > 1
                    and result.status in {
                        exposure.EvidenceExposureStatus.POSTERIOR_ENUMERATION,
                        exposure.EvidenceExposureStatus.POSTERIOR_PARETO_HORIZON,
                    }):
                result = replace(result, width=1)
            return result

        exposure.plan_evidence_gated_exposure = top1
    agent = Baseline(catalog)
    if arm == "lossless_slots":
        from conversational_search.intent import LOSSLESS_MULTI_SLOT_INTENT_POLICY
        agent._intent_policy = LOSSLESS_MULTI_SLOT_INTENT_POLICY
    return agent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", default="data/catalog.jsonl", type=Path)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--arm", choices=ARMS, default="baseline")
    parser.add_argument("--external-root", type=Path)
    parser.add_argument("--module", default="starter.agent")
    parser.add_argument("--wording", choices=("official", "paraphrase"), default="official")
    args = parser.parse_args()
    if args.external_root and args.arm != "baseline":
        parser.error("external agents cannot be combined with local experiments")
    catalog_ids, categories, products = official.catalog_index(args.catalog)
    samples = official.load_jsonl(args.dataset)
    # The reviewed Vibe source has opt-in network/model hooks. Explicitly keep
    # its documented standard-library arm, without reading credential values.
    for key in tuple(os.environ):
        if key.startswith("COPILOT_"):
            del os.environ[key]
    started = time.perf_counter()
    if args.external_root:
        for key in tuple(sys.modules):
            if key == "starter" or key.startswith("starter."):
                del sys.modules[key]
        sys.path.insert(0, str(args.external_root.resolve()))
        cls = importlib.import_module(args.module).Agent
        agent = cls(args.catalog.resolve())
    else:
        agent = local_agent(args.arm, args.catalog)
    startup = time.perf_counter() - started
    observed = ObservedAgent(agent, catalog_ids, args.wording)
    started = time.perf_counter()
    result = official.evaluate(observed, samples, catalog_ids, categories, products)
    elapsed = time.perf_counter() - started
    latencies = sorted(observed.latencies)
    result["measurement"] = {
        "arm": args.arm, "external_root": str(args.external_root) if args.external_root else None,
        "wording": args.wording, "python": platform.python_version(), "platform": platform.platform(),
        "catalog_sha256": hashlib.sha256(args.catalog.read_bytes()).hexdigest(),
        "dataset_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
        "evaluator_sha256": hashlib.sha256(Path(official.__file__).read_bytes()).hexdigest(),
        "startup_seconds": startup, "evaluation_seconds": elapsed,
        "respond_mean_ms": statistics.fmean(latencies) * 1000,
        "respond_p95_ms": latencies[min(len(latencies)-1, int(len(latencies)*0.95))] * 1000,
        "respond_max_ms": max(latencies) * 1000, "calls": len(latencies),
        "exceptions": observed.errors, "invalid_outputs": observed.invalid_outputs,
        "response_sha256": observed.response_hash.hexdigest(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "sessions"}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
