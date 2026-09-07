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


if __name__ == "__main__":
    unittest.main()
