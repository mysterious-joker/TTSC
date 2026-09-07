import unittest
from scripts.audit_observability import best_total


class OracleTests(unittest.TestCase):
    def test_singleton_earliest_eligible_score(self):
        self.assertAlmostEqual(best_total(1, 4, "technical_score"), 0.94)
        self.assertEqual(best_total(1, 4, "mrr"), 1.0)

    def test_more_than_horizon_capacity_cannot_all_hit(self):
        self.assertEqual(best_total(264, 1, "hit_rate_at_10"), 100.0)
        self.assertEqual(best_total(264, 4, "hit_rate_at_10"), 70.0)

    def test_rank_one_trials_and_last_turn_harmonic_sum(self):
        self.assertEqual(best_total(10, 1, "mrr"), 10.0)
        self.assertAlmostEqual(best_total(11, 1, "mrr"), 10.5)
        self.assertAlmostEqual(best_total(20, 10, "mrr"), sum(1/r for r in range(1, 11)))
