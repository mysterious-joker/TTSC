"""Run the opt-in attribute experiment with unchanged official scoring."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from scripts import benchmark_finalists as runner
from scripts.benchmark_paraphrases import confirmation_transform, transform


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--variant', choices=('baseline', 'attribute_ties', 'attribute_counterevidence'), required=True)
    parser.add_argument('--index', type=Path, required=True)
    parser.add_argument('--wording', choices=('official', 'development', 'confirmation', 'mixed', 'semantic'), default='official')
    args, remaining = parser.parse_known_args()
    changed = [0, 0]

    def language(message):
        modified = transform(message) if args.wording == 'development' else confirmation_transform(message, semantic=args.wording == 'semantic')
        if args.wording == 'mixed' and hashlib.sha256(message.encode()).digest()[0] % 2:
            modified = message
        changed[0] += int(modified != message)
        changed[1] += 1
        return modified

    if args.variant != 'baseline':
        from scripts.attribute_candidate import AttributeAgent
        runner.local_agent = lambda arm, catalog: AttributeAgent(catalog, args.index,
            counterevidence_only=args.variant == 'attribute_counterevidence')
    if args.wording != 'official':
        runner.paraphrase = language
    sys.argv = ['benchmark_finalists', *remaining, '--wording', 'official' if args.wording == 'official' else 'paraphrase']
    runner.main()
    path = Path(remaining[remaining.index('--output') + 1])
    result = json.loads(path.read_text())
    result['measurement'].update({'variant': args.variant, 'wording': args.wording,
        'index_sha256': hashlib.sha256(args.index.read_bytes()).hexdigest(),
        'changed_messages': changed[0], 'total_messages': changed[1]})
    path.write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
