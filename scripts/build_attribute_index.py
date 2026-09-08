"""Build the experimental sidecar from catalog fields only."""
import argparse
import json
from pathlib import Path
from conversational_search.attribute_index import build_attribute_index

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, default=Path('data/catalog.jsonl'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--omit-details', action='store_true', help='Stress only the new index; do not modify the catalog.')
    args = parser.parse_args()
    report = build_attribute_index(args.catalog, args.output, omit_details=args.omit_details)
    report['bytes'] = args.output.stat().st_size
    print(json.dumps(report), flush=True)
