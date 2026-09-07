"""Research-only complete-belief controller; no evaluation labels are read."""
from __future__ import annotations

from functools import lru_cache

from starter.agent import Agent as Baseline
from conversational_search.intent import apply_user_message, record_question
from conversational_search.protocol import CandidateReplyStatus, PROTOCOL_ACTIONS, ProtocolEventKind, remaining_reply
from conversational_search.protocol_index import resolve_protocol_transcript, protocol_probe_question
from conversational_search.exposure import plan_protocol_pareto_action
from conversational_search.questions import QUESTION_TEXT
from conversational_search.slates import SlateState
from conversational_search.utility_planner import hit_utility
from scripts.finals_candidates import answer_value_action, branches_for, hypotheses_for


@lru_cache(maxsize=65536)
def enumeration(count, turn, top_k):
    """Sum of uniform per-target utilities; shared bounded count-only cache."""
    if not count or turn > 10:
        return 0.0, 0
    best = (-1.0, 0)
    immediate = 0.0
    for width in range(1, min(count, top_k) + 1):
        immediate += hit_utility(turn, width)
        value = immediate + enumeration(count - width, turn + 1, top_k)[0]
        if value > best[0] + 1e-12 or abs(value - best[0]) <= 1e-12:
            best = value, width
    return best


def opportunity_action(ids, resolution, *, current_turn, top_k, allow_reorder=True):
    """Joint rank-one probe/question, then fixed rank-one/other continuation.

    Consider the first top_k prior candidates as probes; cover all hypotheses
    when valuing replies. Bound expensive planning to complete supports <=200.
    Equal utility retains the catalog prior. This is a uniform-world model,
    not an estimate of the private evaluator's purchase distribution.
    """
    if len(ids) > 200:
        width, question = answer_value_action(ids, resolution, current_turn=current_turn, top_k=top_k)
        return ids, width, question
    hypotheses = hypotheses_for(ids, resolution)

    @lru_cache(maxsize=None)
    def future(remaining, turn):
        if not remaining or turn > 10:
            return 0.0
        if turn == 10:
            return sum(hit_utility(turn, rank) for rank in range(1, min(top_k, len(remaining)) + 1))
        if not any(remaining_reply(card, "other", disclosed).status is CandidateReplyStatus.DISCLOSURE
                   for _, card, disclosed in remaining):
            return enumeration(len(remaining), turn, top_k)[0]
        return hit_utility(turn, 1) + sum(future(branch, turn + 1)
                                        for branch in branches_for(remaining[1:], "other"))

    best_value, best_probe, best_question = -1.0, 0, "other"
    for probe in range(min(top_k, len(hypotheses)) if allow_reorder else 1):
        rest = hypotheses[:probe] + hypotheses[probe + 1:]
        seen = set()
        for question in ("other", *(q for q in PROTOCOL_ACTIONS if q not in {"other", "category", "brand"})):
            branches = branches_for(rest, question)
            if branches in seen:
                continue
            seen.add(branches)
            value = hit_utility(current_turn, 1) + sum(future(branch, current_turn + 1) for branch in branches)
            if value > best_value + 1e-12:
                best_value, best_probe, best_question = value, probe, question
    order = (ids[best_probe], *ids[:best_probe], *ids[best_probe + 1:])
    return order, 1, best_question


