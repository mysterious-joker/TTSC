"""Meaning-preserving opening/edit transforms with no target access."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


def transform(message: str) -> str:
    match = re.fullmatch(r"I'm looking for (.+)\. A key requirement is: (.+)\.", message)
    if match:
        category, clue = match.groups()
        labeled = re.fullmatch(r'(?:Color|Material): ([A-Za-z]+)', clue)
        material = re.fullmatch(r'(?:100% )?(?:cotton|polyester|nylon|leather|wool|silk|linen)', clue, re.I)
        if labeled or material:
            value = labeled[1] if labeled else clue
            return f'I need {value} {category}.'
    prefix = 'Actually, ignore my earlier preference. What I need is: '
    if message.startswith(prefix):
        value = message.removeprefix(prefix).rstrip('.')
        return f'Remove my earlier preference; I need {value}; keep everything else.'
    return message


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--catalog', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source_root.resolve()))
    from scripts import benchmark_finalists as benchmark
    import conversational_search.intent as intent
    if Path(intent.__file__).resolve().parent.parent != args.source_root.resolve():
        raise RuntimeError('incorrect source imported')
    counts = [0, 0]

    def observed(message):
        result = transform(message)
        counts[0] += result != message
        counts[1] += 1
        return result

    benchmark.paraphrase = observed
    sys.argv = ['benchmark_finalists', '--catalog', str(args.catalog.resolve()),
                '--dataset', str(args.dataset.resolve()), '--output', str(args.output.resolve()),
                '--wording', 'paraphrase']
    benchmark.main()
    report = json.loads(args.output.read_text())
    report['measurement'].update(wording='composed-opening-edits-v1',
        wording_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        transformed_messages=counts[0], total_messages=counts[1])
    args.output.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
