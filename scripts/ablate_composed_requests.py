"""Post-confirmation explanatory ablations; never used to select a new arm."""
import argparse
import importlib.util
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--without', choices=('openings', 'operations'), required=True)
    args, remaining = parser.parse_known_args()
    root = Path(__file__).resolve().parents[1]
    if args.without == 'openings':
        import conversational_search.composed_request as composed
        composed.parse_composed_request = lambda *args, **kwargs: None
    else:
        import conversational_search.intent_operations as operations
        path = root.parent / 'round8/baseline/conversational_search/intent_operations.py'
        spec = importlib.util.spec_from_file_location('conversational_search._baseline_operations', path)
        legacy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(legacy)
        operations.reduce_prose_intent = legacy.reduce_prose_intent
    from scripts.benchmark_composed_requests import main as benchmark
    sys.argv = ['benchmark_composed_requests', *remaining]
    benchmark()


if __name__ == '__main__':
    main()
