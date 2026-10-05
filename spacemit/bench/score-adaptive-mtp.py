#!/usr/bin/env python3
"""Verify saved adaptive-MTP evidence, score paired answers and apply pilot gates."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics

def load(name,root):
    spec=importlib.util.spec_from_file_location(name,root/(name+'.py'))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def quality_eligible(record,runner):
    return all(runner.pilot.audit_result(record,record['request'],record['prompt_tokens']).values())

def score(root,key_file):
    receipt=json.loads((root/'collection-receipt.json').read_text())
    manifest=json.loads((root/'run.json').read_text())
    infrastructure=manifest.get('screen')=='infrastructure'
    for name,digest in receipt['files_sha256'].items():
        if Path(name).name!=name or hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('collected artifact changed')
    for name,digest in manifest['code_sha256'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('staged code changed')
    runner=load('adaptive-mtp-test',root); checks=runner.checks
    gate_helper=load('score-mtp-quality',root);judge=load('judge-shared-document-cache',root)
    key=key_file.read_text().strip()
    if not key or '\n' in key:raise ValueError('judge key must be one line')
    url=judge.endpoint(manifest['judge']['base_url'],False);model=manifest['judge']['model']
    configs=json.loads((root/'server-configs.json').read_text()) if (root/'server-configs.json').exists() else {}
    for config in configs.values():
        argv=config['command']; env=config['runtime']
        if env.get('SPINE_SPEC_RS')!='0' or env.get('SPINE_K1_GEMM_ROUTE')!='0':raise ValueError('runtime changed')
        for flag,value in [('-t','4'),('-c','6144'),('-b','32'),('-ub','32'),('-ctk','f16'),('-ctv','f16'),('-ngl','0')]:
            if argv[argv.index(flag)+1]!=value:raise ValueError('workload changed')
        if ('--spec-type' in argv)!=(config['arm']!='direct'):raise ValueError('server arm changed')
    summary={'status':'scoring','generation_exit':(root/'exit-status').read_text().strip(),
        'screen':manifest.get('screen','quality'),
        'verified_artifacts':len(receipt['files_sha256']),'models':{},'candidate_qualified':False,
        'limitations':'Three repetitions of three tasks/model, one slot, one two-order cloud judge. No long-context/concurrency or statistical-equivalence claim.'}
    generation=json.loads((root/'summary.json').read_text())
    for size in ('2B','4B'):
        (root/'scoring-phase').write_text('score '+size+'\n')
        raw_file=root/(size+'-responses.json')
        if not raw_file.exists():
            summary['models'][size]={'status':'timing skipped or incomplete',
                'generation':generation.get('models',{}).get(size,{}),'qualified':False}
            continue
        raw=json.loads(raw_file.read_text());tasks={c['case_id']:c for c in json.loads((root/(size+'-cases.json')).read_text())}
        by_pair={}
        for record in raw:
            case=tasks[record['case_id']];payload=record['request']
            if payload['messages']!=[{'role':'system','content':case['system']},{'role':'user','content':case['user']}]:
                raise ValueError('full task input changed')
            if payload['max_tokens']!=case['max_tokens']:raise ValueError('task output budget changed')
            if hashlib.sha256(record['answer'].encode()).hexdigest()!=record['answer_sha256']:raise ValueError('answer hash changed')
            if hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest()!=record['request_sha256']:
                raise ValueError('request hash changed')
            if not all(runner.timing_audit(record,payload,record['prompt_tokens'],infrastructure).values()):
                raise ValueError('invalid timing generation')
            record['quality_eligible']=quality_eligible(record,runner)
            record['checked_facts']=checks.fact_check(case,record['answer'])
            if case['kind']=='code':record['checked_code']=checks.check_code(case['case_id'],record['answer'])
            label=record['server_label']
            if label not in configs or configs[label]['arm']!=record['arm']:raise ValueError('arm/configuration differs')
            tele=record['timings'].get('spine_mtp',{})
            if record['arm']=='direct':
                if record['timings'].get('draft_n',0):raise ValueError('standalone direct drafted')
            else:
                wanted=record['arm']=='adaptive' and case['kind']=='code'
                if tele.get('initially_enabled') is not wanted:raise ValueError('ineffective per-request policy')
                if not wanted and record['timings'].get('draft_n',0):raise ValueError('disabled arm drafted')
                if wanted and tele.get('cycles',0)<=0:raise ValueError('adaptive code never drafted')
            by_pair.setdefault((record['repeat'],record['case_id']),{})[record['arm']]=record
        previous={}
        grades=root/(size+'-judge.jsonl')
        if grades.exists():previous={r['case_id']:r for r in map(json.loads,grades.read_text().splitlines())}
        comparisons=[];scores=[]
        for (repeat,case_id),arms in sorted(by_pair.items()):
            if set(arms)!={'direct','loaded_off','adaptive'}:continue
            d,a,o=arms['direct'],arms['adaptive'],arms['loaded_off'];case=tasks[case_id]
            normalized=[{k:v for k,v in r['request'].items() if k!='spine_mtp'} for r in arms.values()]
            if not all(n==normalized[0] for n in normalized) or len({r['prompt_tokens'] for r in arms.values()})!=1:
                raise ValueError('paired inputs differ')
            regression=False
            for r in (a,o):
                for field in ('facts','citations'):
                    regression|=gate_helper.regression(d['checked_facts'][field],r['checked_facts'][field])
                if case['kind']=='code':regression|=d['checked_code']['pass'] and not r['checked_code']['pass']
            pair={'repeat':repeat,'case_id':case_id,'deterministic_regression':bool(regression),
                'quality_eligible':{arm:r['quality_eligible'] for arm,r in arms.items()},
                'finish_reason':{arm:r['finish_reason'] for arm,r in arms.items()},
                'wall_s':{arm:r['wall_s'] for arm,r in arms.items()},
                'ttft_s':{arm:r['ttft_s'] for arm,r in arms.items()},
                'output_tokens':{arm:r['usage']['completion_tokens'] for arm,r in arms.items()},
                'decode_tps':{arm:r['timings']['predicted_per_second'] for arm,r in arms.items()},
                'adaptive_policy':a['timings']['spine_mtp'],
                'facts':{arm:r['checked_facts'] for arm,r in arms.items()},
                'code_tests':{arm:r.get('checked_code') for arm,r in arms.items()}}
            comparisons.append(pair)
            gate_helper.fast_write(root/(size+'-comparisons.json'),comparisons)
            if not all(r['quality_eligible'] for r in arms.values()):continue
            item={'case_id':f'{size}-r{repeat}-{case_id}','question':case['question'],'evidence':case['evidence'],
                'required_facts':case['required_facts'],'cold_answer':d['answer'],'warm_answer':a['answer']}
            fingerprint=hashlib.sha256(json.dumps(item,sort_keys=True).encode()).hexdigest()
            if item['case_id'] in previous:
                rating=previous[item['case_id']]
                if rating['input_sha256']!=fingerprint or rating['judge_model']!=model or len(rating['passes'])!=2:
                    raise ValueError('judge resume evidence changed')
            else:
                rating=judge.grade_case(item,url,model,key,120,2,4096,True)
                with grades.open('a') as f:f.write(json.dumps(rating,ensure_ascii=False)+'\n')
            scores.append(rating)
            gate_helper.fast_write(root/(size+'-comparisons.json'),comparisons)
        gate=gate_helper.judge_gate(scores,comparisons,required=9)
        timing={}
        for case_id in tasks:
            selected=[p for p in comparisons if p['case_id']==case_id]
            timing[case_id]={}
            for arm in ('loaded_off','adaptive'):
                gains=[100*(1-p['wall_s'][arm]/p['wall_s']['direct']) for p in selected]
                decode_gains=[100*(p['decode_tps'][arm]/p['decode_tps']['direct']-1) for p in selected]
                timing[case_id][arm]={'paired_time_reduction_pct':gains,
                    'median_time_reduction_pct':statistics.median(gains) if gains else None,
                    'paired_decode_throughput_gain_pct':decode_gains,
                    'median_decode_throughput_gain_pct':statistics.median(decode_gains) if decode_gains else None,
                    'same_output_token_count':[p['output_tokens'][arm]==p['output_tokens']['direct'] for p in selected]}
        code_metric='median_decode_throughput_gain_pct' if infrastructure else 'median_time_reduction_pct'
        timing_pass=len(comparisons)==9 and timing['unicode_offsets']['adaptive'][code_metric]>3 and all(
            timing[c]['adaptive']['median_time_reduction_pct']>=-3 for c in ('chinese_policy','routes'))
        absolute=len(comparisons)==9 and all(all(p['quality_eligible'].values()) and all(p['facts']['adaptive']['facts']) and
            (p['case_id']!='unicode_offsets' or p['code_tests']['adaptive']['pass']) for p in comparisons)
        model_generation=generation.get('models',{}).get(size,{})
        summary['models'][size]={'relative_quality_gate':gate,'timing_gate':timing_pass,'absolute_checks':absolute,
            'infrastructure_timing_available':len(comparisons)==9,
            'code_timing_metric':code_metric,'quality_pairs':len(scores),
            'generation':model_generation,
            'qualified':model_generation.get('status')=='generation completed' and gate['pass'] and timing_pass and absolute,
            'pairs':len(comparisons),'timing':timing,'comparisons':comparisons,
            'timing_interpretation':'Bounded decode throughput is infrastructure evidence. Wall-time changes can reflect different output lengths; capped answers do not establish useful-answer speedup.' if infrastructure else 'Natural complete-answer wall-time comparison.'}
        gate_helper.fast_write(root/'adaptive-quality-summary.json',summary)
    summary['status']='completed'
    summary['candidate_qualified']=summary['generation_exit']=='0' and all(
        summary['models'].get(s,{}).get('qualified',False) for s in ('2B','4B'))
    gate_helper.fast_write(root/'adaptive-quality-summary.json',summary)
    (root/'adaptive-quality-summary.md').write_text('# Adaptive MTP screen\n\n```json\n'+json.dumps(summary,indent=2,ensure_ascii=False)+'\n```\n')
    (root/'scoring-phase').write_text('completed\n')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path)
    p.add_argument('--key-file',type=Path,default=Path.home()/'.secret_ai_key');args=p.parse_args()
    score(args.root.resolve(),args.key_file.resolve())
