"""Fixed, mutually target-disjoint sensitivity suites; no hidden data access."""
from __future__ import annotations

import argparse
from collections import defaultdict, Counter
import hashlib
import json
import math
from pathlib import Path
import random

from evaluator.local_evaluator import coarse_category, load_jsonl


def sample_targets(products, count, distribution, rng):
    ids = sorted(products)
    if distribution == "uniform":
        return rng.sample(ids, count)
    if distribution == "weighted":
        # Exponential race: weighted sampling without replacement. Sqrt reduces
        # concentration; the exponent is declared rather than fit to outcomes.
        keys = [(math.log(1 - rng.random()) / math.sqrt(1 + max(0, int(products[a].get("rating_number") or 0))), a)
                for a in ids]
        return [a for _, a in sorted(keys, reverse=True)[:count]]
    if distribution != "category":
        raise ValueError("unknown distribution")
    groups = defaultdict(list)
    for asin in ids:
        groups[coarse_category(products[asin].get("categories") or [])].append(asin)
    categories = sorted(groups)
    selected = []
    for _ in range(count):
        category = rng.choice(categories)
        group = groups[category]
        index = rng.randrange(len(group))
        selected.append(group.pop(index))
        if not group:
            categories.remove(category)
    return selected


def generate(catalog, public, exclude, output, seed):
    if output.exists():
        raise ValueError("output must be new; never replace consumed samples")
    profiles = [row["user_profile"] for row in load_jsonl(public)]
    excluded = {row["ground_truth"]["parent_asin"] for path in (public, *exclude)
                for row in load_jsonl(path)}
    products = {row["parent_asin"]: row for row in load_jsonl(catalog)
                if row["parent_asin"] not in excluded}
    rng = random.Random(seed)
    output.mkdir(parents=True)
    manifest = {"seed": seed, "excluded_target_count": len(excluded), "suites": {}}
    specs = (("development-weighted", "weighted", 800),
             ("development-category", "category", 800),
             ("confirmation-uniform", "uniform", 1600),
             ("confirmation-weighted", "weighted", 1600),
             ("confirmation-category", "category", 800))
    for name, distribution, count in specs:
        targets = sample_targets(products, count, distribution, rng)
        scenarios = [s for s, w in (("buying", 8), ("browsing", 8), ("intent_override", 3), ("boundary", 1))
                     for _ in range(count * w // 20)]
        rng.shuffle(scenarios)
        rng.shuffle(targets)
        rows = [{"sample_id": f"round4_{seed}_{name}_{i:04d}", "scenario_type": scenario,
                 "user_profile": rng.choice(profiles), "ground_truth": {"parent_asin": target}}
                for i, (scenario, target) in enumerate(zip(scenarios, targets), 1)]
        data = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows).encode()
        (output / f"{name}.jsonl").write_bytes(data)
        manifest["suites"][name] = {"count": count, "distribution": distribution,
                                    "sha256": hashlib.sha256(data).hexdigest(),
                                    "scenarios": dict(Counter(scenarios))}
        for target in targets:
            del products[target]
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=Path("data/catalog.jsonl"))
    parser.add_argument("--public", type=Path, default=Path("data/public_set.jsonl"))
    parser.add_argument("--exclude", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    print(json.dumps(generate(args.catalog, args.public, args.exclude, args.output, args.seed), sort_keys=True))
