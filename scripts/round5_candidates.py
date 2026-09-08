"""Explicit round-five research; the production adapter never imports this."""
from __future__ import annotations

from conversational_search.decision import ProtocolObservation, recognize_protocol_observation
from starter.agent import Agent as Baseline


ARMS = ("language_top1", "cold_answer", "first_answer", "cold_continuation", "language_prior", "cold_vector")


def vector_question(ids, resolution, *, current_turn, top_k, baseline_action):
    """Constrain each modeled metric before optimizing expected utility."""
    from functools import lru_cache
    from conversational_search.exposure import _protocol_enumeration_plan
    from conversational_search.protocol import CandidateReplyStatus, PROTOCOL_ACTIONS, remaining_reply
    from scripts.finals_candidates import hypotheses_for, branches_for

    width, baseline_question = baseline_action
    if len(ids) > 200 or set(ids) != set(resolution.candidate_ids):
        return baseline_action
    hypotheses = hypotheses_for(ids, resolution)

    def plus(a, b):
        return tuple(x + y for x, y in zip(a, b))

    def immediate(count, turn):
        return count, sum(1 / rank for rank in range(1, count + 1)), count * (11 - turn) / 10

    @lru_cache(maxsize=None)
    def exhausted(count, turn):
        if not count or turn > 10:
            return 0.0, 0.0, 0.0
        batch = _protocol_enumeration_plan(count, current_turn=turn, top_k=min(top_k, count))[1]
        return plus(immediate(batch, turn), exhausted(count - batch, turn + 1))

    @lru_cache(maxsize=None)
    def future(remaining, turn):
        if not remaining or turn > 10:
            return 0.0, 0.0, 0.0
        if turn == 10:
            return immediate(min(top_k, len(remaining)), turn)
        if not any(remaining_reply(card, "other", disclosed).status is CandidateReplyStatus.DISCLOSURE
                   for _, card, disclosed in remaining):
            return exhausted(len(remaining), turn)
        value = immediate(1, turn)
        for branch in branches_for(remaining[1:], "other"):
            value = plus(value, future(branch, turn + 1))
        return value

    def evaluate(question):
        value = immediate(width, current_turn)
        for branch in branches_for(hypotheses[width:], question):
            value = plus(value, future(branch, current_turn + 1))
        return value

    baseline = evaluate(baseline_question)
    score = lambda values: .5 * values[0] + .3 * values[1] + .2 * values[2]
    best_score, best_question = score(baseline), baseline_question
    for question in PROTOCOL_ACTIONS:
        if question in {"category", "brand", baseline_question}:
            continue
        values = evaluate(question)
        if any(x + 1e-12 < y for x, y in zip(values, baseline)):
            continue
        candidate_score = score(values)
        if candidate_score > best_score + 1e-12:
            best_score, best_question = candidate_score, question
    return width, best_question


def make_agent(arm, catalog):
    if arm not in ARMS:
        raise ValueError("unknown round-five arm")
    if arm == "language_prior":
        class LanguagePrior(Baseline):
            def respond(self, session_id, user_message, turn, top_k):
                self._research_natural = (
                    not self._protocol_consistency.get(session_id, False)
                    or recognize_protocol_observation(user_message, turn)
                    is ProtocolObservation.UNSUPPORTED)
                try:
                    return super().respond(session_id, user_message, turn, top_k)
                finally:
                    self._research_natural = False

            def _apply_exact_evidence_ranking(self, state, ids, **kwargs):
                if self._research_natural and not kwargs.get("protocol_events"):
                    evidence = self._retriever.candidate_protocol_evidence(ids)
                    counts = {e.parent_asin: e.popularity or 0 for e in evidence}
                    order = tuple(sorted(ids, key=lambda a: -counts.get(a, 0)))
                    self.research_diagnostics["interventions"] += order != ids
                    ids = order
                return super()._apply_exact_evidence_ranking(state, ids, **kwargs)
        agent = LanguagePrior(catalog)
        agent.research_diagnostics = {"interventions": 0, "errors": 0}
        return agent
    if arm == "language_top1":
        class LanguageTop1(Baseline):
            def respond(self, session_id, user_message, turn, top_k):
                # Reducing the request before the service acts keeps novelty
                # memory truthful: an undisplayed tail is never recorded shown.
                valid = (session_id in self._sessions and isinstance(user_message, str)
                         and type(turn) is int and 1 <= turn < 10
                         and type(top_k) is int and top_k > 1)
                unsupported = valid and (
                    not self._protocol_consistency.get(session_id, False)
                    or recognize_protocol_observation(user_message, turn)
                    is ProtocolObservation.UNSUPPORTED)
                if unsupported:
                    self.research_diagnostics["interventions"] += 1
                return super().respond(session_id, user_message, turn, 1 if unsupported else top_k)
        agent = LanguageTop1(catalog)
        agent.research_diagnostics = {"interventions": 0, "errors": 0}
        return agent

    from conversational_search import exposure
    from scripts.finals_candidates import make_agent as prior_agent, answer_value_action
    if arm == "first_answer":
        from scripts.early_probe_candidates import make_agent as early_agent
        agent = early_agent("first_turn_prior", catalog)
    else:
        agent = prior_agent("support_cold_prior", catalog)
    original = exposure.plan_protocol_pareto_action

    def planner(ids, resolution, **kwargs):
        if set(ids) != set(resolution.candidate_ids):
            return original(ids, resolution, **kwargs)
        agent.research_diagnostics["question_model_calls"] += 1
        if arm == "cold_vector":
            baseline_action = original(ids, resolution, **kwargs)
            action = vector_question(ids, resolution, **kwargs, baseline_action=baseline_action)
            agent.research_diagnostics["question_changes"] += action != baseline_action
            return action
        if arm == "cold_continuation":
            from scripts.direct_belief import opportunity_action
            _, width, question = opportunity_action(ids, resolution, **kwargs, allow_reorder=False)
            return width, question
        return answer_value_action(ids, resolution, **kwargs)

    agent.research_diagnostics["question_model_calls"] = 0
    agent.research_diagnostics["question_changes"] = 0
    exposure.plan_protocol_pareto_action = planner
    return agent
