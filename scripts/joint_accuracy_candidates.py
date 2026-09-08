"""Research-only joint probe/question hypotheses; no evaluation data access."""
from dataclasses import replace
from functools import lru_cache
from math import sqrt

from conversational_search.protocol import CandidateReplyStatus, PROTOCOL_ACTIONS, remaining_reply
from conversational_search.exposure import _protocol_enumeration_plan
from scripts.finals_candidates import hypotheses_for, branches_for

ARMS = ('joint_uniform', 'joint_dual')


def joint_action(ids, resolution, popularity, *, current_turn, top_k, baseline_action, dual):
    width, baseline_question = baseline_action
    if width != 1 or current_turn >= 10 or not 1 < len(ids) <= 200 or set(ids) != set(resolution.candidate_ids):
        return ids, baseline_action
    hypotheses = hypotheses_for(ids, resolution)
    weights = {asin: sqrt(1 + max(0, popularity.get(asin, 0))) for asin in ids}

    def plus(a, b):
        return tuple(x+y for x,y in zip(a,b))

    def immediate(rows, turn):
        return (len(rows), sum(1/r for r in range(1,len(rows)+1)), len(rows)*(11-turn)/10,
                sum(weights[a] for a,_,_ in rows),
                sum(weights[a]/r for r,(a,_,_) in enumerate(rows,1)),
                sum(weights[a]*(11-turn)/10 for a,_,_ in rows))

    @lru_cache(maxsize=None)
    def future(rows, turn):
        if not rows or turn > 10:
            return (0.,)*6
        if turn == 10:
            return immediate(rows[:top_k], turn)
        if not any(remaining_reply(c,'other',d).status is CandidateReplyStatus.DISCLOSURE for _,c,d in rows):
            batch = _protocol_enumeration_plan(len(rows), current_turn=turn, top_k=min(top_k,len(rows)))[1]
            return plus(immediate(rows[:batch],turn), future(rows[batch:],turn+1))
        value = immediate(rows[:1],turn)
        for branch in branches_for(rows[1:], 'other'):
            value = plus(value, future(branch,turn+1))
        return value

    def evaluate(probe, question):
        rest = hypotheses[:probe]+hypotheses[probe+1:]
        value = immediate(hypotheses[probe:probe+1],current_turn)
        for branch in branches_for(rest,question):
            value = plus(value,future(branch,current_turn+1))
        return value

    def utility(value):
        return (.5*value[0]+.3*value[1]+.2*value[2],
                .5*value[3]+.3*value[4]+.2*value[5])

    baseline = evaluate(0,baseline_question)
    best = utility(baseline)
    best_probe, best_question = 0, baseline_question
    for probe in range(len(hypotheses)):
        for question in PROTOCOL_ACTIONS:
            if question in {'category','brand'} or (probe == 0 and question == baseline_question):
                continue
            value = evaluate(probe,question)
            if any(x+1e-12 < y for x,y in zip(value[:6 if dual else 3],baseline)):
                continue
            candidate = utility(value)
            if candidate[0] > best[0]+1e-12 or (abs(candidate[0]-best[0]) <= 1e-12 and candidate[1] > best[1]+1e-12):
                best = candidate
                best_probe,best_question = probe,question
    order = (ids[best_probe], *ids[:best_probe], *ids[best_probe+1:])
    return order, (1,best_question)


def make_agent(arm, catalog):
    if arm not in ARMS:
        raise ValueError(arm)
    from starter.agent import Agent
    from conversational_search import service, question_value
    from conversational_search.protocol import ProtocolEventKind
    resolve = service.resolve_protocol_transcript
    planner = question_value.plan_metric_constrained_question
    context = {'resolution':None,'planned':None}
    diagnostics = {'eligible':0,'probe_changes':0,'question_changes':0,'errors':0}

    def observed_resolve(*args,**kwargs):
        result = resolve(*args,**kwargs)
        context['resolution'] = result if result.exact else None
        return result

    def observed_planner(ids,resolution,**kwargs):
        planned = context['planned']
        if planned is not None and ids == planned[0]:
            return planned[1]
        return planner(ids,resolution,**kwargs)

    service.resolve_protocol_transcript = observed_resolve
    question_value.plan_metric_constrained_question = observed_planner

    class JointAgent(Agent):
        def respond(self,session_id,user_message,turn,top_k):
            context.update(resolution=None,planned=None,session_id=session_id,turn=turn,top_k=top_k)
            try:
                return super().respond(session_id,user_message,turn,top_k)
            finally:
                context.update(resolution=None,planned=None)

        def _apply_exact_evidence_ranking(self,state,ids,**kwargs):
            result = super()._apply_exact_evidence_ranking(state,ids,**kwargs)
            resolution = context['resolution']
            session = context['session_id']
            events = self._protocol_events.get(session,())
            if (resolution is None or result.result is None or context['turn'] >= 10
                    or self._protocol_override_pending.get(session,False)
                    or (len(events)==1 and events[0].kind is ProtocolEventKind.INITIAL_BROWSING)
                    or set(result.output_ranked_ids) != set(resolution.candidate_ids)
                    or len(resolution.candidate_ids)>200):
                return result
            ids = result.output_ranked_ids
            baseline = planner(ids,resolution,current_turn=context['turn'],top_k=min(context['top_k'],len(ids)))
            if baseline[0] != 1 or len(ids)<2:
                return result
            diagnostics['eligible'] += 1
            order,action = joint_action(ids,resolution,{e.parent_asin:e.popularity or 0 for e in result.evidence},
                current_turn=context['turn'],top_k=min(context['top_k'],len(ids)),baseline_action=baseline,
                dual=arm=='joint_dual')
            diagnostics['probe_changes'] += order != ids
            diagnostics['question_changes'] += action != baseline
            context['planned'] = order,action
            return replace(result,output_ranked_ids=order,result=replace(result.result,ranked_ids=order))

    agent = JointAgent(catalog)
    agent.research_diagnostics = diagnostics
    return agent
