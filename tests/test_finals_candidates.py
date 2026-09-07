import unittest

from conversational_search.protocol import DisclosureCard
from conversational_search.protocol_index import ProtocolResolution, ProtocolResolutionStatus, ResolvedCardGroup
from scripts.finals_candidates import answer_value_action, branches_for, hypotheses_for, two_step_action


def resolution(cards):
    return ProtocolResolution(ProtocolResolutionStatus.EXACT,
                              tuple(ResolvedCardGroup(card, (str(i),), ()) for i, card in enumerate(cards)),
                              tuple(str(i) for i in range(len(cards))), len(cards), 0)


class PlanningTests(unittest.TestCase):
    def test_question_can_skip_shared_opening_values(self):
        # A material question bypasses two generic features to reach a unique
        # third clue. All values are catalog-derived; no target is selected.
        cards = [DisclosureCard("item", ("feature one", "feature two"), (material,))
                 for material in ("cotton", "wool", "nylon", "silk")]
        r = resolution(cards)
        self.assertEqual(answer_value_action(r.candidate_ids, r, current_turn=1, top_k=10), (1, "material"))

    def test_same_rendered_reply_is_one_observation(self):
        a = DisclosureCard("A", ("x; y",), ())
        b = DisclosureCard("B", ("x", "y"), ())
        branches = branches_for((("a", a, ()), ("b", b, ())), "other")
        self.assertEqual(len(branches), 1)
        self.assertEqual({row[0] for row in branches[0]}, {"a", "b"})

    def test_full_support_retains_missing_retrieval_candidates(self):
        r = resolution([DisclosureCard("item", (str(i),), ()) for i in range(4)])
        self.assertEqual(tuple(h[0] for h in hypotheses_for(("2",), r)), ("2", "0", "1", "3"))

    def test_final_future_turn_has_no_extra_disclosure(self):
        r = resolution([DisclosureCard("item", ("shared",), ()) for _ in range(15)])
        width, question = two_step_action(r.candidate_ids, r, current_turn=9, top_k=10)
        self.assertGreater(width, 1)  # One probe + ten final slots cannot cover 15.
        self.assertLessEqual(width, 10)
        self.assertIn(question, {"other", "feature", "material", "color", "size", "style", "use_case", "budget"})


if __name__ == "__main__":
    unittest.main()
