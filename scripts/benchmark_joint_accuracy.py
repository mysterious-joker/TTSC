"""Explicit joint-action arms under unchanged benchmark instrumentation."""
from scripts import benchmark_finalists as runner
from scripts.joint_accuracy_candidates import ARMS, make_agent

if __name__ == '__main__':
    original = runner.local_agent
    runner.ARMS = (*runner.ARMS,*ARMS)
    runner.local_agent = lambda arm,catalog: make_agent(arm,catalog) if arm in ARMS else original(arm,catalog)
    runner.main()
