import random
import unittest

from conversational_search.protocol import DisclosureCard
from scripts.early_probe_candidates import recoverable_probe
from scripts.generate_distribution_suites import sample_targets
from tests.test_finals_candidates import resolution


class RecoverableProbeTests(unittest.TestCase):
    def test_only_moves_a_more_popular_uniquely_recoverable_probe(self):
        r = resolution([DisclosureCard(str(i), (value,), ())
                        for i, value in enumerate(("cotton", "wool", "silk"))])
        self.assertEqual(recoverable_probe(("2", "1", "0"), r, "other"), "0")
        self.assertIsNone(recoverable_probe(("0", "1", "2"), r, "other"))

    def test_rendered_collision_is_not_unique(self):
        r = resolution([DisclosureCard("a", ("x; y",), ()),
                        DisclosureCard("b", ("x", "y"), ()),
                        DisclosureCard("c", ("z",), ())])
        self.assertIsNone(recoverable_probe(("2", "0", "1"), r, "other"))

    def test_ambiguous_baseline_and_incomplete_support_are_rejected(self):
        r = resolution([DisclosureCard("a", ("same",), ()),
                        DisclosureCard("b", ("same",), ()),
                        DisclosureCard("c", ("unique",), ())])
        self.assertIsNone(recoverable_probe(("1", "2", "0"), r, "other"))
        self.assertIsNone(recoverable_probe(("2", "0"), r, "other"))

    def test_non_disclosing_answer_cannot_certify_recovery(self):
        r = resolution([DisclosureCard("a", ("cotton",), ()),
                        DisclosureCard("b", ("wool",), ())])
        self.assertIsNone(recoverable_probe(("1", "0"), r, "budget"))

    def test_ambiguous_probe_uses_a_costly_branch_and_preserves_prior_ties(self):
        r = resolution([DisclosureCard(str(i), (value,), ())
                        for i, value in enumerate(("same", "same", "different", "different", "different", "unique"))])
        self.assertEqual(recoverable_probe(("5", "4", "3", "2", "1", "0"), r, "other", ambiguous=True), "2")
        self.assertIsNone(recoverable_probe(("1", "5", "4", "3", "2", "0"), r, "other", ambiguous=True))

    def test_dominant_prior_requires_declared_margin_not_catalog_order(self):
        r = resolution([DisclosureCard("a", ("same",), ()),
                        DisclosureCard("b", ("same",), ()),
                        DisclosureCard("c", ("unique",), ())])
        ids = ("2", "1", "0")
        self.assertIsNone(recoverable_probe(ids, r, "other", popularity={"0": 18, "1": 10, "2": 1}))
        self.assertEqual(recoverable_probe(ids, r, "other", popularity={"0": 19, "1": 10, "2": 1}), "0")


class DistributionTests(unittest.TestCase):
    def test_sampling_is_reproducible_without_duplicates(self):
        products = {str(i): {"rating_number": i * i, "categories": [str(i % 3)]} for i in range(50)}
        for distribution in ("uniform", "weighted", "category"):
            a = sample_targets(products, 30, distribution, random.Random(91))
            b = sample_targets(products, 30, distribution, random.Random(91))
            self.assertEqual(a, b)
            self.assertEqual(len(set(a)), 30)
            self.assertTrue(set(a) <= products.keys())
