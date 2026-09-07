"""Sequential, alternating baseline/candidate timing with response equivalence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import subprocess
import sys

import numpy as np


def summarize(pairs, *, alpha, require_identical=True):
    if len(pairs) != 3:
        raise ValueError("the frozen timing protocol requires three pairs")
    for baseline, candidate in pairs:
        if require_identical and baseline["sessions"] != candidate["sessions"]:
            raise ValueError("per-session behavior changed")
        if [(r["sample_id"], r["scenario_type"]) for r in baseline["sessions"]] != [
                (r["sample_id"], r["scenario_type"]) for r in candidate["sessions"]]:
            raise ValueError("paired session identities or order changed")
        for key in ("dataset_sha256", "catalog_sha256", "evaluator_sha256", "wording",
                    *(("response_sha256",) if require_identical else ())):
            if baseline["measurement"][key] != candidate["measurement"][key]:
                raise ValueError(f"paired {key} mismatch")
        for result in (baseline, candidate):
            if result["measurement"]["exceptions"] or result["measurement"]["invalid_outputs"]:
                raise ValueError("invalid runtime behavior")
            if len(result["timing"]["session_response_ms"]) != len(result["sessions"]):
                raise ValueError("timings do not align with sessions")
    for side in (0, 1):
        if len({pair[side]["measurement"]["runtime_source_sha256"] for pair in pairs}) != 1:
            raise ValueError("runtime source changed during the timing study")
    # Match sessions in evaluator order; block by session rather than treating
    # correlated turns as independent observations. Median across repetitions
    # reduces sensitivity to isolated scheduling pauses. All repetitions remain.
    savings = np.median(np.array([
        np.array(a["timing"]["session_response_ms"]) - np.array(b["timing"]["session_response_ms"])
        for a, b in pairs
    ]), axis=0)
    rng = np.random.default_rng(20260907)
    draws = np.concatenate([
        savings[rng.integers(len(savings), size=(1000, len(savings)))].mean(axis=1)
        for _ in range(20)
    ])
    timing = {}
    for side, label in enumerate(("baseline", "candidate")):
        measurements = [pair[side]["measurement"] for pair in pairs]
        timing[label] = {
            key: statistics.median(m[key] for m in measurements)
            for key in ("startup_seconds", "evaluation_seconds", "respond_mean_ms", "respond_p95_ms", "peak_rss_mib")
        }
        timing[label]["end_to_end_seconds"] = statistics.median(
            m["startup_seconds"] + m["evaluation_seconds"] for m in measurements)
    a, b = timing["baseline"], timing["candidate"]
    result = {
        "sample_count": len(savings),
        "identical_sessions_and_responses": all(
            a["sessions"] == b["sessions"] and a["measurement"]["response_sha256"] == b["measurement"]["response_sha256"]
            for a, b in pairs),
        "requires_identical_behavior": require_identical,
        "timing_medians": timing, "paired_runs": [
            {label: pair[side]["measurement"] for side, label in enumerate(("baseline", "candidate"))}
            for pair in pairs
        ],
        "median_end_to_end_speedup": a["end_to_end_seconds"] / b["end_to_end_seconds"],
        "mean_paired_session_saving_ms": float(savings.mean()),
        "one_sided_saving_lower_bound_ms": float(np.quantile(draws, alpha)),
        "alpha": alpha, "bootstrap_draws": 20000,
        "aggregate_runtime_nonregression": b["end_to_end_seconds"] <= a["end_to_end_seconds"]
                                           and b["respond_p95_ms"] <= a["respond_p95_ms"],
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-root", required=True, type=Path)
    parser.add_argument("--candidate-root", required=True, type=Path)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--confirmation", action="store_true")
    parser.add_argument("--runtime-family-size", type=int, default=1)
    args = parser.parse_args()
    suites = {"confirmation": (args.data_root / "confirmation.jsonl", "official")} if args.confirmation else {
        "development": (args.data_root / "development.jsonl", "official"),
        "public": (args.candidate_root / "data/public_set.jsonl", "official"),
        "stress": (args.data_root / "language-stress.jsonl", "paraphrase"),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    report = {}
    for name, (dataset, wording) in suites.items():
        pairs = []
        for repeat in range(3):
            results = {}
            for label in (("baseline", "candidate") if repeat % 2 == 0 else ("candidate", "baseline")):
                root = args.baseline_root if label == "baseline" else args.candidate_root
                output = args.output / f"{name}-{repeat + 1}-{label}.json"
                if output.exists():
                    raise ValueError(f"refusing to overwrite a timing repetition: {output}")
                print(f"START {name} pair {repeat + 1} {label}", flush=True)
                completed = subprocess.run([
                    sys.executable, "-m", "scripts.benchmark_finalists", "--dataset", str(dataset.resolve()),
                    "--wording", wording, "--output", str(output.resolve()),
                ], cwd=root, text=True, capture_output=True)
                if completed.returncode:
                    raise RuntimeError(completed.stderr[-4000:] or completed.stdout[-4000:])
                result = json.loads(output.read_text())
                results[label] = result
                m = result["measurement"]
                print(json.dumps({"suite": name, "pair": repeat + 1, "arm": label,
                                  "evaluation_seconds": m["evaluation_seconds"],
                                  "p95_ms": m["respond_p95_ms"], "response_sha256": m["response_sha256"]}), flush=True)
            pairs.append((results["baseline"], results["candidate"]))
        report[name] = summarize(pairs, alpha=.05 if args.confirmation else .05 / (3 * args.runtime_family_size))
        (args.output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({"suite": name, **{key: value for key, value in report[name].items()
                                         if key not in {"paired_runs", "timing_medians"}}}), flush=True)


if __name__ == "__main__":
    main()
