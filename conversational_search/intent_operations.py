"""Bounded compositional edits for prose the canonical reducer does not parse.

This module only edits intent. It never constructs simulator events. Destructive
edits require an explicit command and an unambiguous slot or existing value;
an incomplete interpretation returns None without applying any partial edits.
"""
from __future__ import annotations

import re
from dataclasses import replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .intent import IntentState

_FLAGS = re.IGNORECASE
_UNSAFE = re.compile(
    r'["“”]|\b(?:if|unless|possibly|consider|suppose|imagine|perhaps|maybe|might|could be|not sure|wonder|said|says|'
    r'suggested|whether|do not replace|don.t replace|not only)\b', _FLAGS,
)
_OPENING = re.compile(
    r'^(?:(?:could|can|would) you (?:please )?help me (?:find|pick|choose)|'
    r'(?:please )?(?:find|show|recommend|suggest)(?: me)?|'
    r'i(?: would like| want| need))\s+(?P<category>[^.!?;]+)'
    r'(?:[.!?;]\s*(?P<body>.*))?$', _FLAGS,
)
_LABEL = re.compile(
    r'^(?P<attribute>colou?r|material|fabric|size|sizing|style|brand|budget|'
    r'feature|use[ _]case|other)\s*[:=]\s*(?P<value>.+)$', _FLAGS,
)
_POSITIVE = re.compile(
    r'^(?:(?:i (?:also )?(?:want|need|prefer|would like)(?: (?:it|them))?)|'
    r'(?:(?:it|they) (?:must|should) (?:be|have))|'
    r'(?:(?:please )?(?:use|choose|pick|go with)))\s+', _FLAGS,
)
_REPLACE = re.compile(r'^(?:replace|swap) (.+?) (?:with|for) (.+)$', _FLAGS)
_INSTEAD = re.compile(r'^(.+?) (?:instead of|rather than) (.+)$', _FLAGS)
_CONTRAST = re.compile(r'^(.+?),\s*not (.+)$', _FLAGS)
_REVERSED = re.compile(r'^(?:instead of|rather than) (.+?),\s*(.+)$', _FLAGS)
_SET = re.compile(
    r'^(?:make|change|switch|set) (?:it|them|that|the (?P<slot>colou?r|'
    r'material|size|style|brand|budget|feature)) (?:to )?(?P<value>.+)$', _FLAGS,
)
_WITHDRAW = re.compile(
    r'^(?:(?:drop|remove|withdraw|forget|discard) (.+)|'
    r'(?:i )?no longer (?:want|need|require) (.+)|'
    r'(.+?) (?:is|are) no longer (?:what i (?:want|need)|required|needed)|'
    r'i (?:do not|don.t) (?:need|require) (.+?) (?:anymore|any longer))$', _FLAGS,
)
_EXCLUDE = re.compile(
    r'^(?:avoid|exclude|without|no|not|i (?:do not|don.t) want) (.+)$', _FLAGS,
)
_CLEAR = re.compile(
    r'^(?:any (.+?) (?:will do|works(?: for me)?)|'
    r'i (?:do not|don.t) care (?:about|which) (.+)|'
    r'(.+?) (?:is|are) (?:not important|optional))$', _FLAGS,
)
_CONTEXT = re.compile(r'^(?:as for|regarding|for) ([a-z_ ]+),?[:;]\s*(.+)$', _FLAGS)
_BROWSING = re.compile(
    r'^(?:i (?:am|\x27m) (?:just )?(?:browsing|exploring)|'
    r'(?:i )?have(?:n.t| not) (?:chosen|decided)(?: (?:yet|on (?:any )?details))?|'
    r'no (?:specific )?preferences yet|i am open to (?:suggestions|options))$', _FLAGS,
)


