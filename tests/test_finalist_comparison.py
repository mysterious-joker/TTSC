"""Regression tests for decisions that could incorrectly promote an experiment."""
from copy import deepcopy
import unittest

from scripts.compare_finalist_results import compare, utility


def result(turns):
    return {"sessions": [
        {"sample_id": str(i), "scenario_type": "buying", "hit": turn is not None,
         "first_hit_turn": turn, "reciprocal_rank": 1.0 if turn is not None else 0.0}
        for i, turn in enumerate(turns)
    ]}


class PromotionGateTest(unittest.TestCase):
    def test_aggregate_gate_accepts_supported_gain_with_individual_tradeoff(self):
        decision = compare(result([5] * 31), result([1] * 30 + [6]), gate="aggregate")
        self.assertTrue(decision["development_gate_pass"])
        self.assertEqual(decision["regressed_sessions"], 1)
        self.assertGreater(decision["one_sided_bootstrap_lower_bound"], 0)

    def test_aggregate_gate_does_not_trade_mrr_for_speed(self):
        candidate = result([1] * 31)
        candidate["sessions"][0]["reciprocal_rank"] = .5
        decision = compare(result([5] * 31), candidate, gate="aggregate")
        self.assertGreater(decision["mean_utility_delta"], 0)
        self.assertFalse(decision["development_gate_pass"])
        self.assertIn("aggregate_mrr_regression", decision["rejection_reasons"])

    def test_aggregate_gate_reports_equal_hit_swaps_without_veto(self):
        decision = compare(result([None] + [5] * 301), result([1] * 301 + [None]), gate="aggregate")
        self.assertTrue(decision["development_gate_pass"])
        self.assertEqual(decision["lost_hits"], 1)
        self.assertEqual(decision["gained_hits"], 1)

    def test_aggregate_gain_cannot_hide_one_regression(self):
        decision = compare(result([5, 5, 5]), result([1, 1, 6]))
        self.assertGreater(decision["mean_utility_delta"], 0)
        self.assertFalse(decision["development_gate_pass"])
        self.assertEqual(decision["regressed_sessions"], 1)

    def test_missing_pairs_and_duplicate_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            compare(result([3, 4]), result([3]))
        duplicate = result([3, 4])
        duplicate["sessions"][1]["sample_id"] = "0"
        with self.assertRaises(ValueError):
            compare(result([3, 4]), duplicate)

    def test_noop_is_not_an_improvement_and_miss_has_zero_utility(self):
        data = result([None, 3])
        self.assertEqual(utility(data["sessions"][0]), 0)
        decision = compare(data, deepcopy(data))
        self.assertEqual(decision["mean_utility_delta"], 0)
        self.assertFalse(decision["development_gate_pass"])

    def test_different_catalogs_cannot_be_compared_as_paired_results(self):
        a, b = result([3]), result([2])
        a["measurement"] = {"catalog_sha256": "a"}
        b["measurement"] = {"catalog_sha256": "b"}
        with self.assertRaises(ValueError):
            compare(a, b)

    def test_internal_planner_errors_block_a_clean_score_gain(self):
        candidate = result([1, 1, 1])
        candidate["measurement"] = {"research_diagnostics": {"errors": 1}}
        decision = compare(result([2, 2, 2]), candidate, family_size=5)
        self.assertFalse(decision["development_gate_pass"])
        self.assertIn("internal_research_failure", decision["rejection_reasons"])
        self.assertEqual(decision["alpha"], .01)

    def test_invalid_multiplicity_is_rejected(self):
        for count in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                compare(result([2]), result([1]), family_size=count)


if __name__ == "__main__":
    unittest.main()
