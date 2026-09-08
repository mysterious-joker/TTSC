"""Explicit actual-policy rollout experiment under unchanged scoring."""
from scripts import benchmark_finalists as runner
from scripts.verified_accuracy_candidate import make_agent

if __name__ == '__main__':
    original=runner.local_agent
    runner.ARMS=(*runner.ARMS,'joint_verified')
    runner.local_agent=lambda arm,catalog: make_agent(catalog) if arm=='joint_verified' else original(arm,catalog)
    runner.main()
