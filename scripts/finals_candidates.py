"""Explicit research arms; never imported by the submission entry point."""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

from conversational_search.protocol import PROTOCOL_ACTIONS, CandidateReplyStatus, remaining_reply
from conversational_search.utility_planner import hit_utility


def hypotheses_for(ids, resolution):
    by_id = {asin: (g.card, g.disclosed_values)
             for g in resolution.groups for asin in g.parent_asins}
    order = tuple(dict.fromkeys((*ids, *resolution.candidate_ids)))
    return tuple((asin, *by_id[asin]) for asin in order if asin in by_id)


def branches_for(hypotheses, question):
    """Group by the exact *visible text*, retaining deterministic candidate order."""
    groups = {}
    for asin, card, disclosed in hypotheses:
        reply = remaining_reply(card, question, disclosed)
        updated = tuple(sorted(set(disclosed).union(reply.values)))
        groups.setdefault(reply.reply_text, []).append((asin, card, updated))
    return tuple(tuple(group) for group in groups.values())


def answer_value_action(ids, resolution, *, current_turn, top_k):
    """Rank-one probe plus a label-free, full-support one-step question value."""
    hypotheses = hypotheses_for(ids, resolution)[1:]
    best_question, best_value = "other", -1.0
    for question in PROTOCOL_ACTIONS:
        if question in {"category", "brand"}:
            continue  # No classifier branch emits these attributes.
        value = sum(hit_utility(current_turn + 1, rank)
                    for branch in branches_for(hypotheses, question)
                    for rank in range(1, min(top_k, len(branch)) + 1))
        if value > best_value + 1e-12:
            best_value, best_question = value, question
    return 1, best_question


def two_step_action(ids, resolution, *, current_turn, top_k):
    """Finite two-reply lookahead; terminal uncertainty is explicitly truncated."""
    from conversational_search.exposure import _protocol_enumeration_plan
    hypotheses = hypotheses_for(ids, resolution)
    if len(hypotheses) > 200 or set(ids) != set(resolution.candidate_ids):
        return answer_value_action(ids, resolution, current_turn=current_turn, top_k=top_k)

    @lru_cache(maxsize=None)
    def solve(remaining, turn, depth):
        if not remaining or turn > 10:
            return 0.0, 0, None
        count = len(remaining)
        if turn == 10 or depth == 0:
            width = min(top_k, count)
            return sum(hit_utility(turn, rank) for rank in range(1, width + 1)), width, None
        live = any(remaining_reply(card, "other", disclosed).status
                   is CandidateReplyStatus.DISCLOSURE for _, card, disclosed in remaining)
        if not live:
            value, width = _protocol_enumeration_plan(count, current_turn=turn, top_k=top_k)
            return count * value, width, None
        best = (-1.0, 1, "other")
        for width in range(1, min(top_k, count) + 1):
            immediate = sum(hit_utility(turn, rank) for rank in range(1, width + 1))
            seen = set()
            for question in PROTOCOL_ACTIONS:
                if question in {"category", "brand"}:
                    continue
                branches = branches_for(remaining[width:], question)
                if branches in seen:
                    continue
                seen.add(branches)
                value = immediate + sum(solve(branch, turn + 1, depth - 1)[0] for branch in branches)
                if value > best[0] + 1e-12:
                    best = value, width, question
        return best

    _, width, question = solve(hypotheses, current_turn, 2)
    return width, question or "other"


def make_agent(arm: str, catalog: Path):
    from starter.agent import Agent as Baseline
    from conversational_search import exposure, service
    diagnostics = {"interventions": 0, "errors": 0}

    if arm in {"support_cold_prior", "support_review_prior"}:
        with Path(catalog).open() as handle:
            counts = {r["parent_asin"]: int(r.get("rating_number") or 0)
                      for r in map(json.loads, handle)}
        original_fuse = service.fuse_protocol_candidates
        context = {"active": False}

        def fuse(resolution, preferred_ids, *, limit):
            if context["active"] and resolution.exact:
                diagnostics["interventions"] += 1
                return tuple(sorted(resolution.candidate_ids,
                                    key=lambda asin: -counts.get(asin, 0))[:limit])
            return original_fuse(resolution, preferred_ids, limit=limit)

        # Research runners construct only one agent per fresh process.
        service.fuse_protocol_candidates = fuse

        class FullSupportPrior(Baseline):
            def respond(self, session_id, user_message, turn, top_k):
                context["active"] = arm == "support_review_prior"
                if arm == "support_cold_prior":
                    from conversational_search.intent import apply_user_message
                    state = apply_user_message(self._sessions[session_id], user_message, turn)
                    context["active"] = bool(turn == 1 and state.category
                                             and not state.requirements and not state.excluded)
                try:
                    return super().respond(session_id, user_message, turn, top_k)
                finally:
                    context["active"] = False

        agent = FullSupportPrior(catalog)
        agent.research_diagnostics = diagnostics
        return agent

    if arm in {"answer_value", "two_step_value"}:
        planner = answer_value_action if arm == "answer_value" else two_step_action
        def observed_planner(*args, **kwargs):
            diagnostics["interventions"] += 1
            try:
                return planner(*args, **kwargs)
            except Exception:
                diagnostics["errors"] += 1
                raise
        exposure.plan_protocol_pareto_action = observed_planner
        agent = Baseline(catalog)
        agent.research_diagnostics = diagnostics
        return agent
    raise ValueError(f"unknown experimental arm {arm}")
