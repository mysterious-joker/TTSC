"""Conservative parsing of a single apparel request with independent modifiers.

This is a bounded grammar, not general language understanding. Every token must
belong to the request verb, a known product noun, an explicit color/material, or
a maximum budget. Unknown modifiers, alternatives, negation and brand names
leave the original reducer in charge. No catalog, simulator or target is read.
"""
from __future__ import annotations

from dataclasses import replace
import re

from .intent import IntentState, Requirement, infer_requirement_importance

_OPENING = re.compile(
    r"^(?P<verb>i need|i want|i prefer|i would like|i require|i'm looking for|"
    r"please find me|please show me|find me|show me)\s+(?P<body>.+)$", re.I,
)
# Restrict noun boundaries so e.g. blue light glasses is not interpreted as a
# color preference. This vocabulary is domain grammar, not catalog eligibility.
_NOUNS = (
    't-shirts', 't-shirt', 'tee shirts', 'tee shirt', 'polo shirts', 'polo shirt',
    'shirts', 'shirt', 'blouses', 'blouse', 'dresses', 'dress',
    'jackets', 'jacket', 'coats', 'coat', 'sweaters', 'sweater',
    'hoodies', 'hoodie', 'trousers', 'pants', 'shorts', 'skirts', 'skirt',
    'socks', 'running shoes', 'walking shoes', 'hiking boots', 'ankle boots',
    'shoes', 'sneakers', 'boots', 'sandals', 'backpacks', 'backpack',
    'handbags', 'handbag', 'bags', 'bag', 'hats', 'hat', 'scarves', 'scarf',
)
_NOUN = re.compile(r'(?<!\w)(?:' + '|'.join(re.escape(x) for x in _NOUNS) + r')(?!\w)', re.I)
_COLORS = frozenset('black white blue red pink green brown gray grey purple yellow orange navy teal tan beige ivory cream charcoal burgundy maroon olive'.split())
_MATERIALS = frozenset('cotton polyester nylon leather wool silk rayon linen suede canvas denim velvet cashmere acrylic microfiber'.split())
_TOKEN = re.compile(
    r'(?:(?:pure|100%)\s+)?(?:' + '|'.join(sorted(_MATERIALS)) + r')'
    r'(?:\s+blend)?|(?:' + '|'.join(sorted(_COLORS)) + r')', re.I,
)
_BUDGET = re.compile(
    r'\s+(?P<value>(?:under|less than|at most|up to|no more than)\s*\$?\s*'
    r'\d+(?:\.\d{1,2})?)$', re.I,
)


def parse_composed_request(state: IntentState, message: str, turn: int) -> IntentState | None:
    """Split a completely recognized opening; never apply a partial parse."""
    if turn != 1 or state.requirements or state.category or len(message) > 512:
        return None
    message = re.sub(r'\s+', ' ', message).strip().rstrip('.!').strip()
    match = _OPENING.fullmatch(message)
    if not match:
        return None
    body = re.sub(r'^(?:a pair of|a|an|some)\s+', '', match['body'], flags=re.I)
    # Sentences, qualification and hypothetical wording cannot be silently lost.
    if re.search(r'[;?!"“”]|\b(?:if|unless|or|not|without|maybe|perhaps)\b', body, re.I):
        return None
    budget = _BUDGET.search(body)
    if budget:
        body = body[:budget.start()].strip()
    nouns = list(_NOUN.finditer(body))
    if len(nouns) != 1:
        return None
    noun = nouns[0]
    prefix, suffix = body[:noun.start()].strip(), body[noun.end():].strip()
    if not prefix and not suffix and not budget:
        return None  # Preserve the existing category-only path exactly.
    values: dict[str, str] = {}
    for fragment, after_noun in ((prefix, False), (suffix, True)):
        while fragment:
            if after_noun:
                marker = re.match(r'^(?:in|made of|made from)\s+', fragment, re.I)
                if not marker:
                    return None
                fragment = fragment[marker.end():]
            token = _TOKEN.match(fragment)
            if not token or (token.end() < len(fragment) and fragment[token.end()] not in ' ,'):
                return None
            value = token[0]
            attribute = 'color' if value.casefold() in _COLORS else 'material'
            if attribute in values:
                return None  # Do not collapse alternatives or mixed compositions.
            if after_noun and marker[0].strip().casefold() == 'in' and attribute != 'color':
                return None
            if after_noun and marker[0].strip().casefold() != 'in' and attribute != 'material':
                return None
            values[attribute] = value
            fragment = fragment[token.end():].strip()
            fragment = re.sub(r'^(?:,\s*|and\s+)', '', fragment, count=1, flags=re.I)
    if budget:
        values['budget'] = budget['value']
    if not values:
        return None
    tentative = match['verb'].casefold() in {'i prefer', 'i would like'}
    source = 'initial_tentative' if tentative else 'initial_explicit'
    requirements = tuple(Requirement(
        value=value, source='initial_explicit' if attribute == 'budget' else source,
        turn=turn, attribute=attribute,
        importance=infer_requirement_importance(match['verb'] + ' ' + value, source, attribute),
    ) for attribute, value in values.items())
    return replace(state, category=noun[0], requirements=requirements, last_turn=turn)
