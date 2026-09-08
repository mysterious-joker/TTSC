"""Validate the frozen language repair against a frozen source snapshot."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

from scripts.compare_finalist_results import compare


def runtime_hashes(root: Path) -> dict[str, str]:
    files = [root / 'agent.py', *root.glob('starter/**/*.py'),
             *root.glob('conversational_search/**/*.py')]
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(files)}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    work = root.parent / 'round6'
    freeze = json.loads((work / 'runtime-freeze.json').read_text())
    manifest = json.loads((work / 'suites/manifest.json').read_text())
    out = work / 'confirmation'
    out.mkdir(exist_ok=False)
    baseline = work / 'baseline'
    baseline_hashes = runtime_hashes(baseline)
    report = {'source_freeze': freeze, 'suite_manifest': manifest,
              'suites': {}, 'all_gates_pass': False}
    for name in ('official', 'confirmation', 'mixed', 'semantic'):
        results = {}
        dataset = work / f'suites/{name}.jsonl'
        for side, source in (('baseline', baseline), ('candidate', root)):
            if runtime_hashes(root) != freeze['source'] or runtime_hashes(baseline) != baseline_hashes:
                raise RuntimeError('runtime changed after freeze')
            if hashlib.sha256(dataset.read_bytes()).hexdigest() != manifest['suites'][name]['sha256']:
                raise RuntimeError('dataset changed after freeze')
            runner = root / 'scripts/benchmark_paraphrases.py'
            if hashlib.sha256(runner.read_bytes()).hexdigest() != manifest['wording_source_sha256']:
                raise RuntimeError('wording changed after freeze')
            dest = out / f'{name}-{side}.json'
            if name == 'official':
                command = [sys.executable, '-m', 'scripts.benchmark_finalists',
                           '--catalog', str(root / 'data/catalog.jsonl'),
                           '--dataset', str(dataset), '--output', str(dest)]
            else:
                command = [sys.executable, str(runner), '--source-root', str(source),
                           '--catalog', str(root / 'data/catalog.jsonl'),
                           '--dataset', str(dataset), '--wording', name, '--output', str(dest)]
            print(f'START {name} {side}', flush=True)
            with (out / f'{name}-{side}.log').open('w') as log:
                subprocess.run(command, cwd=source, stdout=log, stderr=subprocess.STDOUT, check=True)
            r = results[side] = json.loads(dest.read_text())
            print(json.dumps({'suite': name, 'side': side, **{k:r[k] for k in
                ('hit_rate_at_10','mrr','mttc','recommended_technical_score')}}), flush=True)
        comparison = compare(results['baseline'], results['candidate'], family_size=8, gate='aggregate')
        identical = results['baseline']['measurement']['response_sha256'] == results['candidate']['measurement']['response_sha256']
        errors = any(r['measurement']['exceptions'] or r['measurement']['invalid_outputs'] for r in results.values())
        passed = (identical if name == 'official' else comparison['development_gate_pass']) and not errors
        report['suites'][name] = {
            'gate_pass': passed, 'identical_responses': identical, 'comparison': comparison,
            'metrics': {side: {k:r[k] for k in ('hit_rate_at_10','mrr','mttc',
                       'recommended_technical_score','scenario_metrics','measurement')}
                       for side,r in results.items()},
        }
        report['all_gates_pass'] = all(x['gate_pass'] for x in report['suites'].values())
        (out / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
        print(f'GATE {name}: {passed}', flush=True)
    if runtime_hashes(root) != freeze['source']:
        raise RuntimeError('runtime changed during final evaluation')
    if not report['all_gates_pass']:
        raise SystemExit('Fresh validation failed; do not promote this candidate.')


if __name__ == '__main__':
    main()
