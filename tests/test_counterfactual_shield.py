from collections import OrderedDict
from copy import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from scripts.counterfactual_shield import clone_session_memory, copy_containers, pointwise_gain


class ShieldTests(unittest.TestCase):
    def test_clone_isolates_mutation_but_preserves_backend_identity(self):
        token = object()
        asset = SimpleNamespace(connection=object(), available=True)
        planner = SimpleNamespace(_entries=OrderedDict([(b"session", token)]), _actions={"search": 1})
        agent = SimpleNamespace(_retriever=asset, _orchestrator=planner,
                                _sessions={"s": {"shown": ["one"]}})
        shadow = clone_session_memory(agent)
        shadow._sessions["s"]["shown"].append("two")
        shadow._orchestrator._actions["search"] += 1
        self.assertEqual(agent._sessions["s"]["shown"], ["one"])
        self.assertEqual(agent._orchestrator._actions["search"], 1)
        self.assertIs(shadow._retriever.connection, asset.connection)
        shadow._retriever.available = False
        self.assertTrue(asset.available)
        self.assertIs(shadow._orchestrator._entries[b"session"], token)

    def test_any_harmed_world_rejects_even_if_mean_improves(self):
        self.assertFalse(pointwise_gain({"a": .9, "b": .8}, {"a": .88, "b": 1.0}))

    def test_missing_world_and_noop_reject(self):
        self.assertFalse(pointwise_gain({"a": .9, "b": .8}, {"a": 1.0}))
        self.assertFalse(pointwise_gain({"a": .9}, {"a": .9}))
        self.assertTrue(pointwise_gain({"a": .9, "b": .8}, {"a": .9, "b": .82}))

    def test_real_baseline_shadow_isolated_and_response_identical(self):
        from conversational_search.exposure_policy import PROTOCOL_PARETO_HORIZON_EXPOSURE_POLICY
        from conversational_search.protocol_index import FULL_TRANSCRIPT_PROTOCOL_CATALOG_POLICY, ELIGIBLE_CONTINUATION_REFUTATION_POLICY
        from conversational_search.ranking import LEXICOGRAPHIC_EXACT_EVIDENCE_RANKING_POLICY
        from conversational_search.retrieval import HybridRetriever
        from conversational_search.service import ConversationalSearchAgent
        from conversational_search.slates import INTENT_EPOCH_NOVELTY_SLATE_POLICY
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "catalog.jsonl"
            products = [{"parent_asin": key, "title": "Shoe " + key, "categories": ["Shoes"],
                         "features": ["waterproof", "wide", "warm"], "rating_number": count}
                        for key, count in (("A", 100), ("B", 10), ("C", 1))]
            path.write_text("".join(json.dumps(row) + "\n" for row in products))
            retriever = HybridRetriever(path, None, None, protocol_evidence=True)
            self.addCleanup(retriever._connection.close)
            agent = ConversationalSearchAgent(
                path, retriever=retriever,
                ranking_policy=LEXICOGRAPHIC_EXACT_EVIDENCE_RANKING_POLICY,
                evidence_exposure_policy=PROTOCOL_PARETO_HORIZON_EXPOSURE_POLICY,
                protocol_catalog_policy=FULL_TRANSCRIPT_PROTOCOL_CATALOG_POLICY,
                protocol_refutation_policy=ELIGIBLE_CONTINUATION_REFUTATION_POLICY,
                slate_policy=INTENT_EPOCH_NOVELTY_SLATE_POLICY)
            agent.reset("live", {})
            agent.reset("unrelated", {})
            messages = ["I'm looking for Shoes. warm",
                        "For that, what matters is: waterproof; wide.",
                        "Actually, ignore my earlier preference. What I need is: waterproof.",
                        "For that, what matters is: warm."]
            for turn, message in enumerate(messages, 1):
                before = {key: copy_containers(value) for key, value in agent.__dict__.items()
                          if isinstance(value, (dict, list, set))}
                entries = copy(agent._orchestrator._entries)
                shadow = clone_session_memory(agent)
                expected = shadow.respond("live", message, turn, 10)
                for key, value in before.items():
                    self.assertEqual(getattr(agent, key), value, key)
                self.assertEqual(agent._orchestrator._entries, entries)
                self.assertEqual(agent.respond("live", message, turn, 10), expected)
