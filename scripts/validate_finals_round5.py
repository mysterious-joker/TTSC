"""Frozen round-five generation and sequential paired validation."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import re
import statistics
import subprocess
import sys

from evaluator.local_evaluator import load_jsonl
from scripts.benchmark_runtime_pairs import summarize
from scripts.compare_finalist_results import compare
from scripts.generate_distribution_suites import sample_targets
from scripts.validate_finals_round4 import fingerprint


def generate(research, candidate):
    output = research / "round5/confirmation-data"
    if output.exists():
        raise ValueError("never overwrite generated confirmation")
    excluded_paths = [candidate / "data/public_set.jsonl", research / "development.jsonl",
                      research / "confirmation.jsonl", *sorted((research / "round4/suites").glob("*.jsonl"))]
    excluded = {r["ground_truth"]["parent_asin"] for p in excluded_paths for r in load_jsonl(p)}
    products = {r["parent_asin"]: r for r in load_jsonl(candidate / "data/catalog.jsonl")
                if r["parent_asin"] not in excluded}
    profiles = [r["user_profile"] for r in load_jsonl(candidate / "data/public_set.jsonl")]
    rng = random.Random(202609085)
    manifest = {"seed": 202609085, "excluded_targets": len(excluded), "suites": {}}
    output.mkdir(parents=True)
    for name, distribution, count in (("uniform", "uniform", 1600), ("weighted", "weighted", 1600),
                                      ("language", "category", 800)):
        targets = sample_targets(products, count, distribution, rng)
        scenarios = [s for s, w in (("buying", 8), ("browsing", 8), ("intent_override", 3), ("boundary", 1))
                     for _ in range(count * w // 20)]
        rng.shuffle(scenarios); rng.shuffle(targets)
        rows = [{"sample_id": f"round5_{name}_{i:04d}", "scenario_type": scenario,
                 "user_profile": rng.choice(profiles), "ground_truth": {"parent_asin": target}}
                for i, (target, scenario) in enumerate(zip(targets, scenarios))]
        data = "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows).encode()
        (output / f"{name}.jsonl").write_bytes(data)
        manifest["suites"][name] = {"count": count, "distribution": distribution,
                                   "sha256": hashlib.sha256(data).hexdigest()}
        for target in targets:
            del products[target]
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research-root", type=Path, required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--stage", choices=("generate", "development", "confirmation"), required=True)
    parser.add_argument("--iteration", choices=("v1", "v2", "v3"), default="v1")
    args = parser.parse_args()
    research, candidate = args.research_root.resolve(), args.candidate_root.resolve()
    if args.stage == "generate":
        print(json.dumps(generate(research, candidate)), flush=True)
        return
    baseline = research / "round5/baseline"
    suffix = "" if args.iteration == "v1" else f"-{args.iteration}"
    output = research / f"round5/validation-{args.stage}{suffix}"
    if output.exists():
        raise ValueError("validation output already exists")
    if args.stage == "development":
        specs = (("public", candidate / "data/public_set.jsonl", "official", True),
                 ("weighted", research / "round4/suites/development-weighted.jsonl", "official", args.iteration != "v3"),
                 ("uniform", research / "development.jsonl", "official", False),
                 ("category", research / "round4/suites/development-category.jsonl", "official", False),
                 ("language", research / "language-stress.jsonl", "paraphrase", False))
    else:
        previous = json.loads((research / f"round5/validation-development{suffix}/summary.json").read_text())
        if len(previous["suites"]) != 5 or not previous["all_gates_pass"]:
            raise ValueError("confirmation requires all development gates")
        if fingerprint(candidate) != previous["candidate_source_sha256"]:
            raise ValueError("candidate changed after development validation")
        if fingerprint(baseline) != previous["baseline_source_sha256"]:
            raise ValueError("baseline changed after development validation")
        specs = tuple((name, research / f"round5/confirmation-data/{name}.jsonl",
                       "paraphrase" if name == "language" else "official", name == "weighted")
                      for name in ("uniform", "weighted", "language"))
        manifest = json.loads((research / "round5/confirmation-data/manifest.json").read_text())
        if any(hashlib.sha256(p.read_bytes()).hexdigest() != manifest["suites"][n]["sha256"]
               for n, p, _, _ in specs):
            raise ValueError("confirmation data changed after generation")
    output.mkdir(parents=True)
    report = {"stage": args.stage, "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
              "candidate_source_sha256": fingerprint(candidate), "baseline_source_sha256": fingerprint(baseline),
              "suite_hashes": {n: hashlib.sha256(p.read_bytes()).hexdigest() for n, p, _, _ in specs},
              "suites": {}, "all_gates_pass": False}
    (output / "freeze.json").write_text(json.dumps(report, indent=2) + "\n")
    for name, data, wording, require_gain in specs:
        pairs = []
        for repeat in range(3):
            pair = {}
            for side in (("baseline", "candidate") if repeat % 2 == 0 else ("candidate", "baseline")):
                root = baseline if side == "baseline" else candidate
                if fingerprint(root) != report[f"{side}_source_sha256"]:
                    raise ValueError("source changed during frozen study")
                dest = output / f"{name}-{repeat + 1}-{side}.json"
                print(f"START {name} pair {repeat + 1} {side}", flush=True)
                command = [sys.executable, "-m", "scripts.benchmark_finalists", "--dataset", str(data),
                           "--wording", wording, "--output", str(dest)]
                if args.iteration == "v3":
                    command = ["/usr/bin/time", "-p", *command]
                run = subprocess.run(command,
                                     cwd=root, capture_output=True, text=True)
                (output / f"{name}-{repeat + 1}-{side}.log").write_text(run.stdout + run.stderr)
                if run.returncode:
                    raise RuntimeError(run.stderr[-2000:])
                pair[side] = json.loads(dest.read_text())
                if args.iteration == "v3":
                    process_time = {key: float(value) for key, value in re.findall(
                        r"^(real|user|sys)\s+(\d+(?:\.\d+)?)\s*$", run.stderr, re.M)}
                    if set(process_time) != {"real", "user", "sys"}:
                        raise ValueError("OS process timing was not captured")
                    pair[side]["measurement"]["process_cpu_seconds"] = process_time["user"] + process_time["sys"]
                    pair[side]["measurement"]["process_wall_seconds"] = process_time["real"]
                    dest.write_text(json.dumps(pair[side], indent=2) + "\n")
                print(json.dumps({"suite": name, "side": side, "repeat": repeat + 1,
                                  "score": pair[side]["recommended_technical_score"],
                                  "seconds": pair[side]["measurement"]["evaluation_seconds"]}), flush=True)
            pairs.append((pair["baseline"], pair["candidate"]))
        timing = summarize(pairs, alpha=.05 / len(specs), require_identical=wording != "official")
        accuracy = compare(*pairs[0], family_size=11 if args.iteration == "v3" else 7, gate="aggregate")
        if args.iteration == "v3":
            cpu = {label: statistics.median(p[i]["measurement"]["process_cpu_seconds"] for p in pairs)
                   for i, label in enumerate(("baseline", "candidate"))}
            timing["process_cpu_seconds_medians"] = cpu
            timing["process_cpu_nonregression"] = cpu["candidate"] <= cpu["baseline"]
            timing["aggregate_runtime_nonregression"] &= timing["process_cpu_nonregression"]
        stable = all(pairs[0][i]["sessions"] == p[i]["sessions"]
                     and pairs[0][i]["measurement"]["response_sha256"] == p[i]["measurement"]["response_sha256"]
                     for p in pairs for i in (0, 1))
        nonregression = all(d >= -1e-12 for d in accuracy["aggregate_metric_deltas"].values())
        accuracy_pass = stable and nonregression and (not require_gain or accuracy["development_gate_pass"])
        if wording != "official":
            accuracy_pass = accuracy_pass and timing["identical_sessions_and_responses"]
        passed = accuracy_pass and timing["aggregate_runtime_nonregression"]
        report["suites"][name] = {"accuracy": accuracy, "timing": timing, "requires_significant_gain": require_gain,
            "accuracy_gate_pass": accuracy_pass, "all_gates_pass": passed,
            "metrics": {s: {k: pairs[0][i][k] for k in ("sample_count", "hit_rate_at_10", "mrr", "mttc",
                "efficiency", "recommended_technical_score", "scenario_metrics")} for i, s in enumerate(("baseline", "candidate"))}}
        report["all_gates_pass"] = all(s["all_gates_pass"] for s in report["suites"].values())
        (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({"suite": name, "accuracy_pass": accuracy_pass, "all_gates_pass": passed,
                          "speedup": timing["median_end_to_end_speedup"]}), flush=True)
        if not passed:
            raise SystemExit("gate failed; stop before additional validation")


if __name__ == "__main__":
    main()
