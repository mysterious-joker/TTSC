#!/usr/bin/env python3
"""Paired comparison; aggregate output contains no target IDs or transcripts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def utility(session: dict) -> float:
    turn = session["first_hit_turn"] if session["hit"] else 11
    return 0.5 * int(session["hit"]) + 0.3 * session["reciprocal_rank"] + 0.02 * (11 - turn)


def compare(baseline: dict, candidate: dict, *, family_size: int = 3, gate: str = "pointwise") -> dict:
    if isinstance(family_size, bool) or not isinstance(family_size, int) or family_size < 1:
        raise ValueError("family_size must be a positive integer")
    if gate not in {"pointwise", "aggregate"}:
        raise ValueError("gate must be pointwise or aggregate")
    left = {row["sample_id"]: row for row in baseline["sessions"]}
    right = {row["sample_id"]: row for row in candidate["sessions"]}
    if (not left or left.keys() != right.keys()
            or len(left) != len(baseline["sessions"])
            or len(right) != len(candidate["sessions"])):
        raise ValueError("paired results require identical, unique sample IDs")
    if any(left[key]["scenario_type"] != right[key]["scenario_type"] for key in left):
        raise ValueError("paired scenario labels do not match")
    for field in ("catalog_sha256", "dataset_sha256", "evaluator_sha256", "wording"):
        a = baseline.get("measurement", {}).get(field)
        b = candidate.get("measurement", {}).get(field)
        if a is not None and b is not None and a != b:
            raise ValueError(f"paired {field} differs")
    ids = sorted(left)
    delta = np.array([utility(right[key]) - utility(left[key]) for key in ids])
    rng = np.random.default_rng(20260907)
    # Twenty thousand paired bootstrap draws, with a multiplicity-adjusted
    # one-sided bound for the explicitly declared hypothesis family.
    draws = np.concatenate([
        delta[rng.integers(len(delta), size=(1000, len(delta)))].mean(axis=1)
        for _ in range(20)
    ])
    lower = float(np.quantile(draws, 0.05 / family_size))
    # Exact zero can acquire a tiny positive residue when turn gains and
    # losses cancel. Use the same resolution as the session/mean comparisons;
    # rounding noise is not a strictly positive confidence bound.
    if abs(lower) <= 1e-12:
        lower = 0.0
    scenarios = {}
    for scenario in sorted({row["scenario_type"] for row in left.values()}):
        selected = [i for i, key in enumerate(ids) if left[key]["scenario_type"] == scenario]
        scenarios[scenario] = {
            "n": len(selected), "utility_delta": float(delta[selected].mean()),
            "regressions": int((delta[selected] < -1e-12).sum()),
        }
    lost_hits = sum(left[key]["hit"] and not right[key]["hit"] for key in ids)
    metric_deltas = {
        "hit_rate": sum(int(right[key]["hit"]) - int(left[key]["hit"]) for key in ids) / len(ids),
        "mrr": sum(right[key]["reciprocal_rank"] - left[key]["reciprocal_rank"] for key in ids) / len(ids),
        "turn_efficiency": sum(
            ((left[key]["first_hit_turn"] if left[key]["hit"] else 11)
             - (right[key]["first_hit_turn"] if right[key]["hit"] else 11)) / 10 for key in ids
        ) / len(ids),
    }
    measured = candidate.get("measurement", {})
    reasons = []
    if float(delta.mean()) <= 1e-12:
        reasons.append("no_strict_score_improvement")
    if gate == "pointwise" and (delta < -1e-12).any():
        reasons.append("individual_session_regression")
    if gate == "pointwise" and lost_hits:
        reasons.append("lost_hits")
    if gate == "pointwise" and any(row["utility_delta"] < -1e-12 for row in scenarios.values()):
        reasons.append("scenario_regression")
    if gate == "aggregate":
        reasons.extend(f"aggregate_{key}_regression" for key, value in metric_deltas.items() if value < -1e-12)
    if lower <= 0:
        reasons.append("bootstrap_lower_bound_not_positive")
    if measured.get("exceptions", 0) or measured.get("invalid_outputs", 0):
        reasons.append("runtime_or_contract_failure")
    if measured.get("research_diagnostics", {}).get("errors", 0):
        reasons.append("internal_research_failure")
    return {
        "gate": gate, "aggregate_metric_deltas": metric_deltas,
        "n": len(ids), "mean_utility_delta": float(delta.mean()),
        "improved_sessions": int((delta > 1e-12).sum()),
        "regressed_sessions": int((delta < -1e-12).sum()),
        "unchanged_sessions": int((np.abs(delta) <= 1e-12).sum()),
        "lost_hits": int(lost_hits),
        "gained_hits": sum(not left[key]["hit"] and right[key]["hit"] for key in ids),
        "one_sided_bootstrap_lower_bound": lower,
        "alpha": 0.05 / family_size, "bootstrap_draws": 20000,
        "scenario_deltas": scenarios,
        "development_gate_pass": not reasons, "rejection_reasons": reasons,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--family-size", default=3, type=int)
    parser.add_argument("--gate", choices=("pointwise", "aggregate"), default="pointwise")
    args = parser.parse_args()
    result = compare(json.loads(args.baseline.read_text()), json.loads(args.candidate.read_text()),
                     family_size=args.family_size, gate=args.gate)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
