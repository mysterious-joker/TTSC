"""Research-only real-policy rollouts for proposals from the joint model."""
from copy import copy
from collections import defaultdict
from dataclasses import replace
from math import sqrt

from starter.agent import Agent
from conversational_search import service, question_value
from conversational_search.protocol import ProtocolEventKind, remaining_reply
from scripts.finals_candidates import hypotheses_for
from scripts.joint_accuracy_candidates import joint_action
from scripts.counterfactual_shield import copy_containers


def fork_state(agent):
    """Copy mutable policy memory, sharing immutable model/catalog assets."""
    child = copy(agent)
    child.__dict__ = {k: copy_containers(v) for k,v in agent.__dict__.items()}
    child.research_diagnostics = agent.research_diagnostics
    child._orchestrator = copy(agent._orchestrator)
    child._orchestrator.__dict__ = {
        k:copy_containers(v) for k,v in agent._orchestrator.__dict__.items()}
    return child


def make_agent(catalog):
    original_resolve = service.resolve_protocol_transcript
    original_planner = question_value.plan_metric_constrained_question
    context = {'simulating':False,'resolution':None,'captured':None,'forced':None}
    diagnostics = {'eligible':0,'proposals':0,'accepted':0,'rejected':0,'unexecutable':0,'rollout_calls':0,'errors':0}

    def resolve(*args,**kwargs):
        result = original_resolve(*args,**kwargs)
        if not context['simulating']:
            context['resolution'] = result if result.exact else None
        return result

    def planner(ids,resolution,**kwargs):
        forced = context['forced']
        if forced is not None and ids == forced[0]:
            return forced[1]
        return original_planner(ids,resolution,**kwargs)

    service.resolve_protocol_transcript = resolve
    question_value.plan_metric_constrained_question = planner

    def rollout(agent,response,rows,turn,session,top_k,weights):
        ranks = {r['parent_asin']:i for i,r in enumerate(response['recommendations'],1)}
        value = [0.]*6
        groups = defaultdict(list)
        for asin,card,disclosed in rows:
            if asin in ranks:
                hit=(1.,1/ranks[asin],(11-turn)/10)
                for i,x in enumerate(hit):
                    value[i] += x; value[i+3] += x*weights[asin]
            elif turn < 10:
                reply = remaining_reply(card,response['ask_attribute'],disclosed)
                updated=tuple(sorted(set(disclosed).union(reply.values)))
                groups[reply.reply_text].append((asin,card,updated))
        for message,remaining in groups.items():
            child=fork_state(agent)
            next_response=Agent.respond(child,session,message,turn+1,top_k)
            diagnostics['rollout_calls'] += 1
            continuation=rollout(child,next_response,tuple(remaining),turn+1,session,top_k,weights)
            value=[x+y for x,y in zip(value,continuation)]
        return tuple(value)

    class VerifiedAgent(Agent):
        def _apply_exact_evidence_ranking(self,state,ids,**kwargs):
            result=super()._apply_exact_evidence_ranking(state,ids,**kwargs)
            forced=context['forced']
            if forced is not None and result.result is not None and set(result.output_ranked_ids)==set(forced[0]):
                return replace(result,output_ranked_ids=forced[0],result=replace(result.result,ranked_ids=forced[0]))
            if not context['simulating'] and context['resolution'] is not None:
                context['captured']=(context['resolution'],result)
            return result

        def respond(self,session_id,user_message,turn,top_k):
            before=fork_state(self)
            context.update(resolution=None,captured=None,forced=None,simulating=False)
            baseline_response=Agent.respond(self,session_id,user_message,turn,top_k)
            captured=context['captured']
            if captured is None or turn >= 10 or len(baseline_response['recommendations']) != 1:
                return baseline_response
            resolution,result=captured
            events=self._protocol_events.get(session_id,())
            if (result.result is None or not resolution.exact or not 1<len(resolution.candidate_ids)<=200
                    or set(result.output_ranked_ids)!=set(resolution.candidate_ids)
                    or self._protocol_override_pending.get(session_id,False)
                    or (len(events)==1 and events[0].kind is ProtocolEventKind.INITIAL_BROWSING)):
                return baseline_response
            diagnostics['eligible']+=1
            ids=result.output_ranked_ids
            baseline_action=(1,baseline_response['ask_attribute'])
            popularity={e.parent_asin:e.popularity or 0 for e in result.evidence}
            proposal=joint_action(ids,resolution,popularity,current_turn=turn,top_k=min(top_k,len(ids)),
                baseline_action=baseline_action,dual=True)
            if baseline_action[1] is None:
                proposal=(proposal[0],(1,None))  # Exhausted support uses enumeration, with no question.
            if proposal==(ids,baseline_action):
                return baseline_response
            diagnostics['proposals']+=1
            rows=hypotheses_for(ids,resolution)
            weights={asin:sqrt(1+max(0,popularity.get(asin,0))) for asin in ids}
            context['simulating']=True
            try:
                baseline_value=rollout(fork_state(self),baseline_response,rows,turn,session_id,top_k,weights)
                candidate=fork_state(before)
                context['forced']=proposal
                response=Agent.respond(candidate,session_id,user_message,turn,top_k)
                context['forced']=None
                if response['recommendations'] != [{'parent_asin':proposal[0][0]}] or response['ask_attribute']!=proposal[1][1]:
                    diagnostics['unexecutable']+=1
                    diagnostics['rejected']+=1
                    return baseline_response
                candidate_value=rollout(fork_state(candidate),response,rows,turn,session_id,top_k,weights)
                scale=max(1.,sum(weights.values()))
                safe=all(x+1e-10*scale >= y for x,y in zip(candidate_value,baseline_value))
                better=any(x>y+1e-10*scale for x,y in zip(candidate_value,baseline_value))
                if safe and better:
                    self.__dict__=candidate.__dict__
                    diagnostics['accepted']+=1
                    return response
                diagnostics['rejected']+=1
            except Exception:
                diagnostics['errors']+=1
                import traceback
                traceback.print_exc()
                raise
            finally:
                context.update(simulating=False,forced=None,resolution=None,captured=None)
            return baseline_response

    agent=VerifiedAgent(catalog)
    agent.research_diagnostics=diagnostics
    return agent
