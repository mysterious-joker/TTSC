"""Aggregate-only round-five comparison and accuracy-first selection record."""
import argparse
import json
from pathlib import Path
from statistics import fmean
from scripts.compare_finalist_results import compare, utility


def summarize(research):
    root=research/'round5'
    baseline_paths={
        'public':root/'validation-development-v2/public-1-baseline.json',
        'uniform':root/'validation-development-v2/uniform-1-baseline.json',
        'weighted':root/'validation-development-v2/weighted-1-baseline.json',
        'category':research/'round4/development-category-baseline.json',
        'language':research/'round4/validation-development/stress-1-candidate.json',
    }
    baselines={k:json.loads(p.read_text()) for k,p in baseline_paths.items()}
    files={
        'language_top1':{'language':'stress-language_top1'},
        'language_prior':{'language':'stress-language_prior'},
        'first_answer':{'public':'public-first_answer','uniform':'development-first_answer'},
        'joint_uniform':{'public':'public-joint_uniform','uniform':'uniform-joint_uniform'},
        'joint_dual':{'public':'public-joint_dual','uniform':'uniform-joint_dual'},
        'cold_vector':{n:f'v3-semantic-{n}' for n in baselines},
        'joint_verified':{n:f'{n}-joint_verified-v2' for n in baselines},
        'joint_verified_gain':{n:f'{n}-joint_verified_gain' for n in baselines},
    }
    for arm in ('cold_answer','cold_continuation'):
        files[arm]={n:f'{prefix}-{arm}' for n,prefix in [('public','public'),('uniform','development'),
            ('weighted','development-weighted'),('category','development-category'),('language','stress')]}
    report={'family_size':11,'unused_combination_slots':1,'selection_protocol':'ROUND5-PLAN.md close exploration',
            'development_weighted_gain_established_only_if_bound_positive':True,
            'arms':{},'selected_for_fresh_validation':None,
            'confirmation_manifest':json.loads((root/'confirmation-data/manifest.json').read_text())}
    metrics=('sample_count','hit_rate_at_10','mrr','mttc','efficiency','recommended_technical_score','scenario_metrics')
    eligible=[]
    for arm,paths in files.items():
        suites={};raw={}
        for name,stem in paths.items():
            path=root/f'{stem}.json'
            if not path.exists():continue
            candidate=json.loads(path.read_text());baseline=baselines[name];raw[name]=candidate
            c=compare(baseline,candidate,family_size=11,gate='aggregate')
            valid=not candidate['measurement']['exceptions'] and not candidate['measurement']['invalid_outputs'] and not candidate['measurement'].get('research_diagnostics',{}).get('errors',0)
            same=baseline['measurement']['response_sha256']==candidate['measurement']['response_sha256']
            passes=valid and all(x>=-1e-12 for x in c['aggregate_metric_deltas'].values()) and (name!='language' or (same and baseline['sessions']==candidate['sessions']))
            suites[name]={'baseline':{k:baseline[k] for k in metrics},'candidate':{k:candidate[k] for k in metrics},
                          'comparison':c,'component_nonregression_and_contracts':passes,'identical_responses':same,
                          'first_turn_hits':sum(s['first_hit_turn']==1 for s in candidate['sessions']),
                          'diagnostic_measurement':candidate['measurement'],'raw_result':str(path.relative_to(research))}
        passes=len(suites)==5 and all(s['component_nonregression_and_contracts'] for s in suites.values()) and suites['public']['comparison']['development_gate_pass']
        item={'suites':suites,'accuracy_selection_eligible':passes}
        if passes:
            score=fmean(fmean(utility(s) for s in raw[n]['sessions']) for n in ('uniform','weighted','category'))
            item['mean_non_public_development_score']=score
            eligible.append((score,arm))
        report['arms'][arm]=item
    final_arm=report['arms']['joint_verified_gain']['suites']
    report['screening_complete']=(len(final_arm)==5 or any(
        not suite['component_nonregression_and_contracts'] for suite in final_arm.values()))
    if eligible and report['screening_complete']:
        report['selected_for_fresh_validation']=max(eligible)[1]
    report['invalid_implementation_runs']={}
    for stem in ('public-joint_verified','diagnose-verified-40'):
        path=root/f'{stem}.json'
        if path.exists():
            a=json.loads(path.read_text())
            report['invalid_implementation_runs'][stem]={'reason':'proposal execution exceptions; diagnostic mapping corrected separately', 'measurement':a['measurement']}
    for stage in ('development','confirmation'):
        path=root/f'accuracy-{stage}/summary.json'
        if path.exists():report[f'accuracy_{stage}']=json.loads(path.read_text())
    replication=root/'replication-validation/summary.json'
    if replication.exists():
        report['terminal_replication']=json.loads(replication.read_text())
        report['promotion_decision']='reject_round5_candidate_keep_round4_agent'
        report['promotion_reason']='terminal weighted replication regressed MRR and lacked a positive corrected score bound'
    else:
        report['promotion_decision']='pending_terminal_replication'
    active=research/'docs/finals-review/round5-active-verification.json'
    if active.exists():
        report['final_active_verification']=json.loads(active.read_text())
    report['runtime_trials']={}
    for version,directory in [('v1','validation-development'),('v2','validation-development-v2')]:
        path=root/directory/'summary.json'
        if path.exists():
            a=json.loads(path.read_text())
            report['runtime_trials'][version]={'all_gates_pass':a['all_gates_pass'],
                'candidate_source_sha256':a['candidate_source_sha256'],
                'suites':{n:{k:s[k] for k in ('timing','accuracy_gate_pass','all_gates_pass')} for n,s in a['suites'].items()}}
    report['timing_limitations']='Screening processes overlap. V2 weighted baseline timings were noisy. No clean weighted speedup claim.'
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--research-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();report=summarize(a.research_root.resolve());a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'eligible':[k for k,v in report['arms'].items() if v['accuracy_selection_eligible']],
                      'selected_for_fresh_validation':report['selected_for_fresh_validation'],
                      'promotion_decision':report['promotion_decision']}))

if __name__=='__main__':main()
