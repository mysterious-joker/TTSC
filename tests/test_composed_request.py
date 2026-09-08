import unittest

from conversational_search.composed_request import parse_composed_request
from conversational_search.intent import IntentState, RequirementImportance, apply_user_message


class ComposedRequestTests(unittest.TestCase):
    def test_opening_separates_category_material_color_and_budget(self):
        state = apply_user_message(IntentState(), 'I need a blue cotton T-shirt under $50.', 1)
        self.assertEqual(state.category, 'T-shirt')
        self.assertEqual({r.attribute: r.value for r in state.requirements},
                         {'color': 'blue', 'material': 'cotton', 'budget': 'under $50'})
        self.assertTrue(all(r.importance is RequirementImportance.MUST for r in state.requirements))

    def test_modifier_order_and_explicit_suffixes(self):
        for message in ('Find me a cotton blue shirt under $49.95.',
                        'Find me a shirt in blue made from cotton under $49.95.',
                        'Find me a shirt made of cotton and in blue under $49.95.'):
            with self.subTest(message=message):
                state = apply_user_message(IntentState(), message, 1)
                self.assertEqual(state.category, 'shirt')
                self.assertEqual({r.attribute: r.value for r in state.requirements},
                                 {'color': 'blue', 'material': 'cotton', 'budget': 'under $49.95'})

    def test_preference_and_composition_are_preserved(self):
        state = apply_user_message(IntentState(), 'I prefer a navy cotton blend jacket at most $80.', 1)
        self.assertEqual(state.requirements[1].value, 'cotton blend')
        self.assertIs(state.requirements[0].importance, RequirementImportance.PREFER)
        self.assertIs(state.requirements[-1].importance, RequirementImportance.MUST)
        pure = apply_user_message(IntentState(), 'I need a pure cotton shirt.', 1)
        self.assertEqual(pure.requirements[0].value, 'pure cotton')

    def test_price_ceiling_is_independent_of_preferred_attributes(self):
        for limit in ('under $50', 'up to $50', 'at most $50', 'no more than $50'):
            state = apply_user_message(IntentState(), 'I prefer a blue shirt ' + limit, 1)
            self.assertIs(state.requirements[0].importance, RequirementImportance.PREFER)
            self.assertEqual(state.requirements[0].strength, 'soft')
            self.assertIs(state.requirements[-1].importance, RequirementImportance.MUST)
            self.assertEqual(state.requirements[-1].strength, 'hard')

    def test_slot_change_preserves_other_opening_requirements(self):
        state = apply_user_message(IntentState(), 'I need a blue cotton shirt under $50.', 1)
        changed = apply_user_message(state, 'Change the color to black; keep everything else.', 2)
        self.assertEqual({r.attribute: r.value for r in changed.requirements},
                         {'color': 'black', 'material': 'cotton', 'budget': 'under $50'})
        self.assertEqual(changed.intent_version, 1)
        self.assertEqual(changed.requirements[:2], state.requirements[1:])

    def test_incomplete_or_ambiguous_requests_are_not_partially_split(self):
        for text in ('I need blue light glasses.', 'I need a blueberry shirt.',
                     'I need a cotton-free shirt.', 'I need a linen-look dress.',
                     'I need an Orange brand shirt.', 'I need a blue or red shirt.',
                     'I need a blue shirt if it is cheap.', 'I need a blue shirt with pockets.',
                     'I need a blue shirt and a cotton skirt.', 'I need a blue shirt under $50 tomorrow.',
                     'I need a blue cotton/polyester shirt.', 'I need a blue cotton shirt, maybe.',
                     'I need a blue shirt. I prefer wool.', 'I need a red blue shirt.'):
            with self.subTest(text=text):
                self.assertIsNone(parse_composed_request(IntentState(), text, 1))

    def test_official_envelopes_and_later_turns_keep_existing_path(self):
        for text in ("I'm looking for Shoes. A key requirement is: Color: blue.",
                     "I'm looking for Shoes, but I'm still exploring.", 'I need shoes.'):
            self.assertIsNone(parse_composed_request(IntentState(), text, 1))
        self.assertIsNone(parse_composed_request(IntentState(last_turn=1), 'I need blue shoes.', 2))
