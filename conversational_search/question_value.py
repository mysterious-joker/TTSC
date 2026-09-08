"""Metric-constrained questions over complete, exactly recognized support.

The finite continuation keeps survivor ordering fixed. Constraints apply to
that model's aggregate hits, reciprocal ranks and turn efficiency; they are
not a guarantee about future live retrieval or the unknown target population.
"""
from __future__ import annotations

from functools import lru_cache

from conversational_search.exposure import (
    _protocol_enumeration_plan,
    plan_protocol_pareto_action,
)
from conversational_search.protocol import (
    CandidateReplyStatus,
    PROTOCOL_ACTIONS,
    remaining_reply,
)


def _visible_branches(hypotheses, question):
    groups = {}
    for asin, card, disclosed in hypotheses:
        reply = remaining_reply(card, question, disclosed)
        updated = tuple(sorted(set(disclosed).union(reply.values)))
        groups.setdefault(reply.reply_text, []).append((asin, card, updated))
    return tuple(tuple(group) for group in groups.values())


def plan_metric_constrained_question(ids, resolution, *, current_turn, top_k):
    baseline_action = plan_protocol_pareto_action(
        ids, resolution, current_turn=current_turn, top_k=top_k,
    )
    if len(ids) > 200 or set(ids) != set(resolution.candidate_ids):
        return baseline_action
    by_id = {asin: (g.card, g.disclosed_values)
             for g in resolution.groups for asin in g.parent_asins}
    if set(by_id) != set(ids):
        return baseline_action
    hypotheses = tuple((asin, *by_id[asin]) for asin in ids)
    width, baseline_question = baseline_action

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
        for branch in _visible_branches(remaining[1:], "other"):
            value = plus(value, future(branch, turn + 1))
        return value

    def evaluate(question):
        value = immediate(width, current_turn)
        for branch in _visible_branches(hypotheses[width:], question):
            value = plus(value, future(branch, current_turn + 1))
        return value

    baseline = evaluate(baseline_question)
    score = lambda values: .5 * values[0] + .3 * values[1] + .2 * values[2]
    best_score, best_question = score(baseline), baseline_question
    # With the same displayed prefix, no remaining target can score before
    # next turn or above rank one. Stop if the baseline attains that bound.
    upper = plus(immediate(width, current_turn),
                 (len(ids) - width, len(ids) - width,
                  (len(ids) - width) * (10 - current_turn) / 10))
    if score(upper) <= best_score + 1e-12:
        return baseline_action
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
