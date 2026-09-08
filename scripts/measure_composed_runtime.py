"""Sequential public timing pairs after round-eight accuracy validation."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from scripts.benchmark_runtime_pairs import summarize


def main():
    root = Path(__file__).resolve().parents[1]
    work = root.parent / 'round8'
    if not json.loads((work / 'confirmation/summary.json').read_text())['accuracy_gate_pass']:
        raise RuntimeError('accuracy gate must pass')
    freeze = json.loads((work / 'freeze.json').read_text())
    out = work / 'timing'
    out.mkdir(exist_ok=False)
    pairs = []
    for repeat in range(3):
        pair = {}
        for side in (('baseline', 'candidate') if repeat % 2 == 0 else ('candidate', 'baseline')):
            for rel, digest in freeze['source'].items():
                if hashlib.sha256((root / rel).read_bytes()).hexdigest() != digest:
                    raise RuntimeError('frozen source changed')
            source = work / 'baseline' if side == 'baseline' else root
            dest = out / f'public-{repeat}-{side}.json'
            print(f'START timing {repeat + 1} {side}', flush=True)
            with dest.with_suffix('.log').open('w') as log:
                subprocess.run([sys.executable, '-m', 'scripts.benchmark_finalists',
                    '--catalog', str(root / 'data/catalog.jsonl'),
                    '--dataset', str(root / 'data/public_set.jsonl'), '--output', str(dest)],
                    cwd=source, stdout=log, stderr=subprocess.STDOUT, check=True)
            pair[side] = json.loads(dest.read_text())
        pairs.append((pair['baseline'], pair['candidate']))
    report = summarize(pairs, alpha=.05, require_identical=True)
    (out / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
