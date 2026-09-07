"""Frozen round-four paired accuracy and timing validation in fresh processes."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from scripts.benchmark_runtime_pairs import summarize
from scripts.compare_finalist_results import compare


def fingerprint(root):
    digest = hashlib.sha256()
    paths = [root / "agent.py", *root.glob("starter/**/*.py"),
             *root.glob("conversational_search/**/*.py"), *root.glob("scripts/*.py")]
    for path in sorted(paths):
        digest.update(str(path.relative_to(root)).encode() + b"\0" + path.read_bytes())
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research-root", type=Path, required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--stage", choices=("development", "confirmation"), required=True)
    args = parser.parse_args()
    research = args.research_root.resolve()
    candidate = args.candidate_root.resolve()
    baseline = research / "round4/baseline"
    output = research / f"round4/validation-{args.stage}"
    if output.exists():
        raise ValueError("validation directory already exists; never overwrite")
    if args.stage == "confirmation":
        previous = json.loads((research / "round4/validation-development/summary.json").read_text())
        if len(previous["suites"]) != 4 or not previous["all_gates_pass"]:
            raise ValueError("confirmation requires all development gates")
        if fingerprint(candidate) != previous["candidate_source_sha256"]:
            raise ValueError("candidate source changed after development validation")
        specs = (("uniform", research / "round4/suites/confirmation-uniform.jsonl", "official"),
                 ("weighted-language", research / "round4/suites/confirmation-weighted.jsonl", "punctuation"),
                 ("category-language", research / "round4/suites/confirmation-category.jsonl", "paraphrase"))
    else:
        specs = (("development", research / "development.jsonl", "official"),
                 ("public", candidate / "data/public_set.jsonl", "official"),
                 ("stress", research / "language-stress.jsonl", "paraphrase"),
                 ("weighted-language", research / "round4/suites/development-weighted.jsonl", "punctuation"))
    output.mkdir(parents=True)
    report = {"stage": args.stage, "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
              "candidate_source_sha256": fingerprint(candidate), "baseline_source_sha256": fingerprint(baseline),
              "suite_hashes": {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path, _ in specs},
              "suites": {}, "all_gates_pass": False}
    (output / "freeze.json").write_text(json.dumps(report, indent=2) + "\n")
    for name, dataset, wording in specs:
        pairs = []
        for repeat in range(3):
            pair = {}
            for side in (("baseline", "candidate") if repeat % 2 == 0 else ("candidate", "baseline")):
                root = baseline if side == "baseline" else candidate
                if fingerprint(root) != report[f"{side}_source_sha256"]:
                    raise ValueError("frozen source changed during validation")
                destination = output / f"{name}-{repeat + 1}-{side}.json"
                print(f"START {name} pair {repeat + 1} {side}", flush=True)
                run = subprocess.run([sys.executable, "-m", "scripts.benchmark_finalists",
                    "--dataset", str(dataset), "--wording", wording, "--output", str(destination)],
                    cwd=root, capture_output=True, text=True)
                (output / f"{name}-{repeat + 1}-{side}.log").write_text(run.stdout + run.stderr)
                if run.returncode:
                    raise RuntimeError(run.stderr[-4000:])
                pair[side] = json.loads(destination.read_text())
                print(json.dumps({"suite": name, "side": side, "repeat": repeat + 1,
                                  "score": pair[side]["recommended_technical_score"],
                                  "seconds": pair[side]["measurement"]["evaluation_seconds"]}), flush=True)
            pairs.append((pair["baseline"], pair["candidate"]))
        official = wording == "official"
        timing = summarize(pairs, alpha=.05 / len(specs), require_identical=official)
        accuracy = compare(*pairs[0], family_size=8, gate="aggregate")
        stable_accuracy = all(pairs[0][s]["sessions"] == p[s]["sessions"] for p in pairs for s in (0, 1))
        accuracy_pass = stable_accuracy and (timing["identical_sessions_and_responses"] if official
                                             else accuracy["development_gate_pass"])
        pass_gate = accuracy_pass and timing["aggregate_runtime_nonregression"] and timing["one_sided_saving_lower_bound_ms"] > 0
        report["suites"][name] = {"accuracy": accuracy, "timing": timing,
                                  "accuracy_gate_pass": accuracy_pass, "all_gates_pass": pass_gate,
                                  "metrics": {side: {key: pairs[0][i][key] for key in
                                      ("sample_count", "hit_rate_at_10", "mrr", "mttc", "efficiency", "recommended_technical_score", "scenario_metrics")}
                                      for i, side in enumerate(("baseline", "candidate"))}}
        report["all_gates_pass"] = all(s["all_gates_pass"] for s in report["suites"].values())
        (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({"suite": name, "accuracy_pass": accuracy_pass, "all_gates_pass": pass_gate,
                          "speedup": timing["median_end_to_end_speedup"]}), flush=True)
    if not report["all_gates_pass"]:
        raise SystemExit("one or more validation gates failed")


if __name__ == "__main__":
    main()
