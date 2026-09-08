"""Runtime validation after independent accuracy validation of fixed source."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import statistics
import subprocess
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--research-root',type=Path,required=True)
    p.add_argument('--candidate-root',type=Path,required=True)
    args=p.parse_args();research=args.research_root.resolve();candidate=args.candidate_root.resolve()
    sys.path.insert(0,str(candidate))
    from scripts.benchmark_runtime_pairs import summarize
    from scripts.validate_finals_round4 import fingerprint
    root=research/'round5';baseline=root/'baseline'
    accuracy=json.loads((root/'replication-validation/summary.json').read_text())
    if not accuracy['all_gates_pass']:raise ValueError('terminal accuracy replication must pass first')
    expected=accuracy['manifest']['candidate_source_sha256'];expected_baseline=accuracy['manifest']['baseline_source_sha256']
    if fingerprint(candidate)!=expected or fingerprint(baseline)!=expected_baseline:
        raise ValueError('accuracy-validated source changed')
    specs=[
        ('public',candidate/'data/public_set.jsonl','official',root/'accuracy-development','public'),
        ('language-development',research/'language-stress.jsonl','paraphrase',root/'accuracy-development','language'),
        ('uniform-development',research/'development.jsonl','official',root/'accuracy-development','uniform'),
        ('weighted-development',research/'round4/suites/development-weighted.jsonl','official',root/'accuracy-development','weighted'),
        ('category-development',research/'round4/suites/development-category.jsonl','official',root/'accuracy-development','category'),
        ('uniform-confirmation',root/'confirmation-data/uniform.jsonl','official',root/'accuracy-confirmation','uniform'),
        ('weighted-confirmation',root/'confirmation-data/weighted.jsonl','official',root/'accuracy-confirmation','weighted'),
        ('weighted-replication',root/'replication-data/weighted.jsonl','official',root/'replication-validation','weighted'),
        ('language-confirmation',root/'confirmation-data/language.jsonl','paraphrase',root/'replication-validation','language'),
    ]
    output=root/'runtime-validated-v3'
    if output.exists():raise ValueError('never overwrite a runtime study')
    output.mkdir();driver_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report={'frozen_at_utc':datetime.now(timezone.utc).isoformat(),'candidate_source_sha256':expected,
            'baseline_source_sha256':expected_baseline,'driver_sha256':driver_sha,
            'protocol':'Retain every accuracy pair as B/C repetition 1, then run isolated C/B and B/C pairs.',
            'reference_limitations':'Development public/weighted first pairs overlapped earlier research. All first pairs are retained; none selected by runtime.',
            'cpu_timing_repetitions':2,'elapsed_timing_repetitions':3,'suites':{},'all_gates_pass':False}
    (output/'freeze.json').write_text(json.dumps(report,indent=2)+'\n')
    for name,data,wording,reference,prefix in specs:
        first=tuple(json.loads((reference/f'{prefix}-{side}.json').read_text()) for side in ('baseline','candidate'))
        dataset_sha=hashlib.sha256(data.read_bytes()).hexdigest()
        if any(r['measurement']['dataset_sha256']!=dataset_sha for r in first):raise ValueError('reference data mismatch')
        pairs=[first]
        for repeat,sides in ((2,('candidate','baseline')),(3,('baseline','candidate'))):
            pair={}
            for side in sides:
                cwd=baseline if side=='baseline' else candidate
                if fingerprint(cwd)!=(expected_baseline if side=='baseline' else expected):raise ValueError('source changed during runtime validation')
                if hashlib.sha256(Path(__file__).read_bytes()).hexdigest()!=driver_sha:raise ValueError('runtime driver changed')
                dest=output/f'{name}-{repeat}-{side}.json'
                print(f'START runtime {name} pair {repeat} {side}',flush=True)
                run=subprocess.run(['/usr/bin/time','-p',sys.executable,'-m','scripts.benchmark_finalists',
                    '--dataset',str(data),'--wording',wording,'--output',str(dest)],cwd=cwd,capture_output=True,text=True)
                (output/f'{name}-{repeat}-{side}.log').write_text(run.stdout+run.stderr)
                if run.returncode:raise RuntimeError(run.stderr[-2000:])
                result=json.loads(dest.read_text())
                clocks={k:float(v) for k,v in re.findall(r'^(real|user|sys)\s+(\d+(?:\.\d+)?)\s*$',run.stderr,re.M)}
                if set(clocks)!={'real','user','sys'}:raise ValueError('OS CPU timing missing')
                result['measurement']['process_cpu_seconds']=clocks['user']+clocks['sys']
                result['measurement']['process_wall_seconds']=clocks['real']
                dest.write_text(json.dumps(result,indent=2)+'\n');pair[side]=result
            pairs.append((pair['baseline'],pair['candidate']))
        stable=all(first[i]['sessions']==pair[i]['sessions'] and first[i]['measurement']['response_sha256']==pair[i]['measurement']['response_sha256'] for pair in pairs for i in (0,1))
        timing=summarize(pairs,alpha=.05/len(specs),require_identical=wording!='official')
        cpu={side:statistics.median(pair[i]['measurement']['process_cpu_seconds'] for pair in pairs[1:]) for i,side in enumerate(('baseline','candidate'))}
        cpu_pass=cpu['candidate']<=cpu['baseline']
        passed=stable and timing['aggregate_runtime_nonregression'] and cpu_pass
        report['suites'][name]={'accuracy_reference':str(reference.relative_to(research)),
            'accuracy_reference_verified':stable,'timing':timing,'process_cpu_seconds_medians':cpu,
            'process_cpu_nonregression':cpu_pass,'all_gates_pass':passed,
            'speed_gain_supported':passed and timing['one_sided_saving_lower_bound_ms']>1e-12}
        report['all_gates_pass']=len(report['suites'])==len(specs) and all(s['all_gates_pass'] for s in report['suites'].values())
        (output/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({'suite':name,'passed':passed,'speedup':timing['median_end_to_end_speedup'],'cpu_medians':cpu}),flush=True)
        if not passed:raise SystemExit('runtime gate failed; keep accuracy result separate')

if __name__=='__main__':main()
