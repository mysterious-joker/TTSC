"""Evaluate both frozen attribute hypotheses without interleaved tuning."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from scripts.compare_finalist_results import compare


def main():
    root=Path(__file__).resolve().parents[1];work=root.parent/'round7'
    freeze=json.loads((work/'freeze.json').read_text())
    manifest=json.loads((work/'suites/manifest.json').read_text())
    out=work/'confirmation';out.mkdir(exist_ok=False)
    report={'freeze':freeze,'manifest':manifest,'suites':{},'accepted':[]}
    for name in ('public','language','missing_fields'):
        dataset=root/'data/public_set.jsonl' if name=='public' else work/f'suites/{name}.jsonl'
        index_name='attributes-no-details.sqlite' if name=='missing_fields' else 'attributes-v1.sqlite'
        index=work/index_name
        results={}
        for arm in ('baseline','attribute_ties','attribute_counterevidence'):
            for path,digest in freeze['source'].items():
                if hashlib.sha256((root/path).read_bytes()).hexdigest()!=digest:
                    raise RuntimeError('frozen source changed')
            if hashlib.sha256(index.read_bytes()).hexdigest()!=manifest['indexes'][index_name]:
                raise RuntimeError('index changed')
            if name!='public' and hashlib.sha256(dataset.read_bytes()).hexdigest()!=manifest['suites'][name]['sha256']:
                raise RuntimeError('dataset changed')
            dest=out/f'{name}-{arm}.json'
            print(f'START {name} {arm}',flush=True)
            with dest.with_suffix('.log').open('w') as log:
                subprocess.run([sys.executable,'-m','scripts.benchmark_attributes','--variant',arm,
                    '--index',str(index),'--wording','official' if name=='public' else 'semantic',
                    '--dataset',str(dataset),'--output',str(dest)],cwd=root,stdout=log,stderr=subprocess.STDOUT,check=True)
            r=results[arm]=json.loads(dest.read_text())
            print(json.dumps({'suite':name,'arm':arm,**{k:r[k] for k in
                ('hit_rate_at_10','mrr','mttc','recommended_technical_score')},
                'diagnostics':r['measurement'].get('research_diagnostics')}),flush=True)
        suite={'comparisons':{},'metrics':{arm:{k:r[k] for k in
            ('hit_rate_at_10','mrr','mttc','recommended_technical_score','scenario_metrics','measurement')}
            for arm,r in results.items()}}
        for arm in ('attribute_ties','attribute_counterevidence'):
            comparison=compare(results['baseline'],results[arm],family_size=8,gate='aggregate')
            identical=results['baseline']['measurement']['response_sha256']==results[arm]['measurement']['response_sha256']
            diagnostics=results[arm]['measurement'].get('research_diagnostics',{})
            comparison['identical_responses']=identical
            comparison['accuracy_gate_pass']=(identical if name=='public' else comparison['development_gate_pass']) and not diagnostics.get('index_unavailable',0)
            suite['comparisons'][arm]=comparison
        report['suites'][name]=suite
        report['accepted']=[arm for arm in ('attribute_ties','attribute_counterevidence')
                           if len(report['suites'])==3 and all(x['comparisons'][arm]['accuracy_gate_pass'] for x in report['suites'].values())]
        (out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
        print('GATES '+name+' '+json.dumps({a:c['accuracy_gate_pass'] for a,c in suite['comparisons'].items()}),flush=True)
    if not report['accepted']:
        print('Neither candidate passed accuracy; no timing promotion gate or runtime activation.',flush=True)


if __name__=='__main__':main()
