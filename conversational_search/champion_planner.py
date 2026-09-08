"""Bounded protocol planning for the competition submission."""

from __future__ import annotations

from functools import lru_cache
from typing import Sequence

from conversational_search.exposure import _protocol_enumeration_plan
from conversational_search.protocol import (
    PROTOCOL_ACTIONS,
    CandidateReplyStatus,
    DisclosureCard,
    ProductProtocolEvidence,
    remaining_reply,
)
from conversational_search.protocol_index import ProtocolResolution
from conversational_search.utility_planner import hit_utility


Hypothesis = tuple[str, DisclosureCard, tuple[str, ...]]


def _hypotheses(
    ids: Sequence[str], resolution: ProtocolResolution
) -> tuple[Hypothesis, ...]:
    by_id = {
        asin: (group.card, group.disclosed_values)
        for group in resolution.groups
        for asin in group.parent_asins
    }
    order = tuple(dict.fromkeys((*ids, *resolution.candidate_ids)))
    return tuple((asin, *by_id[asin]) for asin in order if asin in by_id)


def _branches(
    rows: Sequence[Hypothesis], question: str
) -> tuple[tuple[Hypothesis, ...], ...]:
    groups: dict[str, list[Hypothesis]] = {}
    for asin, card, disclosed in rows:
        reply = remaining_reply(card, question, disclosed)
        updated = tuple(sorted(set(disclosed).union(reply.values)))
        groups.setdefault(reply.reply_text, []).append((asin, card, updated))
    return tuple(tuple(group) for group in groups.values())


def plan_protocol_two_step_action(
    ids: Sequence[str],
    resolution: ProtocolResolution,
    *,
    current_turn: int,
    top_k: int,
) -> tuple[int, str]:
    """Choose the highest-utility action over two exact simulator replies."""

    ordered = tuple(ids)
    rows = _hypotheses(ordered, resolution)
    if (
        current_turn >= 10
        or not rows
        or len(rows) > 200
        or set(ordered) != set(resolution.candidate_ids)
        or len(rows) != len(ordered)
    ):
        from conversational_search.exposure import plan_protocol_pareto_action

        return plan_protocol_pareto_action(
            ordered,
            resolution,
            current_turn=current_turn,
            top_k=top_k,
        )

    @lru_cache(maxsize=None)
    def solve(remaining: tuple[Hypothesis, ...], turn: int, depth: int):
        if not remaining or turn > 10:
            return 0.0, 0, None
        count = len(remaining)
        if turn == 10 or depth == 0:
            width = min(top_k, count)
            value = sum(hit_utility(turn, rank) for rank in range(1, width + 1))
            return value, width, None
        if not any(
            remaining_reply(card, "other", disclosed).status
            is CandidateReplyStatus.DISCLOSURE
            for _, card, disclosed in remaining
        ):
            value, width = _protocol_enumeration_plan(
                count, current_turn=turn, top_k=min(top_k, count)
            )
            return count * value, width, None
        best = (-1.0, 1, "other")
        for width in range(1, min(top_k, count) + 1):
            immediate = sum(
                hit_utility(turn, rank) for rank in range(1, width + 1)
            )
            seen = set()
            for question in PROTOCOL_ACTIONS:
                if question in {"category", "brand"}:
                    continue
                branches = _branches(remaining[width:], question)
                if branches in seen:
                    continue
                seen.add(branches)
                value = immediate + sum(
                    solve(branch, turn + 1, depth - 1)[0]
                    for branch in branches
                )
                if value > best[0] + 1e-12:
                    best = value, width, question
        return best

    _, width, question = solve(rows, current_turn, 2)
    return width, question or "other"


def plan_purchase_prior_probe_order(
    ids: Sequence[str],
    resolution: ProtocolResolution,
    evidence: Sequence[ProductProtocolEvidence],
    *,
    current_turn: int,
    top_k: int,
) -> tuple[str, ...]:
    """Move one recoverable popular probe while guarding uniform metrics."""

    from conversational_search.question_value import (
        plan_metric_constrained_question,
    )

    ordered = tuple(ids)
    if (
        current_turn >= 10
        or not 1 < len(ordered) <= 200
        or len(ordered) != len(set(ordered))
        or set(ordered) != set(resolution.candidate_ids)
        or top_k <= 0
    ):
        return ordered
    baseline_action = plan_metric_constrained_question(
        ordered,
        resolution,
        current_turn=current_turn,
        top_k=min(top_k, len(ordered)),
    )
    width, baseline_question = baseline_action
    if width != 1:
        return ordered
    rows = _hypotheses(ordered, resolution)
    popularity = {item.parent_asin: item.popularity for item in evidence}
    if len(rows) != len(ordered) or any(asin not in popularity for asin in ordered):
        return ordered
    weights = {
        asin: float(1 + max(0, popularity[asin] or 0)) for asin in ordered
    }

    def add(left, right):
        return tuple(a + b for a, b in zip(left, right))

    def immediate(shown: Sequence[Hypothesis], turn: int):
        uniform_count = float(len(shown))
        uniform_rr = sum(1 / rank for rank in range(1, len(shown) + 1))
        uniform_efficiency = uniform_count * (11 - turn) / 10
        weighted_count = sum(weights[asin] for asin, _, _ in shown)
        weighted_rr = sum(
            weights[asin] / rank
            for rank, (asin, _, _) in enumerate(shown, 1)
        )
        weighted_efficiency = weighted_count * (11 - turn) / 10
        return (
            uniform_count,
            uniform_rr,
            uniform_efficiency,
            weighted_count,
            weighted_rr,
            weighted_efficiency,
        )

    @lru_cache(maxsize=None)
    def continuation(remaining: tuple[Hypothesis, ...], turn: int):
        if not remaining or turn > 10:
            return (0.0,) * 6
        if turn == 10:
            return immediate(remaining[:top_k], turn)
        if not any(
            remaining_reply(card, "other", disclosed).status
            is CandidateReplyStatus.DISCLOSURE
            for _, card, disclosed in remaining
        ):
            batch = _protocol_enumeration_plan(
                len(remaining),
                current_turn=turn,
                top_k=min(top_k, len(remaining)),
            )[1]
            return add(
                immediate(remaining[:batch], turn),
                continuation(remaining[batch:], turn + 1),
            )
        value = immediate(remaining[:1], turn)
        for branch in _branches(remaining[1:], "other"):
            value = add(value, continuation(branch, turn + 1))
        return value

    def evaluate(probe: int, question: str):
        shown = rows[probe : probe + 1]
        remaining = rows[:probe] + rows[probe + 1 :]
        value = immediate(shown, current_turn)
        for branch in _branches(remaining, question):
            value = add(value, continuation(branch, current_turn + 1))
        return value

    def weighted_score(value):
        return 0.5 * value[3] + 0.3 * value[4] + 0.2 * value[5]

    baseline = evaluate(0, baseline_question)
    best_value = baseline
    best_probe = 0
    seen_actions = set()
    for probe in range(len(rows)):
        for question in PROTOCOL_ACTIONS:
            if question in {"category", "brand"}:
                continue
            value = evaluate(probe, question)
            signature = value, probe
            if signature in seen_actions:
                continue
            seen_actions.add(signature)
            if any(value[index] + 1e-12 < baseline[index] for index in range(3)):
                continue
            if weighted_score(value) > weighted_score(best_value) + 1e-12:
                best_value = value
                best_probe = probe
    return (
        ordered[best_probe],
        *ordered[:best_probe],
        *ordered[best_probe + 1 :],
    )
