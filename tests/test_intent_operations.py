import unittest

from conversational_search.decision import ProtocolObservation, recognize_protocol_observation
from conversational_search.intent import (
    IntentState, Requirement, apply_user_message, record_question, render_dense_query,
)


class ProseIntentOperationsTests(unittest.TestCase):
    def initial(self):
        state = apply_user_message(IntentState(),
            "I'm looking for Shoes. A key requirement is: Color: black.", 1)
        state = record_question(state, 'material')
        return apply_user_message(state, 'For that, what matters is: cotton.', 2)

    def test_replacement_with_withdrawal_preserves_unrelated_confirmed_answer(self):
        state = self.initial()
        result = apply_user_message(state,
            'Make that white instead; black is no longer what I want.', 3)
        self.assertEqual([r.value for r in result.requirements], ['cotton', 'white'])
        self.assertEqual(result.requirements[-1].source, 'override')
        self.assertEqual(result.intent_version, state.intent_version + 1)
        self.assertNotIn('black', render_dense_query(result))
        self.assertIs(recognize_protocol_observation(
            'Make that white instead; black is no longer what I want.', 3),
            ProtocolObservation.UNSUPPORTED)

    def test_explicit_value_replacements(self):
        for text in ('Replace black with white.', 'Swap black for white.',
                     'I want white instead of black.', 'White rather than black.',
                     'I want white, not black.', 'Instead of black, choose white.',
                     'Change the color to white.', 'Switch that to white.'):
            with self.subTest(text=text):
                result = apply_user_message(self.initial(), text, 3)
                self.assertEqual([r.value.casefold() for r in result.requirements], ['cotton', 'white'])

    def test_correction_takes_precedence_over_bare_answer(self):
        state = record_question(self.initial(), 'color')
        for text in ('I prefer white instead of black.', 'Make it white instead.'):
            result = apply_user_message(state, text, 3)
            self.assertEqual([r.value for r in result.requirements], ['cotton', 'white'])

    def test_new_opening_and_typed_requirement(self):
        result = apply_user_message(IntentState(),
            'Could you help me pick shoes? I need them in black.', 1)
        self.assertEqual(result.category, 'shoes')
        self.assertEqual([(r.value, r.attribute) for r in result.requirements], [('black', 'color')])

    def test_clear_withdraw_and_exclude_are_distinct(self):
        state = self.initial()
        withdrawn = apply_user_message(state, 'Drop black.', 3)
        self.assertEqual([r.value for r in withdrawn.requirements], ['cotton'])
        self.assertEqual(withdrawn.excluded, ())
        excluded = apply_user_message(state, 'Avoid black.', 3)
        self.assertEqual(excluded.excluded, ('black',))
        cleared = apply_user_message(excluded, 'Any color will do.', 4)
        self.assertIn('color', cleared.no_preference)
        self.assertEqual(cleared.excluded, ())
        self.assertEqual([r.value for r in cleared.requirements], ['cotton'])

    def test_withdrawal_does_not_mean_exclusion_and_keep_preserves_provenance(self):
        state = self.initial()
        withdrawn = apply_user_message(state, "I don't need black anymore.", 3)
        self.assertEqual(withdrawn.requirements, state.requirements[1:])
        self.assertEqual(withdrawn.excluded, ())
        kept = apply_user_message(state, 'Keep cotton; change the color to white.', 3)
        self.assertEqual(kept.requirements[0], state.requirements[1])

    def test_untyped_replacement_remains_revocable(self):
        state = self.initial()
        revised = apply_user_message(state,
            'Drop my earlier preference; I need something packable.', 3)
        self.assertEqual(revised.requirements[-1].source, 'override')
        self.assertEqual(revised.requirements[-1].strength, 'soft')
        revised_again = apply_user_message(revised,
            'Drop my earlier preference; I need Color: white.', 4)
        self.assertEqual([r.value for r in revised_again.requirements], ['cotton', 'Color: white'])

    def test_initial_preference_withdrawal_preserves_later_answer(self):
        result = apply_user_message(self.initial(),
            'Remove my earlier preference; I need Color: white.', 3)
        self.assertEqual([r.value for r in result.requirements], ['cotton', 'Color: white'])

    def test_multiple_independent_additions(self):
        result = apply_user_message(IntentState(),
            'Please find me shoes. I need them in black; Material: cotton.', 1)
        self.assertEqual(result.category, 'shoes')
        self.assertEqual([(r.value, r.attribute) for r in result.requirements],
                         [('black', 'color'), ('Material: cotton', 'material')])

    def test_unsafe_or_incomplete_interpretations_do_not_mutate_old_requirements(self):
        state = self.initial()
        for text in ('Maybe replace black with white.', 'Do not replace black with white.',
                     'If I replace black with white, will it look good?',
                     'My friend said "replace black with white".',
                     'Replace black with white?', 'Replace black with white; whatever.',
                     'Replace black with leather.', 'Replace blue with white.',
                     'Replace black with white; blue is no longer what I want.',
                     'I want white rather than black or navy.'):
            with self.subTest(text=text):
                result = apply_user_message(state, text, 3)
                self.assertEqual(result.requirements[:2], state.requirements)
                self.assertEqual(result.intent_version, state.intent_version)

    def test_unknown_semantic_feature_stays_soft(self):
        result = apply_user_message(IntentState(), 'I need something that keeps rain out.', 1)
        self.assertIsNone(result.category)
        self.assertEqual(result.requirements[0].strength, 'soft')

    def test_negated_or_alternative_labeled_values_are_not_positive_constraints(self):
        state = self.initial()
        for text in ('Color: not white.', 'Color: white or navy.',
                     'Replace black with white unless it is expensive.'):
            result = apply_user_message(state, text, 3)
            self.assertEqual(result.requirements[:2], state.requirements)
            self.assertEqual(result.requirements[-1].source, 'free_text')

    def test_compound_prior_cannot_lose_unrelated_requirement(self):
        state = IntentState(category='shoes', last_turn=1, requirements=(
            Requirement('Color: black; size wide', 'initial_explicit', 1, 'color'),))
        result = apply_user_message(state, 'Change the color to white.', 2)
        self.assertEqual(result.requirements[0], state.requirements[0])

    def test_bounded_input_falls_back(self):
        state = self.initial()
        result = apply_user_message(state, 'Replace black with ' + 'white ' * 500, 3)
        self.assertEqual(result.requirements[:2], state.requirements)

    def test_post_freeze_combinations_retain_independent_preferences(self):
        # Authored and first evaluated after the runtime freeze; now regression cases.
        for old, new, material in [('red', 'navy', 'linen'), ('green', 'ivory', 'silk'),
                                   ('brown', 'blue', 'leather')]:
            state = apply_user_message(IntentState(),
                f"I'm looking for Shoes. A key requirement is: Color: {old}.", 1)
            state = record_question(state, 'material')
            state = apply_user_message(state, f'For that, what matters is: {material}.', 2)
            for text in (f'Please swap {old} for {new}; keep {material}.',
                         f'Rather than {old}, I would like {new}.',
                         f'Actually, change the color to {new}.'):
                result = apply_user_message(state, text, 3)
                self.assertEqual([r.value.casefold() for r in result.requirements], [material, new])
            for text in (f'Perhaps swap {old} for {new}.',
                         f'Change the color to {new} if available.',
                         f'Would replacing {old} with {new} help?', f'Colour: not {new}.'):
                result = apply_user_message(state, text, 3)
                self.assertEqual(result.requirements[:2], state.requirements)
                self.assertEqual(result.intent_version, state.intent_version)
