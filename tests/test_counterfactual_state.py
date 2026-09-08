import unittest
from collections import Counter, OrderedDict

from conversational_search.intent import IntentState
from conversational_search.orchestration import BackendSnapshotToken
from scripts.verified_accuracy_candidate import fork_state


class Memory:
    def __init__(self, **values):
        self.__dict__.update(values)


class CounterfactualStateTests(unittest.TestCase):
    def test_hypothetical_feedback_and_cache_eviction_do_not_change_live_memory(self):
        token = BackendSnapshotToken()
        retriever = object()
        state = IntentState(category='Shoes', last_turn=2)
        agent = Memory(
            _retriever=retriever, _sessions={'s':state},
            _protocol_refuted_ids={'s':('old',)},
            _protocol_action_traces={'s':{'branch':[1,2]}},
            _protocol_decision_counts=[1,2], research_diagnostics={'rollout_calls':0},
            _orchestrator=Memory(_entries=OrderedDict([('s',token)]),_actions=Counter(search=1)),
        )
        shadow = fork_state(agent)
        shadow._protocol_refuted_ids['s'] = ('old','hypothetical')
        shadow._protocol_action_traces['s']['branch'].append(3)
        shadow._protocol_decision_counts[0] += 1
        shadow._orchestrator._entries.clear()
        shadow._orchestrator._actions['search'] += 1
        self.assertEqual(agent._protocol_refuted_ids['s'], ('old',))
        self.assertEqual(agent._protocol_action_traces['s']['branch'], [1,2])
        self.assertEqual(agent._protocol_decision_counts, [1,2])
        self.assertIs(agent._orchestrator._entries['s'], token)
        self.assertEqual(agent._orchestrator._actions['search'], 1)
        self.assertIs(shadow._retriever, retriever)
        self.assertIs(shadow._sessions['s'], state)
        shadow.research_diagnostics['rollout_calls'] += 1
        self.assertEqual(agent.research_diagnostics['rollout_calls'], 1)
