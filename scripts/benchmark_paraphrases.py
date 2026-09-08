"""Run meaning-preserving message transforms through the official evaluator.

This wrapper imports the selected source tree before loading the agent. The
transform sees only the user message, never target identifiers or scenario IDs.
"""
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
        return f'Could you help me choose {match[1]}? I need {match[2]}.'
    match = re.fullmatch(r"I'm looking for (.+), but I'm still exploring\.", message)
    if match:
        return f'Please suggest {match[1]}. No specific preferences yet.'
    match = re.fullmatch(r"I'm looking for (.+?)\. (.+)", message)
    if match:
        return f'Can you help me pick {match[1]}? I prefer {match[2]}'
    prefix = 'For that, what matters is: '
    if message.startswith(prefix):
        return 'I need ' + message.removeprefix(prefix)
    prefix = 'Actually, ignore my earlier preference. What I need is: '
    if message.startswith(prefix):
        return 'Drop my earlier preference; I need ' + message.removeprefix(prefix)
    match = re.fullmatch(r"I don't have (?:an additional|a) preference for (.+?)(?:; please use your judgment)?\.", message)
    if match:
        return f'Any {match[1]} works for me.'
    return message


def paraphrase_value(value: str) -> str:
    """Small reviewed equivalences; do not invent or drop product preferences."""
    changes = {
        'machine wash': 'can be washed in a washing machine',
        'hand wash only': 'requires washing by hand',
        '100% cotton': 'pure cotton',
    }
    parts = value.rstrip('.').split('; ')
    converted = []
    for part in parts:
        key = part.casefold()
        if key in changes:
            converted.append(changes[key])
        elif re.fullmatch(r'color: [a-z]+', key):
            color = part.split(': ', 1)[1]
            color = {'grey': 'gray', 'gray': 'grey'}.get(color.casefold(), color)
            converted.append(f'colour = {color}')
        elif key in {'cotton', 'leather', 'polyester', 'nylon', 'wool', 'silk'}:
            converted.append('made from ' + part)
        else:
            converted.append(part)
    return '; '.join(converted)


def confirmation_transform(message: str, *, semantic: bool) -> str:
    def value(raw: str) -> str:
        return paraphrase_value(raw) if semantic else raw.rstrip('.')

    match = re.fullmatch(r"I'm looking for (.+)\. A key requirement is: (.+)\.", message)
    if match:
        return f'Would you please help me choose {match[1]}? I would like {value(match[2])}.'
    match = re.fullmatch(r"I'm looking for (.+), but I'm still exploring\.", message)
    if match:
        return f'Recommend me {match[1]}. I am just exploring.'
    match = re.fullmatch(r"I'm looking for (.+?)\. (.+)", message)
    if match:
        return f'Please recommend {match[1]}. I prefer {value(match[2])}.'
    prefix = 'For that, what matters is: '
    if message.startswith(prefix):
        return 'I also need ' + value(message.removeprefix(prefix)) + '.'
    prefix = 'Actually, ignore my earlier preference. What I need is: '
    if message.startswith(prefix):
        return 'Please withdraw my previous preference. I would like ' + value(message.removeprefix(prefix)) + '.'
    match = re.fullmatch(r"I don't have a preference for (.+); please use your judgment\.", message)
    if match:
        return f'I do not care about {match[1]}.'
    match = re.fullmatch(r"I don't have an additional preference for (.+)\.", message)
    if match:
        return f'I have nothing else to add for {match[1]}.'
    return message


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--catalog', type=Path, required=True)
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--wording', choices=('development', 'confirmation', 'mixed', 'semantic'), default='development')
    args = parser.parse_args()
    sys.path.insert(0, str(args.source_root.resolve()))
    from scripts import benchmark_finalists as benchmark
    import conversational_search.intent as intent
    if Path(intent.__file__).resolve().parent.parent != args.source_root.resolve():
        raise RuntimeError('incorrect runtime source imported')
    changed = [0, 0]

    def observed_transform(message: str) -> str:
        result = (transform(message) if args.wording == 'development' else
                  confirmation_transform(message, semantic=args.wording == 'semantic'))
        if args.wording == 'mixed' and hashlib.sha256(message.encode()).digest()[0] % 2:
            result = message
        changed[0] += int(result != message)
        changed[1] += 1
        return result

    benchmark.paraphrase = observed_transform
    sys.argv = ['benchmark_finalists', '--catalog', str(args.catalog.resolve()),
                '--dataset', str(args.dataset.resolve()), '--output', str(args.output.resolve()),
                '--wording', 'paraphrase']
    benchmark.main()
    report = json.loads(args.output.read_text())
    report['measurement'].update({
        'wording': f'compositional-{args.wording}-v1',
        'wording_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'transformed_messages': changed[0], 'total_messages': changed[1],
    })
    args.output.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
