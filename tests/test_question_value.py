import unittest
from unittest.mock import patch

from conversational_search.exact_evidence import rank_exact_evidence
from conversational_search.exposure import plan_evidence_gated_exposure
from conversational_search.exposure_policy import EvidenceExposureStatus
from conversational_search.intent import IntentState
from conversational_search.protocol import DisclosureCard, ProductProtocolEvidence
from conversational_search.protocol_index import ProtocolResolution, ProtocolResolutionStatus, ResolvedCardGroup
from conversational_search.question_value import _visible_branches, plan_metric_constrained_question


class QuestionValueTests(unittest.TestCase):
    def setUp(self):
        self.cards = tuple(DisclosureCard("item", ("generic detail", "common detail"), (f"color: {c}",))
                           for c in ("red", "blue", "green", "black"))
        self.ids = tuple(str(i) for i in range(4))
        self.resolution = ProtocolResolution(ProtocolResolutionStatus.EXACT,
            tuple(ResolvedCardGroup(card, (asin,), ()) for asin, card in zip(self.ids, self.cards)),
            self.ids, 4, 0)

    def test_question_can_skip_shared_clues_without_changing_probe(self):
        with patch("conversational_search.question_value.plan_protocol_pareto_action", return_value=(1, "other")):
            self.assertEqual(plan_metric_constrained_question(self.ids, self.resolution, current_turn=1, top_k=10),
                             (1, "color"))

    def test_indistinguishable_cards_retain_baseline_action(self):
        shared = ProtocolResolution(ProtocolResolutionStatus.EXACT,
            (ResolvedCardGroup(self.cards[0], self.ids, ()),), self.ids, 4, 0)
        with patch("conversational_search.question_value.plan_protocol_pareto_action", return_value=(1, "other")):
            self.assertEqual(plan_metric_constrained_question(self.ids, shared, current_turn=1, top_k=10),
                             (1, "other"))

    def test_equal_visible_payloads_do_not_create_hidden_information(self):
        a = DisclosureCard("a", ("x; y",), ())
        b = DisclosureCard("b", ("x", "y"), ())
        branches = _visible_branches((("a", a, ()), ("b", b, ())), "other")
        self.assertEqual(len(branches), 1)
        self.assertEqual(tuple(row[0] for row in branches[0]), ("a", "b"))

    def test_unsupported_and_locked_states_do_not_use_new_planner(self):
        state = IntentState(category="Items", last_turn=1)
        evidence = tuple(ProductProtocolEvidence(asin, "Items", card, "item")
                         for asin, card in zip(self.ids, self.cards))
        exact = rank_exact_evidence(self.ids, evidence, state)
        kwargs = dict(current_turn=1, requested_top_k=10, metric_aware_protocol_enumeration=True,
                      metric_constrained_protocol_planning=True)
        with patch("conversational_search.question_value.plan_metric_constrained_question") as planner:
            plan_evidence_gated_exposure(state, exact, evidence, **kwargs)
            locked = plan_evidence_gated_exposure(state, exact, evidence, **kwargs,
                protocol_resolution=self.resolution, protocol_planning_locked=True)
            planner.assert_not_called()
        self.assertIs(locked.status, EvidenceExposureStatus.POSTERIOR_PROBE)
        self.assertEqual(locked.question, "other")
