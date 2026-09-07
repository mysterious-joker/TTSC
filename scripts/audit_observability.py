"""Catalog-only optimistic ceilings; not a deployable or target-aware agent."""
from __future__ import annotations

import argparse
from collections import Counter
from functools import lru_cache
import hashlib
import json
from pathlib import Path

from evaluator.local_evaluator import coarse_category, intent_card, load_jsonl


@lru_cache(maxsize=None)
def best_total(count: int, turn: int, objective: str) -> float:
    """Total reward over equiprobable indistinguishable products (unnormalized)."""
    if not count or turn > 10:
        return 0.0
    best = 0.0
    for width in range(1, min(count, 10) + 1):
        if objective == "hit_rate_at_10":
            immediate = float(width)
        elif objective == "mrr":
            immediate = sum(1.0 / rank for rank in range(1, width + 1))
        elif objective == "technical_score":
            immediate = sum(0.5 + 0.3 / rank + 0.02 * (11 - turn)
                            for rank in range(1, width + 1))
        else:
            raise ValueError(objective)
        best = max(best, immediate + best_total(count - width, turn + 1, objective))
    return best


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", default="data/catalog.jsonl", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    products = load_jsonl(args.catalog)
    groups = Counter()
    for product in products:
        card = intent_card(product)
        groups[(coarse_category(product.get("categories") or []),
                tuple(card["hard_constraints"]), tuple(card["soft_preferences"]))] += 1
    sizes = Counter(groups.values())
    objectives = ("hit_rate_at_10", "mrr", "technical_score")
    by_start = {
        str(start): {metric: sum(frequency * best_total(size, start, metric)
                                for size, frequency in sizes.items()) / len(products)
                     for metric in objectives}
        for start in (1, 3, 4)
    }
    result = {
        "assumptions": [
            "Target uniformly sampled from all 50,000 catalog products.",
            "No target-correlated profile signal; disclosure card granted free before first response.",
            "Each metric optimized independently; ceilings need not be jointly achievable.",
            "At most 10 products each turn, at most 10 turns; first appearance ends scoring.",
            "Duplicate signatures remain exchangeable; no hidden purchase distribution is inferred.",
        ],
        "catalog_sha256": hashlib.sha256(args.catalog.read_bytes()).hexdigest(),
        "catalog_rows": len(products), "signature_groups": len(groups),
        "group_size_distribution": dict(sorted(sizes.items())),
        "oracle_ceilings_by_first_eligible_turn": by_start,
        "oracle_ceilings_85pct_turn1_7_5pct_turn3_7_5pct_turn4": {
            metric: 0.85 * by_start["1"][metric] + 0.075 * by_start["3"][metric]
                    + 0.075 * by_start["4"][metric] for metric in objectives
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
