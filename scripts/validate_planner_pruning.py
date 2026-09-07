"""Differentially validate pruning against an explicit previous source file."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import time

from conversational_search import exposure
from conversational_search.protocol import DisclosureCard
from conversational_search.protocol_index import ProtocolResolution, ProtocolResolutionStatus, ResolvedCardGroup


def validate(reference_path, count=256, seed=202609074):
    spec = importlib.util.spec_from_file_location("unpruned_reference", reference_path)
    reference = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reference)
    rng = random.Random(seed)
    totals = {"reference_seconds": 0.0, "candidate_seconds": 0.0}
    widths = set()
    questions = set()
    vocabulary = ("cotton", "wool", "nylon", "color: red", "color: blue", "size wide",
                  "size narrow", "style loose", "running", "budget around $20", "generic", "feature")
    for case in range(count):
        size = rng.choice((2, 3, 5, 10, 11, 20, 30, 60))
        groups = []
        for i in range(size):
            if case % 4 == 0:
                # A named question bypasses shared opening values. Other cases
                # mix ambiguous cards, exhausted evidence and late horizons.
                values = ("generic detail", "shared detail", vocabulary[i % 10])
            else:
                values = tuple(dict.fromkeys(rng.choices(vocabulary, k=rng.randint(1, 4))))
            card = DisclosureCard("item", values[:2], values[2:])
            disclosed = () if case % 4 == 0 else tuple(v for v in values if rng.random() < 0.3)
            groups.append(ResolvedCardGroup(card, (str(i),), disclosed))
        ids = tuple(str(i) for i in range(size))
        resolution = ProtocolResolution(ProtocolResolutionStatus.EXACT, tuple(groups), ids, size, 0)
        turn = rng.randint(1, 9)
        top_k = rng.choice((1, 3, 10))
        started = time.perf_counter()
        expected = reference.plan_protocol_pareto_action(ids, resolution, current_turn=turn, top_k=top_k)
        totals["reference_seconds"] += time.perf_counter() - started
        started = time.perf_counter()
        actual = exposure.plan_protocol_pareto_action(ids, resolution, current_turn=turn, top_k=top_k)
        totals["candidate_seconds"] += time.perf_counter() - started
        if actual != expected:
            raise AssertionError((case, turn, top_k, expected, actual))
        widths.add(actual[0])
        questions.add(actual[1])
    return {"cases": count, "seed": seed, "all_actions_identical": True,
            "reference_sha256": hashlib.sha256(reference_path.read_bytes()).hexdigest(),
            "candidate_sha256": hashlib.sha256(Path(exposure.__file__).read_bytes()).hexdigest(),
            "observed_widths": sorted(widths), "observed_questions": sorted(questions), **totals,
            "timing_note": "Sequential microcheck with reference first; not adoption timing evidence."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = validate(args.reference)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
