#!/usr/bin/env python3
"""Verify full-answer evidence, check usefulness and blind-score paired answers."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics

def module(name, root):
    spec=importlib.util.spec_from_file_location(name,root/(name+'.py'))
    result=importlib.util.module_from_spec(spec); spec.loader.exec_module(result); return result

def absolute_pass(case, facts, code):
    return all(facts['facts']) and all(facts['citations']) and (case['kind'] != 'code' or code.get('pass') is True)

def score(root, key_file):
    manifest=json.loads((root/'run.json').read_text()); receipt=json.loads((root/'collection-receipt.json').read_text())
    for name,digest in receipt['files_sha256'].items():
        if Path(name).name != name or hashlib.sha256((root/name).read_bytes()).hexdigest() != digest:
            raise ValueError('collected artifact changed: '+name)
    for name,digest in manifest['code_sha256'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest() != digest: raise ValueError('staged source changed: '+name)
    runner=module('k1-ssm-quality',root); judge=module('judge-shared-document-cache',root)
    gate_helper=module('score-mtp-quality',root)
    key=key_file.read_text().strip()
    if not key or '\n' in key: raise ValueError('judge key must be a nonempty single line')
    url=judge.endpoint(manifest['judge']['base_url'],False); judge_model=manifest['judge']['model']
    generation=json.loads((root/'summary.json').read_text())
    summary={'status':'scoring','generation_exit':(root/'exit-status').read_text().strip(),
             'verified_artifacts':len(receipt['files_sha256']),'judge_model':judge_model,'models':{},
             'operator_gate':generation['stages'].get('operators',{}).get('eligible',False),
             'limitations':'Six tasks/model, one pair/task, two answer orders from one cloud judge. Deterministic task checks establish correctness only for these tasks. Shared failures are not optimization regressions; identical answers alone do not establish usefulness. No general speedup claim.'}
    for size in ('2B','4B'):
        (root/'scoring-phase').write_text('score '+size+'\n')
        files=[root/(size+suffix) for suffix in ('-cases.json','-pairs.json','-configs.json')]
        if not all(p.exists() for p in files):
            summary['models'][size]={'status':'incomplete generation','qualified':False}; continue
        cases=json.loads(files[0].read_text())['cases']; raw=json.loads(files[1].read_text()); configs=json.loads(files[2].read_text())
        for arm,config in configs.items():
            argv=config['command']; env=config['runtime']
            if env.get('SPINE_K1_SSM_CONV') != ('0' if arm == 'control' else '3') or env.get('SPINE_K1_GEMM_ROUTE') != '3':
                raise ValueError('candidate or routing configuration differs')
            if '--spec-type' in argv or '--ignore-eos' in argv or '--no-context-shift' not in argv:
                raise ValueError('generation is not natural direct inference')
            for flag,value in (('-t','4'),('-c','6144'),('-b','32'),('-ub','32'),('-ctk','f16'),('-ctv','f16'),('-ngl','0')):
                if argv[argv.index(flag)+1] != value: raise ValueError('paired workload changed')
            runner.check_activation((root/(size+'-'+arm+'.server.log')).read_text(),0 if arm == 'control' else 3)
        grades=root/(size+'-judge.jsonl')
        previous={r['case_id']:r for r in map(json.loads,grades.read_text().splitlines())} if grades.exists() else {}
        pairs=[]; ratings=[]; inputs=[]
        for case in cases:
            arms=raw.get(case['case_id'],{}); row={'case_id':case['case_id'],'kind':case['kind']}
            if set(arms) != {'control','hybrid'}:
                pairs.append(dict(row,eligible=False,reason='missing arm')); continue
            audits={}; facts={}; code={}
            for arm,r in arms.items():
                if r.get('error'): audits[arm]={'error_free':False}; continue
                payload=r['request']
                if payload['messages'] != [{'role':'system','content':case['system']},{'role':'user','content':case['user']}] or payload['max_tokens'] != case['max_tokens']:
                    raise ValueError('full task input/output guard changed')
                if hashlib.sha256(r['answer'].encode()).hexdigest() != r['answer_sha256']:
                    raise ValueError('answer hash differs')
                if hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest() != r['request_sha256']:
                    raise ValueError('request hash differs')
                audits[arm]=runner.audit_result(r,payload,r['prompt_tokens'])
                if audits[arm] != r['audit']: raise ValueError('saved completion audit differs')
                facts[arm]=runner.checks.fact_check(case,r['answer'])
                code[arm]=runner.checks.check_code(case['case_id'],r['answer']) if case['kind'] == 'code' else {}
            eligible=all(all(a.values()) for a in audits.values())
            if not eligible:
                pairs.append(dict(row,eligible=False,audits=audits,
                    finish_reason={a:r.get('finish_reason') for a,r in arms.items()},reason='incomplete or invalid answer'))
                continue
            if arms['control']['request_sha256'] != arms['hybrid']['request_sha256'] or arms['control']['prompt_tokens'] != arms['hybrid']['prompt_tokens']:
                raise ValueError('paired full prompt differs')
            absolute={a:absolute_pass(case,facts[a],code[a]) for a in arms}
            deterministic_regression=any(gate_helper.regression(facts['control'][field],facts['hybrid'][field]) for field in ('facts','citations'))
            if case['kind'] == 'code': deterministic_regression |= code['control']['pass'] and not code['hybrid']['pass']
            d,h=arms['control'],arms['hybrid']
            comparison=dict(row,eligible=True,absolute_checks=absolute,deterministic_regression=bool(deterministic_regression),
                text_identical=d['answer_sha256'] == h['answer_sha256'],facts=facts,code_tests=code,
                output_tokens={a:r['usage']['completion_tokens'] for a,r in arms.items()},
                wall_s={a:r['wall_s'] for a,r in arms.items()},ttft_s={a:r['ttft_s'] for a,r in arms.items()},
                prefill_ms={a:r['timings']['prompt_ms'] for a,r in arms.items()},
                decode_ms={a:r['timings']['predicted_ms'] for a,r in arms.items()},
                wall_reduction_pct=100*(1-h['wall_s']/d['wall_s']))
            pairs.append(comparison)
            item={'case_id':size+'-'+case['case_id'],'question':case['question'],'evidence':case['evidence'],
                  'required_facts':case['required_facts'],'cold_answer':d['answer'],'warm_answer':h['answer']}
            inputs.append(item); runner.fast.write_json(root/(size+'-judge-input.json'),inputs)
            fingerprint=hashlib.sha256(json.dumps(item,sort_keys=True).encode()).hexdigest()
            rating=previous.get(item['case_id'])
            if rating:
                if rating['input_sha256'] != fingerprint or rating['judge_model'] != judge_model or len(rating['passes']) != 2:
                    raise ValueError('resumed judgment input differs')
            else:
                rating=judge.grade_case(item,url,judge_model,key,120,2,4096,True)
                with grades.open('a') as output: output.write(json.dumps(rating,ensure_ascii=False)+'\n')
            ratings.append(rating)
            comparison['scores']={'control':rating['cold_mean_score'],'hybrid':rating['warm_mean_score']}
            comparison['useful']={a:absolute[a] and comparison['scores'][a] >= 4 for a in arms}
            runner.fast.write_json(root/(size+'-comparisons.json'),pairs)
        valid=[p for p in pairs if p['eligible']]
        gate=gate_helper.judge_gate(ratings,valid,required=6)
        gate={k.replace('direct','control').replace('mtp','hybrid'):v for k,v in gate.items()}
        totals={a:sum(p['wall_s'][a] for p in valid) for a in ('control','hybrid')}
        gain=100*(1-totals['hybrid']/totals['control']) if totals['control'] else None
        useful_counts={a:sum(p.get('useful',{}).get(a,False) for p in valid) for a in ('control','hybrid')}
        all_useful=len(valid) == 6 and useful_counts['hybrid'] == 6
        state= generation['stages'].get('state-'+size,{}).get('bitwise_equal',False)
        summary['models'][size]={'status':'complete-answer pilot completed','eligible_pairs':len(valid),'judged_pairs':len(ratings),
            'relative_quality_gate':gate,'useful_answers':useful_counts,'all_candidate_answers_useful':all_useful,
            'paired_total_wall_s':totals,'total_wall_reduction_pct':gain,'state_identity':state,'comparisons':pairs,
            'qualified':all_useful and gate['pass'] and state and summary['operator_gate'] and gain is not None and gain > 3}
        runner.fast.write_json(root/'ssm-quality-summary.json',summary)
    summary.update(status='scoring completed',candidate_qualified=summary['generation_exit'] == '0' and all(
        summary['models'].get(size,{}).get('qualified',False) for size in ('2B','4B')))
    runner.fast.write_json(root/'ssm-quality-summary.json',summary)
    (root/'ssm-quality-summary.md').write_text('# Hybrid SSM complete-answer pilot\n\n'+summary['limitations']+'\n\n```json\n'+json.dumps(summary,indent=2,ensure_ascii=False)+'\n```\n')
    (root/'scoring-phase').write_text('completed\n')
    print(json.dumps({s:{k:v for k,v in m.items() if k != 'comparisons'} for s,m in summary['models'].items()},indent=2),flush=True)
    return summary

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('root',type=Path)
    parser.add_argument('--key-file',type=Path,default=Path.home()/'.secret_ai_key')
    args=parser.parse_args(); score(args.root.resolve(),args.key_file.resolve())
