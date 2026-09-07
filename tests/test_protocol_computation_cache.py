"""Behavior and invalidation boundaries for catalog-only runtime caches."""
import json
from pathlib import Path
import tempfile
import sqlite3
import unittest

from conversational_search.exposure import _protocol_enumeration_plan
from conversational_search.orchestration import BackendSnapshotToken
from conversational_search.protocol import (
    MAX_CONSTRAINT_CHARACTERS, _classify_bounded_constraint, classify_constraint,
)
from conversational_search.retrieval import HybridRetriever
from conversational_search.ranking import (
    _cached_significant_tokens, _significant_tokens, _uncached_significant_tokens,
)
from evaluator.local_evaluator import classify_constraint as official_classifier


class ComputationCacheTests(unittest.TestCase):
    def test_token_cache_preserves_unicode_duplicates_and_long_inputs(self):
        for value in ("Café café—BLUE", "the cotton cotton shoe", "İß 全", "", "warm " * 1000):
            self.assertEqual(_significant_tokens(value), _uncached_significant_tokens(value))
        _cached_significant_tokens.cache_clear()
        _significant_tokens("warm " * 1000)
        self.assertEqual(_cached_significant_tokens.cache_info().currsize, 0)
        for i in range(520):
            _significant_tokens(f"cotton {i}")
        self.assertEqual(_cached_significant_tokens.cache_info().currsize, 512)

    def test_classifier_retains_official_precedence_and_long_input_behavior(self):
        values = ["budget under $50 cotton", "nylon blue", "RED wide", "size winter",
                  "fit running", "outdoor", "miscellaneous", "", "İ" * 180,
                  "x" * (MAX_CONSTRAINT_CHARACTERS + 1) + " cotton"]
        for value in values:
            self.assertEqual(classify_constraint(value), official_classifier(value))
        _classify_bounded_constraint.cache_clear()
        classify_constraint(values[-1])
        self.assertEqual(_classify_bounded_constraint.cache_info().currsize, 0)
        classify_constraint("COTTON")
        classify_constraint("cotton")
        self.assertEqual(_classify_bounded_constraint.cache_info().hits, 1)

    def test_enumeration_cache_preserves_dynamic_program_exactly(self):
        for count in (1, 3, 10, 31, 101):
            for turn in (1, 5, 10):
                for top_k in (1, 5, 10):
                    args = dict(current_turn=turn, top_k=top_k)
                    expected = _protocol_enumeration_plan.__wrapped__(count, **args)
                    self.assertEqual(_protocol_enumeration_plan(count, **args), expected)
                    self.assertEqual(_protocol_enumeration_plan(count, **args), expected)

    def backend(self, folder, product_id):
        path = Path(folder) / (product_id + ".jsonl")
        path.write_text(json.dumps({"parent_asin": product_id, "title": "Shoe " + product_id,
                                   "categories": ["Shoes"], "features": ["cotton", "wide"]}) + "\n")
        backend = HybridRetriever(path, None, None, protocol_evidence=True)
        self.addCleanup(backend._connection.close)
        return backend

    def test_categories_isolate_backends_and_recheck_availability(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b = self.backend(folder, "A"), self.backend(folder, "B")
            first = a.protocol_category_evidence("Shoes")
            self.assertIs(a.protocol_category_evidence("Shoes"), first)
            self.assertEqual(first[0].parent_asin, "A")
            self.assertEqual(b.protocol_category_evidence("Shoes")[0].parent_asin, "B")
            a.protocol_evidence_available = False
            self.assertEqual(a.protocol_category_evidence("Shoes"), ())
            with self.assertRaises(ValueError):
                a.protocol_category_evidence(" Shoes ")
            a.protocol_evidence_available = True
            a._snapshot_token = BackendSnapshotToken()
            refreshed = a.protocol_category_evidence("Shoes")
            self.assertEqual(refreshed, first)
            self.assertIsNot(refreshed, first)

    def test_category_cache_is_bounded_and_does_not_cache_errors(self):
        with tempfile.TemporaryDirectory() as folder:
            backend = self.backend(folder, "A")
            for i in range(20):
                backend.protocol_category_evidence(f"missing {i}")
            self.assertEqual(len(backend._protocol_category_cache), 16)
            backend._connection.execute("ALTER TABLE protocol_products RENAME TO saved_products")
            with self.assertRaises(sqlite3.OperationalError):
                backend.protocol_category_evidence("Shoes")
            backend._connection.execute("ALTER TABLE saved_products RENAME TO protocol_products")
            self.assertEqual(backend.protocol_category_evidence("Shoes")[0].parent_asin, "A")

    def test_indexed_query_preserves_case_sensitive_category_membership(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "case.jsonl"
            path.write_text("".join(json.dumps({"parent_asin": key, "title": "Shoe " + key,
                                                 "categories": [category], "features": ["cotton"]}) + "\n"
                                    for key, category in (("A", "Shoes"), ("B", "shoes"))))
            backend = HybridRetriever(path, None, None, protocol_evidence=True)
            self.addCleanup(backend._connection.close)
            statements = []
            backend._connection.set_trace_callback(statements.append)
            self.assertEqual([x.parent_asin for x in backend.protocol_category_evidence("Shoes")], ["A"])
            self.assertEqual([x.parent_asin for x in backend.protocol_category_evidence("shoes")], ["B"])
            backend._connection.set_trace_callback(None)
            plan = backend._connection.execute("EXPLAIN QUERY PLAN " + statements[0]).fetchall()
            self.assertTrue(any("USING INDEX protocol_category_idx" in row[3] for row in plan))


if __name__ == "__main__":
    unittest.main()
