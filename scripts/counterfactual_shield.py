"""Research-only question shield using actual baseline continuation rollouts."""
from __future__ import annotations

from copy import copy
from dataclasses import replace

from conversational_search.protocol import remaining_reply
from conversational_search.protocol_index import MAX_PROTOCOL_OUTPUT_CANDIDATES
from conversational_search.utility_planner import hit_utility
from scripts.finals_candidates import answer_value_action, hypotheses_for


def copy_containers(value):
    """Copy mutable session containers, preserve immutable dataclasses/tokens."""
    if isinstance(value, dict):
        result = copy(value)
        for key, item in value.items():
            result[key] = copy_containers(item)
        return result
    if isinstance(value, list):
        return [copy_containers(item) for item in value]
    if isinstance(value, set):
        return value.copy()
    return value


def clone_session_memory(agent):
    """Share read-only retrieval/model assets; isolate all agent/orchestrator maps."""
    shadow = copy(agent)
    for key, value in agent.__dict__.items():
        setattr(shadow, key, copy_containers(value))
    shadow._orchestrator = copy(agent._orchestrator)
    for key, value in agent._orchestrator.__dict__.items():
        setattr(shadow._orchestrator, key, copy_containers(value))
    shadow._retriever = copy(agent._retriever)
    return shadow


def pointwise_gain(baseline, candidate):
    if not baseline or baseline.keys() != candidate.keys():
        return False
    deltas = [candidate[key] - value for key, value in baseline.items()]
    return min(deltas) >= -1e-12 and sum(deltas) > 1e-12


def make_shielded_agent(catalog):
    from starter.agent import Agent as Baseline
    from conversational_search import exposure
    from conversational_search.exposure_policy import EvidenceExposureStatus

    original_plan = exposure.plan_evidence_gated_exposure
    diagnostics = {"eligible": 0, "proposals": 0, "accepted": 0, "rejected": 0,
                   "simulation_calls": 0, "budget_rejections": 0, "errors": 0}
    context = {"simulation": False, "force_question": None, "force_turn": None}

    def outcomes(snapshot, hypotheses, session_id, message, turn, top_k, forced_question):
        context.update(simulation=True, force_question=forced_question, force_turn=turn)
        values = {}

        def visit(shadow, worlds, user_message, current_turn):
            context["calls"] += 1
            diagnostics["simulation_calls"] += 1
            if context["calls"] > 512:
                raise TimeoutError("counterfactual call budget exhausted")
            response = Baseline.respond(shadow, session_id, user_message, current_turn, top_k)
            ids = tuple(item["parent_asin"] if isinstance(item, dict) else item
                        for item in response["recommendations"])
            if len(set(ids)) != len(ids) or len(ids) > top_k:
                raise ValueError("invalid simulated slate")
            ranks = {asin: rank for rank, asin in enumerate(ids, 1)}
            groups = {}
            for asin, card, disclosed in worlds:
                if asin in ranks:
                    values[asin] = hit_utility(current_turn, ranks[asin])
                elif current_turn == 10:
                    values[asin] = 0.0
                else:
                    reply = remaining_reply(card, response["ask_attribute"], disclosed)
                    updated = tuple(sorted(set(disclosed).union(reply.values)))
                    groups.setdefault(reply.reply_text, []).append((asin, card, updated))
            for reply_text, remaining in groups.items():
                visit(clone_session_memory(shadow), tuple(remaining), reply_text, current_turn + 1)

        try:
            visit(clone_session_memory(snapshot), hypotheses, message, turn)
        finally:
            context.update(simulation=False, force_question=None, force_turn=None)
        return values

    def shielded_plan(*args, **kwargs):
        baseline = original_plan(*args, **kwargs)
        turn = kwargs["current_turn"]
        if context["simulation"]:
            if turn == context["force_turn"] and context["force_question"] is not None:
                return replace(baseline, question=context["force_question"])
            return baseline
        resolution = kwargs.get("protocol_resolution")
        if (not 1 <= turn <= 8 or kwargs.get("protocol_planning_locked")
                or resolution is None or not resolution.exact
                or not 2 <= resolution.support_count <= MAX_PROTOCOL_OUTPUT_CANDIDATES
                or baseline.width != 1
                or baseline.status is not EvidenceExposureStatus.POSTERIOR_PARETO_HORIZON
                or set(baseline.presentation_ids) != set(resolution.candidate_ids)):
            return baseline
        diagnostics["eligible"] += 1
        _, proposal = answer_value_action(baseline.presentation_ids, resolution,
                                          current_turn=turn, top_k=kwargs["requested_top_k"])
        if proposal == baseline.question:
            return baseline
        diagnostics["proposals"] += 1
        context["calls"] = 0
        try:
            hypotheses = hypotheses_for(baseline.presentation_ids, resolution)
            params = (context["snapshot"], hypotheses, context["session_id"],
                      context["message"], turn, kwargs["requested_top_k"])
            old = outcomes(*params, None)
            new = outcomes(*params, proposal)
            if pointwise_gain(old, new):
                diagnostics["accepted"] += 1
                return replace(baseline, question=proposal)
        except TimeoutError:
            diagnostics["budget_rejections"] += 1
        except Exception:
            diagnostics["errors"] += 1
        diagnostics["rejected"] += 1
        return baseline

    class ShieldedAgent(Baseline):
        def respond(self, session_id, user_message, turn, top_k):
            context.update(snapshot=clone_session_memory(self), session_id=session_id, message=user_message)
            try:
                return super().respond(session_id, user_message, turn, top_k)
            finally:
                context.pop("snapshot", None)

    exposure.plan_evidence_gated_exposure = shielded_plan
    agent = ShieldedAgent(catalog)
    agent.research_diagnostics = diagnostics
    return agent
