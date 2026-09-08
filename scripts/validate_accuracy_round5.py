"""Freeze and validate accuracy first; runtime is reported for the next stage."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from scripts.compare_finalist_results import compare
from scripts.validate_finals_round4 import fingerprint


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--research-root',type=Path,required=True)
    p.add_argument('--stage',choices=('development','confirmation'),required=True)
    p.add_argument('--family-size',type=int,required=True)
    args=p.parse_args()
    research=args.research_root.resolve(); candidate=Path(__file__).resolve().parents[1]
    baseline=research/'round5/baseline'; output=research/f'round5/accuracy-{args.stage}'
    if output.exists(): raise ValueError('refusing to overwrite a validation study')
    if args.stage=='development':
        specs=(('public',candidate/'data/public_set.jsonl','official',True),
               ('weighted',research/'round4/suites/development-weighted.jsonl','official',False),
               ('uniform',research/'development.jsonl','official',False),
               ('category',research/'round4/suites/development-category.jsonl','official',False),
               ('language',research/'language-stress.jsonl','paraphrase',False))
    else:
        previous=json.loads((research/'round5/accuracy-development/summary.json').read_text())
        if len(previous['suites'])!=5 or not previous['all_gates_pass']:
            raise ValueError('all development accuracy gates must pass')
        if args.family_size!=previous['family_size']: raise ValueError('family size changed')
        for side,root in [('candidate',candidate),('baseline',baseline)]:
            if fingerprint(root)!=previous[f'{side}_source_sha256']: raise ValueError('source changed before confirmation')
        manifest=json.loads((research/'round5/confirmation-data/manifest.json').read_text())
        specs=tuple((n,research/f'round5/confirmation-data/{n}.jsonl','paraphrase' if n=='language' else 'official',n=='weighted') for n in ('uniform','weighted','language'))
        for n,path,_,_ in specs:
            if hashlib.sha256(path.read_bytes()).hexdigest()!=manifest['suites'][n]['sha256']:
                raise ValueError('confirmation data changed')
    report={'stage':args.stage,'priority':'accuracy_first','family_size':args.family_size,
            'selection_protocol':'round5-plan-close-exploration-before-confirmation',
            'frozen_at_utc':datetime.now(timezone.utc).isoformat(),
            'candidate_source_sha256':fingerprint(candidate),'baseline_source_sha256':fingerprint(baseline),
            'suite_hashes':{n:hashlib.sha256(path.read_bytes()).hexdigest() for n,path,_,_ in specs},
            'suites':{},'all_gates_pass':False}
    output.mkdir()
    (output/'freeze.json').write_text(json.dumps(report,indent=2)+'\n')
    for name,data,wording,gain in specs:
        pair={}
        for side,root in [('baseline',baseline),('candidate',candidate)]:
            if fingerprint(root)!=report[f'{side}_source_sha256']: raise ValueError('frozen source changed')
            dest=output/f'{name}-{side}.json'
            print(f'START {args.stage} {name} {side}',flush=True)
            run=subprocess.run([sys.executable,'-m','scripts.benchmark_finalists','--dataset',str(data),'--wording',wording,'--output',str(dest)],cwd=root,capture_output=True,text=True)
            (output/f'{name}-{side}.log').write_text(run.stdout+run.stderr)
            if run.returncode: raise RuntimeError(run.stderr[-2000:])
            pair[side]=json.loads(dest.read_text())
        a,b=pair['baseline'],pair['candidate']; comparison=compare(a,b,family_size=args.family_size,gate='aggregate')
        valid=all(not r['measurement']['exceptions'] and not r['measurement']['invalid_outputs'] for r in (a,b))
        stable_language=wording=='official' or (a['sessions']==b['sessions'] and a['measurement']['response_sha256']==b['measurement']['response_sha256'])
        passed=valid and stable_language and all(x>=-1e-12 for x in comparison['aggregate_metric_deltas'].values()) and (not gain or comparison['development_gate_pass'])
        report['suites'][name]={'comparison':comparison,'requires_significant_gain':gain,'all_gates_pass':passed,
            'identical_language_required':wording!='official','identical_responses':a['measurement']['response_sha256']==b['measurement']['response_sha256'],
            'metrics':{side:{k:r[k] for k in ('sample_count','hit_rate_at_10','mrr','mttc','efficiency','recommended_technical_score','scenario_metrics')} for side,r in pair.items()},
            'diagnostic_runtime':{side:r['measurement'] for side,r in pair.items()}}
        report['all_gates_pass']=len(report['suites'])==len(specs) and all(s['all_gates_pass'] for s in report['suites'].values())
        (output/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({'suite':name,'passed':passed,'score':b['recommended_technical_score'],'comparison':comparison}),flush=True)
        if not passed: raise SystemExit('accuracy gate failed; stop before further validation')

if __name__=='__main__':main()
