import unittest

from conversational_search.intent import IntentState, apply_user_message, record_question
from conversational_search.decision import ProtocolObservation, recognize_protocol_observation


class IntentEnvelopeTests(unittest.TestCase):
    def test_requirement_punctuation_preserves_values_and_provenance(self):
        for value in ("cotton", "budget around $25.50", "color: blue; size wide"):
            expected = apply_user_message(IntentState(), f"I'm looking for shirts. A key requirement is: {value}.", 1)
            for text in (f"Help me find shirts. It must have: {value}.",
                         f"Please help me find shirts. It must be: {value}.",
                         f"I need shirts; it must have — {value}."):
                self.assertEqual(apply_user_message(IntentState(), text, 1), expected)
                self.assertIs(recognize_protocol_observation(text, 1), ProtocolObservation.UNSUPPORTED)

    def test_browsing_second_sentence_does_not_become_a_requirement(self):
        expected = apply_user_message(IntentState(), "I'm looking for shirts, but I'm still exploring.", 1)
        for text in ("I'm shopping for shirts. I haven't decided on the details yet.",
                     "I'm browsing for shirts. I am still deciding.",
                     "I'm looking for shirts. I'm still exploring."):
            self.assertEqual(apply_user_message(IntentState(), text, 1), expected)

    def test_tentative_preference_can_be_replaced_without_losing_confirmed_answer(self):
        state = apply_user_message(IntentState(), "Please help me find shirts. For now I prefer: wool.", 1)
        canonical = apply_user_message(IntentState(), "I'm looking for shirts. wool", 1)
        self.assertEqual(state, canonical)
        state = record_question(state, "color")
        state = apply_user_message(state, "For that, what matters is: color: blue.", 2)
        expected = apply_user_message(state, "Actually, ignore my earlier preference. What I need is: cotton.", 3)
        for separator in (":", ".", "—", "-"):
            result = apply_user_message(state, f"Change of plan{separator} Replace my earlier preference with: cotton.", 3)
            self.assertEqual(result, expected)
            self.assertNotIn("wool", [r.value for r in result.requirements])
            self.assertIn("color: blue", [r.value for r in result.requirements])

    def test_answer_and_decline_need_context_and_preserve_payload(self):
        state = record_question(IntentState(), "color")
        self.assertEqual(apply_user_message(state, "My priorities are — color: blue; size wide.", 1),
                         apply_user_message(state, "For that, what matters is: color: blue; size wide.", 1))
        self.assertEqual(apply_user_message(state, "Any color is fine with me.", 1),
                         apply_user_message(state, "I don't have an additional preference for color.", 1))

    def test_quoted_or_questioned_replacement_does_not_withdraw_preference(self):
        state = apply_user_message(IntentState(), "I'm looking for shirts. wool", 1)
        for text in ('My friend said "Change of plan. Replace my earlier preference with: cotton."',
                     "Change of plan? Replace my earlier preference with: cotton.",
                     "Change of plan. Replace my earlier preference with:"):
            result = apply_user_message(state, text, 2)
            self.assertIn("wool", [r.value for r in result.requirements])