class DirectBeliefAgent(Baseline):
    def __init__(self, catalog_path, *, arm="direct_prior"):
        super().__init__(catalog_path)
        if arm not in {"direct_prior", "direct_value", "direct_opportunity"}:
            raise ValueError("unknown direct-belief arm")
        self.arm = arm
        self._category_evidence = lru_cache(maxsize=256)(self._retriever.protocol_category_evidence)
        self.research_diagnostics = {"direct_calls": 0, "fallback_calls": 0, "errors": 0,
                                     "retrieval_calls_avoided": 0, "opportunity_probe_changes": 0}

    def respond(self, session_id, user_message, turn, top_k):
        # Let the original implementation own request validation and unsupported
        # protocol behavior. Stage observation changes transactionally so a
        # fallback sees the original prior state and only observes this turn once.
        if (session_id not in self._sessions or not isinstance(user_message, str)
                or isinstance(top_k, bool) or not isinstance(top_k, int) or top_k <= 0
                or not self._protocol_consistency.get(session_id, False)):
            self.research_diagnostics["fallback_calls"] += 1
            return super().respond(session_id, user_message, turn, top_k)
        maps = (self._protocol_consistency, self._protocol_events, self._protocol_override_pending,
                self._protocol_refuted_ids)
        saved = tuple(mapping.get(session_id) for mapping in maps)
        try:
            state = apply_user_message(self._sessions[session_id], user_message, turn, policy=self._intent_policy)
            eligible, _ = self._observe_expected_protocol_turn(
                session_id, state, user_message, turn, intent_cacheable=True)
            if eligible:
                refuted = self._protocol_refuted_ids[session_id]
                if self._protocol_pending_refutable.get(session_id, False):
                    refuted = tuple(dict.fromkeys((*refuted, *self._protocol_pending_ids[session_id])))
                events = self._protocol_events[session_id]
                evidence = self._category_evidence(state.category)
                resolution = resolve_protocol_transcript(evidence, events, observed_turn_count=turn,
                                                         refuted_ids=frozenset(refuted))
                if resolution.exact:
                    ids = resolution.candidate_ids  # complete review-count order, no lexical reranking
                    question = protocol_probe_question(resolution) if turn < 10 else None
                    width = min(top_k, len(ids)) if turn == 10 else 1
                    pending = self._protocol_override_pending[session_id]
                    locked = pending or (turn == 1 and events[0].kind is ProtocolEventKind.INITIAL_BROWSING)
                    if len(ids) == 1:
                        question = None
                    elif turn < 10 and question is None:
                        width = enumeration(len(ids), turn, top_k)[1]
                    elif turn < 10 and not locked:
                        if self.arm == "direct_prior":
                            width, question = plan_protocol_pareto_action(ids, resolution, current_turn=turn, top_k=top_k)
                        elif self.arm == "direct_value":
                            width, question = answer_value_action(ids, resolution, current_turn=turn, top_k=top_k)
                        else:
                            original_probe = ids[0]
                            ids, width, question = opportunity_action(ids, resolution, current_turn=turn, top_k=top_k)
                            self.research_diagnostics["opportunity_probe_changes"] += ids[0] != original_probe
                    recommendations = ids[:width]
                    if question is not None:
                        state = record_question(state, question)
                    self._sessions[session_id] = state
                    shown = tuple(dict.fromkeys((*self._protocol_shown_ids[session_id], *recommendations)))
                    self._slates[session_id] = SlateState(shown_ids=shown)
                    self._protocol_shown_ids[session_id] = shown
                    self._protocol_refuted_ids[session_id] = refuted
                    self._protocol_pending_ids[session_id] = recommendations
                    self._protocol_pending_refutable[session_id] = not pending
                    self._protocol_action_traces[session_id] = {
                        "protocol_mode": "direct_exact", "support_count": len(ids),
                        "question": question, "presented_width": len(recommendations),
                        "retrieval_action": "skipped_complete_support", "planner_outcome": self.arm,
                    }
                    self.research_diagnostics["direct_calls"] += 1
                    self.research_diagnostics["retrieval_calls_avoided"] += 1
                    return {"message": "Here are the closest matches based on your current preferences."
                            + (" " + QUESTION_TEXT[question] if question else ""),
                            "ask_attribute": question,
                            "recommendations": [{"parent_asin": asin} for asin in recommendations],
                            "usage": {"prompt_tokens": 0, "completion_tokens": 0}}
        except Exception:
            self.research_diagnostics["errors"] += 1
        for mapping, value in zip(maps, saved):
            mapping[session_id] = value
        self.research_diagnostics["fallback_calls"] += 1
        return super().respond(session_id, user_message, turn, top_k)
