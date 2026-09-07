"""Research-only early ranking hypotheses; never reads evaluation labels."""
from __future__ import annotations

from dataclasses import replace

from conversational_search.protocol import CandidateReplyStatus, remaining_reply


def recoverable_probe(ids, resolution, question, *, ambiguous=False, popularity=None):
    """Select a higher-prior probe with a unique next disclosing response.

    Both changed targets must be uniquely recoverable after one answer. This
    does not pretend that a review-count order is a calibrated target posterior.
    """
    if not ids or set(ids) != set(resolution.candidate_ids) or not question:
        return None
    replies = {}
    by_id = {}
    for group in resolution.groups:
        reply = remaining_reply(group.card, question, group.disclosed_values)
        for asin in group.parent_asins:
            by_id[asin] = reply
            replies.setdefault(reply.reply_text, []).append(asin)
    def singleton(asin):
        reply = by_id[asin]
        return (reply.status is CandidateReplyStatus.DISCLOSURE
                and len(replies[reply.reply_text]) == 1)
    if not singleton(ids[0]):
        return None
    candidates = []
    for asin in resolution.candidate_ids:
        if asin == ids[0]:
            break
        if popularity is not None:
            if 1 + popularity.get(asin, 0) >= 10 * (1 + popularity.get(ids[0], 0)):
                return asin
            continue
        reply = by_id[asin]
        if ambiguous:
            if reply.status is CandidateReplyStatus.DISCLOSURE and len(replies[reply.reply_text]) > 1:
                candidates.append((len(replies[reply.reply_text]), asin))
        elif singleton(asin):
            return asin
    return max(candidates, key=lambda row: row[0])[1] if candidates else None


def make_agent(arm, catalog):
    from starter.agent import Agent as Baseline
    from conversational_search import exposure, service
    from conversational_search.protocol_index import fuse_protocol_candidates

    if arm not in {"first_turn_prior", "soft_prior", "recoverable_prior", "ambiguous_probe", "cold_ambiguous", "dominant_prior"}:
        raise ValueError("unknown early-probe arm")
    context = {"turn": 0, "resolution": None, "locked": True, "question": None}
    diagnostics = {"interventions": 0, "errors": 0, "recoverable_states": 0}

    def fuse(resolution, preferred_ids, *, limit):
        context["resolution"] = resolution if resolution.exact else None
        if not resolution.exact:
            return fuse_protocol_candidates(resolution, preferred_ids, limit=limit)
        if ((arm == "first_turn_prior" and context["turn"] == 1)
                or (arm == "cold_ambiguous" and context.get("cold", False))):
            output = resolution.candidate_ids[:limit]
        elif arm == "soft_prior":
            prior = {asin: rank for rank, asin in enumerate(resolution.candidate_ids, 1)}
            preferred = {asin: rank for rank, asin in enumerate(dict.fromkeys(preferred_ids), 1)}
            output = tuple(sorted(prior, key=lambda asin: (
                -(2 / (60 + prior[asin]) + (1 / (60 + preferred[asin]) if asin in preferred else 0)),
                prior[asin],
            ))[:limit])
        else:
            return fuse_protocol_candidates(resolution, preferred_ids, limit=limit)
        diagnostics["interventions"] += output != fuse_protocol_candidates(resolution, preferred_ids, limit=limit)
        return output

    service.fuse_protocol_candidates = fuse
    original_planner = exposure.plan_protocol_pareto_action

    def planner(ids, resolution, **kwargs):
        if context.get("planned_action") is not None:
            return context["planned_action"]
        return original_planner(ids, resolution, **kwargs)

    if arm in {"recoverable_prior", "ambiguous_probe", "cold_ambiguous", "dominant_prior"}:
        exposure.plan_protocol_pareto_action = planner

    class EarlyProbe(Baseline):
        def respond(self, session_id, user_message, turn, top_k):
            from conversational_search.intent import apply_user_message
            state = apply_user_message(self._sessions[session_id], user_message, turn)
            context.update(turn=turn, resolution=None, question=None, planned_action=None,
                           session_id=session_id, top_k=top_k,
                           cold=bool(turn == 1 and state.category and not state.requirements and not state.excluded))
            try:
                return super().respond(session_id, user_message, turn, top_k)
            finally:
                context.update(resolution=None, question=None)

        def _apply_exact_evidence_ranking(self, state, ids, **kwargs):
            result = super()._apply_exact_evidence_ranking(state, ids, **kwargs)
            resolution = context["resolution"]
            if (arm not in {"recoverable_prior", "ambiguous_probe", "cold_ambiguous", "dominant_prior"}
                    or resolution is None or result.result is None
                    or context["turn"] >= 9 or len(resolution.candidate_ids) > 200
                    or self._protocol_override_pending.get(context["session_id"], False)):
                return result
            events = self._protocol_events.get(context["session_id"], ())
            if len(events) == 1 and events[0].kind.value == "initial_browsing":
                return result
            ids = result.output_ranked_ids
            if len(ids) < 2 or set(ids) != set(resolution.candidate_ids):
                return result
            width, question = original_planner(ids, resolution, current_turn=context["turn"],
                                               top_k=min(context["top_k"], len(ids)))
            context["planned_action"] = width, question
            if width != 1:
                return result
            diagnostics["recoverable_states"] += 1
            probe = recoverable_probe(ids, resolution, question,
                                      ambiguous=arm in {"ambiguous_probe", "cold_ambiguous"},
                                      popularity=({e.parent_asin: e.popularity or 0 for e in result.evidence}
                                                  if arm == "dominant_prior" else None))
            if probe is None:
                return result
            order = (probe, *(asin for asin in ids if asin != probe))
            context["question"] = question
            diagnostics["interventions"] += 1
            return replace(result, output_ranked_ids=order,
                           result=replace(result.result, ranked_ids=order))

    agent = EarlyProbe(catalog)
    agent.research_diagnostics = diagnostics
    return agent
