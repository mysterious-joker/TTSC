"""Evaluate the frozen round-eight candidate without changing source."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from scripts.compare_finalist_results import compare


def main():
    root = Path(__file__).resolve().parents[1]
    work = root.parent / 'round8'
    freeze = json.loads((work / 'freeze.json').read_text())
    manifest = json.loads((work / 'suites/manifest.json').read_text())
    out = work / 'confirmation'
    out.mkdir(exist_ok=False)
    report = {'freeze': freeze, 'manifest': manifest, 'suites': {}, 'accuracy_gate_pass': False}
    for name in ('public', 'official', 'composed', 'compatibility'):
        dataset = (root / 'data/public_set.jsonl' if name == 'public' else
                   root.parent / 'round7/suites/language.jsonl' if name == 'compatibility' else
                   work / f'suites/{name}.jsonl')
        results = {}
        for side, source in (('baseline', work / 'baseline'), ('candidate', root)):
            for rel, digest in freeze['source'].items():
                if hashlib.sha256((root / rel).read_bytes()).hexdigest() != digest:
                    raise RuntimeError('frozen source changed')
            if hashlib.sha256(dataset.read_bytes()).hexdigest() != manifest['suites'][name]['sha256']:
                raise RuntimeError('frozen dataset changed')
            dest = out / f'{name}-{side}.json'
            command = [sys.executable, '-m', 'scripts.benchmark_finalists']
            if name in {'composed', 'compatibility'}:
                runner = 'benchmark_composed_requests.py' if name == 'composed' else 'benchmark_paraphrases.py'
                command = [sys.executable, str(root / 'scripts' / runner), '--source-root', str(source)]
                if name == 'compatibility':
                    command += ['--wording', 'semantic']
            command += ['--catalog', str(root / 'data/catalog.jsonl'), '--dataset', str(dataset), '--output', str(dest)]
            print(f'START {name} {side}', flush=True)
            with dest.with_suffix('.log').open('w') as log:
                subprocess.run(command, cwd=source, stdout=log, stderr=subprocess.STDOUT, check=True)
            r = results[side] = json.loads(dest.read_text())
            print(json.dumps({'suite': name, 'side': side, **{k:r[k] for k in
                ('hit_rate_at_10', 'mrr', 'mttc', 'recommended_technical_score')}}), flush=True)
        comparison = compare(results['baseline'], results['candidate'], family_size=4, gate='aggregate')
        identical = results['baseline']['measurement']['response_sha256'] == results['candidate']['measurement']['response_sha256']
        clean = not any(r['measurement']['exceptions'] or r['measurement']['invalid_outputs'] for r in results.values())
        passed = (comparison['development_gate_pass'] if name == 'composed' else
                  all(d >= -1e-12 for d in comparison['aggregate_metric_deltas'].values()) if name == 'compatibility' else identical) and clean
        report['suites'][name] = {'gate_pass': passed, 'identical_responses': identical,
            'comparison': comparison, 'metrics': {side:{k:r[k] for k in
            ('hit_rate_at_10','mrr','mttc','recommended_technical_score','scenario_metrics','measurement')}
            for side,r in results.items()}}
        report['accuracy_gate_pass'] = len(report['suites']) == 4 and all(x['gate_pass'] for x in report['suites'].values())
        (out / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
        print(f'GATE {name}: {passed}', flush=True)


if __name__ == '__main__':
    main()
