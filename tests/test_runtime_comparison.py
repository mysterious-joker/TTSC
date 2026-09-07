from copy import deepcopy
import unittest

from scripts.benchmark_runtime_pairs import summarize


def result(duration):
    return {"sessions": [{"sample_id": str(i), "scenario_type": "buying"} for i in range(12)],
            "measurement": {"response_sha256": "same", "dataset_sha256": "data",
                            "catalog_sha256": "catalog", "evaluator_sha256": "evaluator",
                            "wording": "official", "exceptions": 0, "invalid_outputs": 0,
                            "runtime_source_sha256": "code", "startup_seconds": 1,
                            "evaluation_seconds": duration, "respond_mean_ms": duration,
                            "respond_p95_ms": duration, "peak_rss_mib": 1},
            "timing": {"session_response_ms": [duration] * 12}}


class RuntimeComparisonTests(unittest.TestCase):
    def test_accuracy_change_requires_explicit_timing_mode(self):
        pairs = [(result(10), result(8)) for _ in range(3)]
        for a, b in pairs:
            b["measurement"]["response_sha256"] = "changed"
            b["sessions"][0]["first_hit_turn"] = 1
        with self.assertRaises(ValueError):
            summarize(pairs, alpha=.05)
        summary = summarize(pairs, alpha=.05, require_identical=False)
        self.assertFalse(summary["identical_sessions_and_responses"])
        self.assertTrue(summary["aggregate_runtime_nonregression"])

    def test_nonidentical_mode_still_rejects_mismatched_pairs(self):
        pairs = [(result(10), result(8)) for _ in range(3)]
        pairs[1][1]["sessions"].reverse()
        with self.assertRaises(ValueError):
            summarize(pairs, alpha=.05, require_identical=False)

    def test_identical_faster_responses_pass(self):
        comparison = summarize([(result(10), result(8)) for _ in range(3)], alpha=.05)
        self.assertTrue(comparison["aggregate_runtime_nonregression"])
        self.assertEqual(comparison["one_sided_saving_lower_bound_ms"], 2)

    def test_mean_speed_cannot_hide_tail_regression(self):
        a, b = result(10), result(8)
        b["measurement"]["respond_p95_ms"] = 11
        self.assertFalse(summarize([(a, b)] * 3, alpha=.05)["aggregate_runtime_nonregression"])

    def test_changed_response_or_source_and_missing_timing_fail_closed(self):
        for change in ("response", "source", "timing"):
            pairs = [(result(10), result(8)) for _ in range(3)]
            modified = deepcopy(pairs[1][1])
            if change == "response":
                modified["measurement"]["response_sha256"] = "changed"
            elif change == "source":
                modified["measurement"]["runtime_source_sha256"] = "changed"
            else:
                modified["timing"]["session_response_ms"].pop()
            pairs[1] = pairs[1][0], modified
            with self.assertRaises(ValueError):
                summarize(pairs, alpha=.05)
