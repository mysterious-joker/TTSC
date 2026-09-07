#!/usr/bin/env python3
"""Generate a frozen official-template suite with public target IDs excluded."""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path

from evaluator.local_evaluator import catalog_index, load_jsonl


SCENARIO_WEIGHTS = (
    ("buying", 8),
    ("browsing", 8),
    ("intent_override", 3),
    ("boundary", 1),
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default="data/catalog.jsonl")
    parser.add_argument("--exclude", default="data/public_set.jsonl")
    parser.add_argument("--output", required=True)
    parser.add_argument("--count", type=int, default=800)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    if args.count <= 0 or args.count % 20:
        raise SystemExit("--count must be a positive multiple of 20")

    excluded_samples = load_jsonl(args.exclude)
    excluded_ids = {
        str(sample["ground_truth"]["parent_asin"])
        for sample in excluded_samples
    }
    profiles = tuple(sample["user_profile"] for sample in excluded_samples)
    catalog_ids, _, _ = catalog_index(args.catalog)
    candidates = sorted(catalog_ids.difference(excluded_ids))
    if len(candidates) < args.count:
        raise SystemExit("catalog does not contain enough target-disjoint products")

    rng = random.Random(args.seed)
    targets = rng.sample(candidates, args.count)
    scenarios = [
        scenario
        for scenario, weight in SCENARIO_WEIGHTS
        for _ in range(args.count * weight // 20)
    ]
    rng.shuffle(scenarios)
    rng.shuffle(targets)

    samples = [
        {
            "sample_id": f"disjoint_{args.seed}_{index:04d}",
            "scenario_type": scenario,
            "user_profile": profiles[rng.randrange(len(profiles))],
            "ground_truth": {"parent_asin": target},
        }
        for index, (scenario, target) in enumerate(
            zip(scenarios, targets),
            start=1,
        )
    ]
    output = Path(args.output)
    output.write_text(
        "".join(json.dumps(sample, sort_keys=True) + "\n" for sample in samples),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "count": len(samples),
                "excluded_target_count": len(excluded_ids),
                "scenario_counts": dict(sorted(Counter(scenarios).items())),
                "seed": args.seed,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