def _clean(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip().rstrip('.!').strip()


def _attribute(text: str) -> str | None:
    from .intent import _normalize_attribute
    text = re.sub(r'^the\s+', '', text.strip(), flags=_FLAGS)
    return _normalize_attribute({'colour': 'color', 'fabric': 'material',
                                 'sizing': 'size'}.get(text.casefold(), text))


def _value(text: str) -> tuple[str, str | None]:
    from .intent import _candidate_attribute
    text = _clean(text)
    text = _POSITIVE.sub('', text, count=1)
    text = re.sub(r'^(?:to be|in|made (?:of|from)|with)\s+', '', text, flags=_FLAGS)
    text = re.sub(r'(?:,\s*|\s+)(?:instead|please)$', '', text, flags=_FLAGS)
    label = _LABEL.fullmatch(text)
    attr, ambiguous = _candidate_attribute(text)
    if ((ambiguous and not label) or not text or len(text) > 256
            or re.search(r'\b(?:not|no|without|but|or|instead of|rather than|'
                         r'replace|switch|withdraw|remove|change|drop)\b', text, _FLAGS)):
        raise ValueError('ambiguous value')
    if label:
        return text, _attribute(label['attribute'])
    return text, attr


def _key(text: str) -> str:
    text = _clean(text)
    label = _LABEL.fullmatch(text)
    return _clean(label['value'] if label else text).casefold()


def reduce_prose_intent(state: IntentState, message: str, turn: int) -> IntentState | None:
    """Interpret an entire unsupported message, or leave the old fallback intact."""
    from .intent import Requirement, infer_requirement_importance

    message = _clean(message)
    if not message or len(message) > 2048 or _UNSAFE.search(message):
        return None
    category = state.category
    initial = False
    if turn == 1:
        opening = _OPENING.fullmatch(message)
        if opening:
            phrase = opening['category'].strip()
            # Do not promote an embedded requirement into a category name.
            if re.search(r'\b(?:with|without|in|that|which|but|and|not|something|anything)\b', phrase, _FLAGS):
                return None
            category = phrase
            message = _clean(opening['body'] or '')
            initial = True
            if not message or _BROWSING.fullmatch(message):
                return replace(state, category=category, last_turn=turn)
    if '?' in message:
        return None
    # Periods within decimal numbers and values remain untouched.
    clauses = re.split(r'\s*;\s*|(?<=[.!])\s+(?=[A-Z])', message)
    if len(clauses) > 6 or len(state.requirements) > 24 or len(state.excluded) > 16:
        return None
    requirements = list(state.requirements)
    original_requirements = tuple(state.requirements)
    exclusions = list(state.excluded)
    declined = set(state.no_preference)
    destructive = False
    withdrawn_preference = False
    keep_remaining = False

    def referenced(raw: str) -> list[int]:
        reference = _clean(raw).casefold()
        if reference in {'my earlier preference', 'my previous preference',
                         'the earlier preference', 'the previous preference'}:
            indices = [i for i, req in enumerate(requirements)
                       if req.source in {'initial_explicit', 'initial_tentative', 'override'}]
            if len(indices) > 1:
                raise ValueError('ambiguous preference reference')
            return indices
        return [i for i, req in enumerate(requirements) if _key(req.value) == _key(raw)]

    def remove(indices: list[int]) -> None:
        nonlocal requirements, destructive
        requirements = [req for i, req in enumerate(requirements) if i not in indices]
        destructive |= bool(indices)

    def add(raw: str, *, replacing: bool = False, old: str | None = None,
            explicit_attribute: str | None = None) -> None:
        nonlocal requirements, exclusions, destructive
        value, attr = _value(raw)
        if explicit_attribute:
            if attr is not None and attr != explicit_attribute:
                raise ValueError('contradictory slot')
            attr = explicit_attribute
        indices = referenced(old) if old else []
        if old and len(indices) != 1:
            raise ValueError('ambiguous old reference')
        if indices:
            prior = requirements[indices[0]]
            if attr is not None and prior.attribute not in {None, attr}:
                raise ValueError('cross-slot replacement')
            if attr is None and prior.attribute not in {None, 'feature', 'other', 'brand'}:
                raise ValueError('untyped replacement')
            attr = attr or prior.attribute
        if replacing and not indices:
            if attr is None:
                raise ValueError('unresolved replacement')
            indices = [i for i, req in enumerate(requirements) if req.attribute == attr]
            if not indices:
                raise ValueError('replacement has no matching slot')
        if replacing:
            # A combined requirement cannot be removed as if it were one slot.
            if any(';' in requirements[i].value for i in indices):
                raise ValueError('compound prior requirement')
            remove(indices)
            destructive = True
        requirements = [req for req in requirements if _key(req.value) != _key(value)]
        exclusions = [item for item in exclusions if _key(item) != _key(value)]
        declined.discard(attr)
        source = 'override' if replacing or withdrawn_preference else 'initial_explicit' if initial else 'answer'
        if initial and re.match(r'^i prefer\b', raw, _FLAGS):
            source = 'initial_tentative'
        # Untyped semantic evidence remains soft rather than inventing a hard slot.
        requirements.append(Requirement(value=value, source=source, turn=turn,
                                        attribute=attr, strength='soft' if attr is None else None,
                                        importance=infer_requirement_importance(raw, source, attr)))

    try:
        for clause in clauses:
            clause = _clean(clause)
            clause = re.sub(r'^(?:(?:actually|now|also),?\s+|instead,\s+|please\s+)', '', clause, flags=_FLAGS)
            if not clause:
                raise ValueError('empty clause')
            clear = _CLEAR.fullmatch(clause)
            withdrawal = _WITHDRAW.fullmatch(clause)
            replacement = _REPLACE.fullmatch(clause)
            instead = _INSTEAD.fullmatch(clause) or _CONTRAST.fullmatch(clause)
            reversed_replacement = _REVERSED.fullmatch(clause)
            setting = _SET.fullmatch(clause)
            exclusion = _EXCLUDE.fullmatch(clause)
            contextual = _CONTEXT.fullmatch(clause)
            if clear:
                attr = _attribute(next(value for value in clear.groups() if value))
                if attr is None or attr == 'category':
                    raise ValueError('unknown cleared slot')
                remove([i for i, req in enumerate(requirements) if req.attribute == attr])
                from .intent import _exclusion_matches_attribute
                exclusions = [item for item in exclusions if not _exclusion_matches_attribute(item, attr)]
                declined.add(attr)
                destructive = True
            elif replacement:
                add(replacement[2], replacing=True, old=replacement[1])
            elif reversed_replacement:
                add(reversed_replacement[2], replacing=True, old=reversed_replacement[1])
            elif instead:
                add(instead[1], replacing=True, old=instead[2])
            elif setting:
                add(setting['value'], replacing=True,
                    explicit_attribute=_attribute(setting['slot']) if setting['slot'] else None)
            elif withdrawal:
                raw = next(value for value in withdrawal.groups() if value)
                indices = referenced(raw)
                # A repeated withdrawal after a replacement is an idempotent no-op.
                if not indices and not (destructive and any(
                    _key(req.value) == _key(raw) for req in original_requirements
                )):
                    raise ValueError('unknown withdrawal reference')
                withdrawn_preference |= bool(indices)
                remove(indices)
            elif exclusion:
                value, attr = _value(exclusion[1])
                if attr is None and not referenced(value):
                    raise ValueError('ungrounded exclusion')
                remove(referenced(value))
                exclusions = [item for item in exclusions if _key(item) != _key(value)]
                exclusions.append(value)
                destructive = True
            elif contextual:
                attr = _attribute(contextual[1])
                if attr is None or attr in {'category', 'other'}:
                    raise ValueError('unknown contextual slot')
                add(contextual[2], explicit_attribute=attr)
            elif _POSITIVE.match(clause) or _LABEL.fullmatch(clause):
                add(clause)
            elif clause.casefold() in {'keep everything else', 'keep all other preferences'}:
                # The remaining validated operations already preserve other slots.
                # This clause alone supplies no actionable shopping preference.
                keep_remaining = True
            elif clause.casefold().startswith('keep '):
                if not referenced(clause[5:]):
                    raise ValueError('unknown retained reference')
            else:
                # Typed bare answers require a real question context.
                value, attr = _value(clause)
                if state.last_asked_attribute != attr or attr is None:
                    raise ValueError('unrecognized clause')
                add(value)
        if keep_remaining and not (destructive or tuple(requirements) != original_requirements):
            raise ValueError('no accompanying intent operation')
        if len(requirements) > 24 or len(exclusions) > 16:
            return None
        return replace(state, category=category, requirements=tuple(requirements),
                       excluded=tuple(exclusions), no_preference=frozenset(declined),
                       intent_version=state.intent_version + int(destructive), last_turn=turn)
    except ValueError:
        return None
