from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from conversational_search.exposure_policy import (
    PROTOCOL_METRIC_AWARE_EXPOSURE_POLICY,
    PROTOCOL_POSTERIOR_EXPOSURE_POLICY,
    PROTOCOL_METRIC_CONSTRAINED_EXPOSURE_POLICY,
)
from conversational_search.protocol_index import (
    ELIGIBLE_CONTINUATION_REFUTATION_POLICY,
    FULL_TRANSCRIPT_PROTOCOL_CATALOG_POLICY,
    COLD_PRIOR_PROTOCOL_FUSION_POLICY,
)
from conversational_search.ranking import (
    LEXICOGRAPHIC_EXACT_EVIDENCE_RANKING_POLICY,
)
from conversational_search.retrieval import HybridRetriever
from conversational_search.service import ConversationalSearchAgent
from conversational_search.slates import INTENT_EPOCH_NOVELTY_SLATE_POLICY


class ServiceProtocolCatalogTest(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.catalog_path = Path(directory.name) / "catalog.jsonl"
        products = (
            {
                "parent_asin": "A",
                "title": "Popular shoe",
                "categories": ["Shoes"],
                "features": ["waterproof", "wide", "warm"],
                "details": {},
                "description": [],
                "store": "One",
                "rating_number": 100,
            },
            {
                "parent_asin": "B",
                "title": "Less popular shoe",
                "categories": ["Shoes"],
                "features": ["waterproof", "wide", "warm"],
                "details": {},
                "description": [],
                "store": "Two",
                "rating_number": 10,
            },
            {
                "parent_asin": "C",
                "title": "Different shoe",
                "categories": ["Shoes"],
                "features": ["water resistant", "narrow", "cool"],
                "details": {},
                "description": [],
                "store": "Three",
                "rating_number": 1,
            },
        )
        self.catalog_path.write_text(
            "".join(json.dumps(product) + "\n" for product in products),
            encoding="utf-8",
        )

    def _agent(self, *, cold=False) -> ConversationalSearchAgent:
        retriever = HybridRetriever(
            self.catalog_path,
            None,
            None,
            protocol_evidence=True,
        )
        self.addCleanup(retriever._connection.close)
        return ConversationalSearchAgent(
            self.catalog_path,
            retriever=retriever,
            ranking_policy=LEXICOGRAPHIC_EXACT_EVIDENCE_RANKING_POLICY,
            evidence_exposure_policy=(PROTOCOL_METRIC_CONSTRAINED_EXPOSURE_POLICY
                                      if cold else PROTOCOL_POSTERIOR_EXPOSURE_POLICY),
            **({"protocol_fusion_policy": COLD_PRIOR_PROTOCOL_FUSION_POLICY} if cold else {}),
            protocol_catalog_policy=FULL_TRANSCRIPT_PROTOCOL_CATALOG_POLICY,
            protocol_refutation_policy=(
                ELIGIBLE_CONTINUATION_REFUTATION_POLICY
            ),
            slate_policy=INTENT_EPOCH_NOVELTY_SLATE_POLICY,
        )

    def test_cold_opening_defers_search_and_later_boundary_matches_eager_path(self):
        lazy, eager = self._agent(cold=True), self._agent(cold=True)
        for agent in (lazy, eager):
            agent.reset("cold", {})
        messages = ("I'm looking for Shoes, but I'm still exploring.",
                    "I don't have a preference for other; please use your judgment.",
                    "For that, what matters is: waterproof; wide.")
        with patch.object(eager, "_respond_catalog_cold_start", return_value=None), \
                patch.object(lazy._retriever, "search_with_trace", wraps=lazy._retriever.search_with_trace) as search:
            for turn, message in enumerate(messages, 1):
                self.assertEqual(lazy.respond("cold", message, turn, 10),
                                 eager.respond("cold", message, turn, 10))
                self.assertEqual(lazy._sessions["cold"], eager._sessions["cold"])
                self.assertEqual(lazy._slates["cold"], eager._slates["cold"])
                self.assertEqual(lazy._protocol_refuted_ids["cold"], eager._protocol_refuted_ids["cold"])
                if turn == 1:
                    search.assert_not_called()
                    self.assertEqual(lazy._protocol_action_traces["cold"]["retrieval_action"], "deferred")
                if turn == 2:
                    self.assertEqual(search.call_count, 1)  # No fabricated cached hybrid ranking.

    def test_cold_opening_falls_back_if_complete_evidence_is_unavailable(self):
        agent = self._agent(cold=True)
        agent.reset("cold", {})
        with patch.object(agent._retriever, "protocol_category_evidence", side_effect=RuntimeError("offline")), \
                patch.object(agent._retriever, "search_with_trace", wraps=agent._retriever.search_with_trace) as search:
            result = agent.respond("cold", "I'm looking for Shoes, but I'm still exploring.", 1, 10)
            search.assert_called_once()
        self.assertTrue(result["recommendations"])

    def test_free_form_and_explicit_requirements_do_not_use_cold_shortcut(self):
        agent = self._agent(cold=True)
        with patch.object(agent, "_respond_catalog_cold_start", wraps=agent._respond_catalog_cold_start) as shortcut:
            for message in ("I'm looking for Shoes. A key requirement is: waterproof.",
                            "Can you find me some comfy shoes?"):
                agent.reset("session", {})
                agent.respond("session", message, 1, 10)
            shortcut.assert_not_called()

    def test_continuation_refutes_only_the_prior_score_eligible_product(self) -> None:
        agent = self._agent()
        agent.reset("session", {})

        first = agent.respond(
            "session",
            "I'm looking for Shoes. A key requirement is: waterproof.",
            1,
            10,
        )
        second = agent.respond(
            "session",
            "For that, what matters is: wide; warm.",
            2,
            10,
        )

        self.assertEqual(first["recommendations"], [{"parent_asin": "A"}])
        self.assertEqual(first["ask_attribute"], "other")
        self.assertEqual(second["recommendations"], [{"parent_asin": "B"}])
        self.assertIsNone(second["ask_attribute"])
        self.assertEqual(agent._protocol_refuted_ids["session"], ("A",))

    def test_pre_override_products_are_not_refuted(self) -> None:
        agent = self._agent()
        agent.reset("override", {})

        first = agent.respond(
            "override",
            "I'm looking for Shoes. warm",
            1,
            10,
        )
        second = agent.respond(
            "override",
            "For that, what matters is: waterproof; wide.",
            2,
            10,
        )
        third = agent.respond(
            "override",
            "Actually, ignore my earlier preference. What I need is: waterproof.",
            3,
            10,
        )
        refuted_after_override = agent._protocol_refuted_ids["override"]
        fourth = agent.respond(
            "override",
            "For that, what matters is: warm.",
            4,
            10,
        )

        self.assertEqual(first["recommendations"], [{"parent_asin": "A"}])
        self.assertEqual(second["recommendations"], [{"parent_asin": "A"}])
        self.assertEqual(refuted_after_override, ())
        self.assertEqual(agent._protocol_refuted_ids["override"], ("A",))
        self.assertEqual(third["recommendations"], [{"parent_asin": "A"}])
        self.assertEqual(fourth["recommendations"], [{"parent_asin": "B"}])

    def test_metric_aware_policy_requires_refutation(self) -> None:
        retriever = HybridRetriever(
            self.catalog_path,
            None,
            None,
            protocol_evidence=True,
        )
        self.addCleanup(retriever._connection.close)

        with self.assertRaisesRegex(ValueError, "requires continuation refutation"):
            ConversationalSearchAgent(
                self.catalog_path,
                retriever=retriever,
                evidence_exposure_policy=(
                    PROTOCOL_METRIC_AWARE_EXPOSURE_POLICY
                ),
                protocol_catalog_policy=FULL_TRANSCRIPT_PROTOCOL_CATALOG_POLICY,
            )


if __name__ == "__main__":
    unittest.main()
