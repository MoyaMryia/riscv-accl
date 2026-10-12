#!/usr/bin/env python3
"""Verify generation evidence, blind-score eligible pairs, and report MTP usefulness."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics

HERE=Path(__file__).resolve().parent
def module(name,folder=HERE):
    spec=importlib.util.spec_from_file_location(name,folder/(name+'.py'))
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def regression(a,b):
    return any(x and not y for x,y in zip(a,b)) or len(a)!=len(b)


def judge_gate(scores, pairs, required=6):
    covered=len(scores)==required and len(pairs)==required
    if not covered: return {'pass':False,'reason':'incomplete eligible/judged coverage'}
    direct_mean=statistics.mean(s['cold_mean_score'] for s in scores)
    mtp_mean=statistics.mean(s['warm_mean_score'] for s in scores)
    loss=max(s['cold_mean_score']-s['warm_mean_score'] for s in scores)
    deterministic=all(not p['deterministic_regression'] for p in pairs)
    return {'pass':deterministic and mtp_mean>=direct_mean-0.25 and loss<=0.5,
        'direct_mean_score':direct_mean,'mtp_mean_score':mtp_mean,'worst_pair_score_loss':loss,
        'deterministic_no_regression':deterministic,
        'thresholds':{'mean_score_loss':0.25,'worst_pair_score_loss':0.5},
        'interpretation':'descriptive pilot; no statistical noninferiority or universal equivalence claim'}


def score(root, key_file, base_url, model):
    manifest=json.loads((root/'run.json').read_text()); receipt=json.loads((root/'collection-receipt.json').read_text())
    for name,digest in receipt['files_sha256'].items():
        if Path(name).name!=name or hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('collected artifact hash differs: '+name)
    for name,digest in manifest['code_sha256'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest: raise ValueError('staged code differs: '+name)
    runner=module('mtp-quality',root); checks=module('mtp-quality-checks',root)
    judge=module('judge-shared-document-cache',root)
    # The key stays on the workstation and is never staged, logged or sent to the board.
    key=key_file.read_text().strip()
    if not key or '\n' in key: raise ValueError('judge key must be one nonempty line')
    url=judge.endpoint(base_url,False)
    summary={'status':'scoring','generation_exit':(root/'exit-status').read_text().strip(),
        'verified_artifacts':len(receipt['files_sha256']),'judge_model':model,
        'models':{},'limitations':'Six tasks, one pair per model/task, one cloud judge in two answer orders. Shared baseline failures are reported, not labelled MTP regressions. RS rollback is untested here.'}
    for size in ('2B','4B'):
        (root/'scoring-phase').write_text('score '+size+'\n')
        cases_file=root/(size+'-cases.json'); pairs_file=root/(size+'-pairs.json')
        if not cases_file.exists() or not pairs_file.exists():
            summary['models'][size]={'status':'incomplete generation'}; continue
        cases=json.loads(cases_file.read_text())['cases']; raw=json.loads(pairs_file.read_text())
        configurations=json.loads((root/(size+'-configs.json')).read_text())
        for arm,config in configurations.items():
            argv=config['command']
            if config['runtime'].get('SPINE_SPEC_RS')!='0' or config['runtime'].get('SPINE_K1_GEMM_ROUTE')!='0':
                raise ValueError('checkpoint/routing settings changed')
            if ('--spec-type' in argv)!=(arm=='mtp') or '--no-context-shift' not in argv:
                raise ValueError('server mode or overflow protection changed')
            for flag,value in (('-t','4'),('-c','6144'),('-b','32'),('-ub','32'),('-ctk','f16'),('-ctv','f16'),('-ngl','0')):
                if argv[argv.index(flag)+1]!=value: raise ValueError('server workload changed')
        mtp_log_path=root/(size+'-mtp.server.log')
        if 'mtp' not in configurations or not mtp_log_path.exists():
            summary['models'][size]={'status':'incomplete generation: MTP arm missing'}; continue
        if not runner.ACCEPTANCE.search(mtp_log_path.read_text()):
            summary['models'][size]={'status':'incomplete generation: MTP activity absent'}; continue
        comparisons=[]; scores=[]; inputs=[]
        grade_file=root/(size+'-judge.jsonl')
        previous={r['case_id']:r for r in (json.loads(l) for l in grade_file.read_text().splitlines())} if grade_file.exists() else {}
        for case in cases:
            arms=raw.get(case['case_id'],{}); row={'case_id':case['case_id'],'kind':case['kind']}
            if set(arms)!={'direct','mtp'}:
                comparisons.append(dict(row,eligible=False,reason='missing arm')); continue
            audits={}; fact_checks={}; code_checks={}
            for arm,result in arms.items():
                if result.get('error'):
                    audits[arm]={'error_free':False}; continue
                payload=result['request']
                expected_messages=[{'role':'system','content':case['system']},{'role':'user','content':case['user']}]
                if payload['messages']!=expected_messages: raise ValueError('full task input changed')
                if hashlib.sha256(result['answer'].encode()).hexdigest()!=result['answer_sha256']:
                    raise ValueError('answer text/hash differs')
                if hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest()!=result['request_sha256']:
                    raise ValueError('request hash differs')
                audits[arm]=runner.audit_result(result,payload,result['prompt_tokens'])
                if audits[arm]!=result['audit']: raise ValueError('completion audit differs')
                fact_checks[arm]=checks.fact_check(case,result['answer'])
                if case['kind']=='code': code_checks[arm]=checks.check_code(case['case_id'],result['answer'])
            eligible=all(all(v.values()) for v in audits.values()) and arms['direct'].get('prompt_tokens')==arms['mtp'].get('prompt_tokens')
            if not eligible:
                comparisons.append(dict(row,eligible=False,audits=audits,reason='incomplete, cached, mismatched or invalid request')); continue
            if arms['direct']['request_sha256']!=arms['mtp']['request_sha256']: raise ValueError('paired request differs')
            deterministic_regression=(regression(fact_checks['direct']['facts'],fact_checks['mtp']['facts'])
                or regression(fact_checks['direct']['citations'],fact_checks['mtp']['citations'])
                or case['kind']=='code' and code_checks['direct']['pass'] and not code_checks['mtp']['pass'])
            comparison=dict(row,eligible=True,deterministic_regression=bool(deterministic_regression),
                facts=fact_checks,code_tests=code_checks,text_identical=arms['direct']['answer_sha256']==arms['mtp']['answer_sha256'],
                output_tokens={a:r['usage']['completion_tokens'] for a,r in arms.items()},
                wall_s={a:r['wall_s'] for a,r in arms.items()},ttft_s={a:r['ttft_s'] for a,r in arms.items()},
                decode_ms={a:r['timings']['predicted_ms'] for a,r in arms.items()},
                decode_tps={a:1000*r['timings']['predicted_n']/r['timings']['predicted_ms'] for a,r in arms.items()})
            comparison['wall_reduction_pct']=100*(1-comparison['wall_s']['mtp']/comparison['wall_s']['direct'])
            comparisons.append(comparison)
            item={'case_id':size+'-'+case['case_id'],'question':case['question'],'evidence':case['evidence'],
                  'required_facts':case['required_facts'],'cold_answer':arms['direct']['answer'],'warm_answer':arms['mtp']['answer']}
            inputs.append(item)
            fast_write(root/(size+'-judge-input.json'),inputs)
            fingerprint=hashlib.sha256(json.dumps(item,sort_keys=True).encode()).hexdigest()
            if item['case_id'] in previous:
                rating=previous[item['case_id']]
                if rating['input_sha256']!=fingerprint or rating['judge_model']!=model or len(rating['passes'])!=2:
                    raise ValueError('resume judge evidence differs')
            else:
                rating=judge.grade_case(item,url,model,key,120,2,1536,True)
                with grade_file.open('a') as output: output.write(json.dumps(rating,ensure_ascii=False)+'\n')
            scores.append(rating)
            fast_write(root/(size+'-comparisons.json'),comparisons)
        gate=judge_gate(scores,[p for p in comparisons if p['eligible']],required=6)
        valid=[p for p in comparisons if p['eligible']]
        direct_wall=sum(p['wall_s']['direct'] for p in valid); mtp_wall=sum(p['wall_s']['mtp'] for p in valid)
        timing={'paired_total_wall_s':{'direct':direct_wall,'mtp':mtp_wall},
            'total_wall_reduction_pct':100*(1-mtp_wall/direct_wall) if direct_wall else None,
            'interpretation':'descriptive complete-task latency; output lengths may differ, so also inspect per-task throughput'}
        summary['models'][size]={'status':'pilot quality gate passed' if gate['pass'] else 'quality/incomplete review required',
            'gate':gate,'timing':timing,'planned_pairs':6,'eligible_pairs':len(valid),'judged_pairs':len(scores),'comparisons':comparisons}
        fast_write(root/'quality-summary.json',summary)
    summary['status']='scoring completed'
    summary['candidate_useful_in_pilot']=summary['generation_exit']=='0' and len(summary['models'])==2 and all(
        m.get('gate',{}).get('pass') and m['gate']['mtp_mean_score']>=4
        and all(all(p['facts']['mtp']['facts']) and (p['kind']!='code' or p['code_tests']['mtp']['pass']) for p in m['comparisons'])
        and m['timing']['total_wall_reduction_pct']>3 for m in summary['models'].values())
    fast_write(root/'quality-summary.json',summary)
    (root/'quality-summary.md').write_text('# Checkpoint MTP complete-answer pilot\n\n'+summary['limitations']+'\n\n```json\n'+json.dumps(summary,indent=2,ensure_ascii=False)+'\n```\n')
    (root/'scoring-phase').write_text('completed\n')
    print(json.dumps({k:{'status':v['status'],'gate':v.get('gate'),'timing':v.get('timing')} for k,v in summary['models'].items()},indent=2),flush=True)
    return summary


def fast_write(path,value):
    temporary=path.with_suffix(path.suffix+'.tmp'); temporary.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n'); temporary.replace(path)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('root',type=Path)
    parser.add_argument('--key-file',type=Path,default=Path.home()/'.secret_ai_key')
    parser.add_argument('--base-url',default='https://api.xiaomimimo.com/v1'); parser.add_argument('--model',default='mimo-v2.6-flash')
    args=parser.parse_args(); score(args.root.resolve(),args.key_file,args.base_url,args.model)
