"""Opt-in attribute evidence tie-break. Never imported by starter.agent."""
from dataclasses import replace
from pathlib import Path

from conversational_search.attribute_index import AttributeIndex, query_atoms
from conversational_search.decision import ProtocolObservation, recognize_protocol_observation
from conversational_search.exact_evidence import _harmonic_beliefs
from starter.agent import Agent as Baseline


class AttributeAgent(Baseline):
    def __init__(self, catalog_path, index_path, *, counterevidence_only=False):
        super().__init__(catalog_path)
        self._attribute_counterevidence_only = counterevidence_only
        self.research_diagnostics = {'interventions': 0, 'eligible_ties': 0,
                                     'errors': 0, 'index_unavailable': 0}
        self._attribute_natural = False
        try:
            self._attribute_index = AttributeIndex(Path(index_path), Path(catalog_path))
        except Exception:
            # Fail open for absent, stale, corrupt, or incompatible research assets.
            self._attribute_index = None
            self.research_diagnostics['index_unavailable'] += 1

    def respond(self, session_id, user_message, turn, top_k):
        self._attribute_natural = (
            not self._protocol_consistency.get(session_id, False)
            or recognize_protocol_observation(user_message, turn) is ProtocolObservation.UNSUPPORTED)
        try:
            return super().respond(session_id, user_message, turn, top_k)
        finally:
            self._attribute_natural = False

    def _apply_exact_evidence_ranking(self, state, ids, **kwargs):
        context = super()._apply_exact_evidence_ranking(state, ids, **kwargs)
        if not self._attribute_natural or self._attribute_index is None or context.result is None:
            return context
        result = context.result
        tier = tuple(b.parent_asin for b in result.beliefs)
        if len(tier) < 2:
            return context
        atoms = query_atoms(state)
        if not atoms:
            return context
        self.research_diagnostics['eligible_ties'] += 1
        try:
            preferred = self._attribute_index.rerank(tier, atoms,
                counterevidence_only=self._attribute_counterevidence_only)
            if preferred == tier:
                return context
            tier_ids = frozenset(tier)
            order = iter(preferred)
            ranked = tuple(next(order) if asin in tier_ids else asin for asin in result.ranked_ids)
            support = frozenset(result.consistent_support_ids)
            revised = replace(result, ranked_ids=ranked,
                consistent_support_ids=tuple(asin for asin in ranked if asin in support),
                beliefs=_harmonic_beliefs(preferred))
            self._validate_exact_evidence_ranking(revised, expected_ids=ids)
            self.research_diagnostics['interventions'] += 1
            return replace(context, result=revised, output_ranked_ids=ranked)
        except Exception:
            self.research_diagnostics['errors'] += 1
            return context
