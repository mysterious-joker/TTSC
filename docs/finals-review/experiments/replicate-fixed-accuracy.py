"""One terminal independent replication of the unchanged round-five candidate."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--research-root',type=Path,required=True)
    p.add_argument('--candidate-root',type=Path,required=True)
    p.add_argument('--stage',choices=('generate','evaluate'),required=True)
    args=p.parse_args();research=args.research_root.resolve();candidate=args.candidate_root.resolve()
    sys.path.insert(0,str(candidate))
    from evaluator.local_evaluator import load_jsonl
    from scripts.generate_distribution_suites import sample_targets
    from scripts.validate_finals_round4 import fingerprint
    from scripts.compare_finalist_results import compare
    baseline=research/'round5/baseline'
    first=json.loads((research/'round5/accuracy-confirmation/summary.json').read_text())
    expected='65b6693b3a199910520788250e28fbd4266e5f96e9eb8ddffbeb55dbb00756e3'
    if first['candidate_source_sha256']!=expected or fingerprint(candidate)!=expected:
        raise ValueError('candidate changed; this is not a fixed-candidate replication')
    if fingerprint(baseline)!=first['baseline_source_sha256']:
        raise ValueError('baseline changed')
    if set(first['suites'])!={'uniform','weighted'}:
        raise ValueError('unexpected original confirmation state')
    for name,suite in first['suites'].items():
        if any(x < -1e-12 for x in suite['comparison']['aggregate_metric_deltas'].values()):
            raise ValueError('replication cannot rescue a first-study metric regression')
        if any(m['exceptions'] or m['invalid_outputs'] for m in suite['diagnostic_runtime'].values()):
            raise ValueError('first study was invalid')
    if first['suites']['weighted']['comparison']['rejection_reasons']!=['bootstrap_lower_bound_not_positive']:
        raise ValueError('first weighted study was not an inconclusive significance result')
    language=research/'round5/confirmation-data/language.jsonl'
    old_manifest=json.loads((language.parent/'manifest.json').read_text())
    if hashlib.sha256(language.read_bytes()).hexdigest()!=old_manifest['suites']['language']['sha256']:
        raise ValueError('reserved language data changed')
    if list((research/'round5/accuracy-confirmation').glob('language-*.json')):
        raise ValueError('reserved language outcomes were already opened')
    data_root=research/'round5/replication-data'
    if args.stage=='generate':
        if data_root.exists():raise ValueError('never overwrite replication data')
        paths=[candidate/'data/public_set.jsonl',research/'development.jsonl',research/'confirmation.jsonl',
               *sorted((research/'round4/suites').glob('*.jsonl')),
               *sorted((research/'round5/confirmation-data').glob('*.jsonl'))]
        excluded={r['ground_truth']['parent_asin'] for path in paths for r in load_jsonl(path)}
        if len(excluded)!=12200:raise ValueError('unexpected target exclusion count')
        products={r['parent_asin']:r for r in load_jsonl(candidate/'data/catalog.jsonl') if r['parent_asin'] not in excluded}
        profiles=[r['user_profile'] for r in load_jsonl(candidate/'data/public_set.jsonl')]
        rng=random.Random(202609086);count=6400;targets=sample_targets(products,count,'weighted',rng)
        scenarios=[s for s,w in (('buying',8),('browsing',8),('intent_override',3),('boundary',1)) for _ in range(count*w//20)]
        rng.shuffle(scenarios);rng.shuffle(targets)
        rows=[{'sample_id':f'round5_replication_{i:04d}','scenario_type':s,'user_profile':rng.choice(profiles),
               'ground_truth':{'parent_asin':a}} for i,(a,s) in enumerate(zip(targets,scenarios))]
        payload=''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows).encode()
        manifest={'seed':202609086,'count':count,'distribution':'sqrt_review_weighted_without_replacement',
                  'excluded_targets':len(excluded),'sha256':hashlib.sha256(payload).hexdigest(),
                  'candidate_source_sha256':expected,'baseline_source_sha256':fingerprint(baseline),
                  'catalog_sha256':hashlib.sha256((candidate/'data/catalog.jsonl').read_bytes()).hexdigest(),
                  'language_sha256':old_manifest['suites']['language']['sha256'],
                  'generated_at_utc':datetime.now(timezone.utc).isoformat(),'family_size':22,
                  'driver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
        data_root.mkdir();(data_root/'weighted.jsonl').write_bytes(payload)
        (data_root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        print(json.dumps(manifest),flush=True);return
    manifest=json.loads((data_root/'manifest.json').read_text())
    weighted=data_root/'weighted.jsonl'
    if hashlib.sha256(weighted.read_bytes()).hexdigest()!=manifest['sha256']:
        raise ValueError('replication data changed')
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest()!=manifest['driver_sha256']:
        raise ValueError('replication driver changed after generation')
    if hashlib.sha256((candidate/'data/catalog.jsonl').read_bytes()).hexdigest()!=manifest['catalog_sha256']:
        raise ValueError('catalog changed')
    output=research/'round5/replication-validation'
    if output.exists():raise ValueError('never overwrite replication results')
    output.mkdir();report={'manifest':manifest,'frozen_at_utc':datetime.now(timezone.utc).isoformat(),
        'suites':{},'all_gates_pass':False,'original_confirmation_gate_pass':False}
    (output/'freeze.json').write_text(json.dumps(report,indent=2)+'\n')
    for name,dataset,wording in (('weighted',weighted,'official'),('language',language,'paraphrase')):
        pair={}
        for side,root in (('baseline',baseline),('candidate',candidate)):
            if fingerprint(root)!=manifest[f'{side}_source_sha256']:raise ValueError('frozen source changed')
            dest=output/f'{name}-{side}.json';print(f'START terminal replication {name} {side}',flush=True)
            run=subprocess.run([sys.executable,'-m','scripts.benchmark_finalists','--dataset',str(dataset),
                '--wording',wording,'--output',str(dest)],cwd=root,capture_output=True,text=True)
            (output/f'{name}-{side}.log').write_text(run.stdout+run.stderr)
            if run.returncode:raise RuntimeError(run.stderr[-2000:])
            pair[side]=json.loads(dest.read_text())
            print(json.dumps({'suite':name,'side':side,'score':pair[side]['recommended_technical_score']}),flush=True)
        a,b=pair['baseline'],pair['candidate'];comparison=compare(a,b,family_size=22,gate='aggregate')
        valid=all(not r['measurement']['exceptions'] and not r['measurement']['invalid_outputs'] for r in pair.values())
        same=a['sessions']==b['sessions'] and a['measurement']['response_sha256']==b['measurement']['response_sha256']
        nonreg=all(x>=-1e-12 for x in comparison['aggregate_metric_deltas'].values())
        passed=valid and nonreg and (comparison['development_gate_pass'] if name=='weighted' else same)
        report['suites'][name]={'comparison':comparison,'all_gates_pass':passed,'identical_sessions_and_responses':same,
            'metrics':{side:{k:r[k] for k in ('sample_count','hit_rate_at_10','mrr','mttc','efficiency',
                'recommended_technical_score','scenario_metrics')} for side,r in pair.items()},
            'diagnostic_runtime':{side:r['measurement'] for side,r in pair.items()}}
        report['all_gates_pass']=len(report['suites'])==2 and all(s['all_gates_pass'] for s in report['suites'].values())
        (output/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({'suite':name,'passed':passed,'comparison':comparison}),flush=True)
        if not passed:raise SystemExit('terminal replication failed; reject candidate')

if __name__=='__main__':main()
