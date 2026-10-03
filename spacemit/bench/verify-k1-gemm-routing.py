#!/usr/bin/env python3
"""Recalculate a completed routing screen from collected artifacts and requests."""
import argparse
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('route',HERE/'k1-gemm-routing.py')
route=importlib.util.module_from_spec(spec); spec.loader.exec_module(route)
fast=route.fast


def check_config(record, model_path, mode, output_tokens):
    required={'model':model_path,'threads':4,'batch_size':32,'ubatch_size':32,
              'cache_type_k':'f16','cache_type_v':'f16','gpu_layers':0,
              'parallel':1,'concurrency':1,'ctx_size':4096,'mode':'plain',
              'n_predict':output_tokens,'capture_token_ids':True,
              'ignore_eos':True,'cache_prompt':False,'verify_cold':True}
    if any(record.get(k)!=v for k,v in required.items()):
        raise ValueError('model workload/configuration changed')
    env=record.get('runtime_env',{})
    expected={'SPINE_FA_WIDE_TILE':'1','SPINE_FA_K1_LAYOUT':'0'}
    if any(env.get(k)!=v for k,v in expected.items()):
        raise ValueError('runtime routing/attention configuration changed')
    # The first run's lifecycle allowlist omitted the new flag. Actual mode,
    # eligibility and bypass are independently required from kernel markers
    # below. Reject an explicitly recorded conflicting flag when present.
    if 'SPINE_K1_GEMM_ROUTE' in env and env['SPINE_K1_GEMM_ROUTE']!=str(mode):
        raise ValueError('recorded routing flag conflicts with the arm')


def verify(root):
    if (root/'exit-status').read_text().strip()!='0': raise ValueError('run is not successfully complete')
    receipt=json.loads((root/'collection-receipt.json').read_text())
    for name,digest in receipt['files_sha256'].items():
        if Path(name).name!=name or fast.digest(root/name)!=digest: raise ValueError('artifact checksum mismatch: '+name)
    summary=json.loads((root/'summary.json').read_text())
    if summary['status'] not in ('screen eligible','inconclusive'):
        raise ValueError('screen did not reach its terminal result')
    expected=json.loads((root/'expected-provenance.json').read_text())
    numeric=summary['stages']['numeric']
    hashes=numeric['output_sha256']
    if numeric['cases_per_arm']!=104 or set(hashes)!={'-1','0','1','2','3'} or len(set(hashes.values()))!=1:
        raise ValueError('incomplete/different numerical arms')
    for mode in (-1,0,1,2,3):
        log=(root/f'numeric-{mode}.log').read_text()
        if 'PASS: 104 production graph cases;' not in log: raise ValueError('numerical guard checks incomplete')
        route.check_activation(log,mode,('prefill','single'))
    rows=[json.loads(l) for l in (root/'operator.jsonl').read_text().splitlines()]
    comparisons=summary['stages']['operators']['comparisons']
    controls=summary['stages']['operators']['original_control_checks']
    if len(rows)!=144 or len(comparisons)!=8 or len(controls)!=8: raise ValueError('operator matrix incomplete')
    for c in comparisons:
        model,m,k,n,mode=(c[x] for x in ('model','m','k','n','mode'))
        arms={r:[v for v in rows if (v['model'],v['m'],v['k'],v['n'],v['mode'])==(model,m,k,n,r)] for r in (-1,0,mode)}
        for r,values in arms.items():
            if len(values)!=6 or {v['block'] for v in values}!=set(range(6)): raise ValueError('operator block missing/duplicated')
            for v in values:
                log=(root/f'op-{model}-m{m}-k{k}-n{n}-b{v["block"]}-r{r}.log').read_text()
                route.check_activation(log,r,('single' if m==1 else 'prefill',))
        calculated=fast.gate([v['ms_per_call'] for v in arms[0]],[v['ms_per_call'] for v in arms[mode]])
        if any(c[key]!=value for key,value in calculated.items()): raise ValueError('operator summary differs from records')
        original=fast.gate([v['ms_per_call'] for v in arms[-1]],[v['ms_per_call'] for v in arms[0]])
        matched=[v for v in controls if (v['model'],v['m'],v['k'],v['n'],v['mode'])==(model,m,k,n,mode)]
        if len(matched)!=1 or any(matched[0][key]!=value for key,value in original.items()):
            raise ValueError('original-control summary differs from records')
    eligible=[]
    for mode in (1,2):
        c=[r for r in comparisons if r['mode']==mode]
        ctrl=[r for r in controls if r['mode']==mode]
        if len(c)!=4 or len(ctrl)!=4: raise ValueError('phase shape matrix incomplete')
        if not any(r['clear_regression'] for r in c+ctrl) and sum(r['advance'] for r in c)>=2:
            eligible.append(mode)
    if eligible!=summary.get('eligible_modes'): raise ValueError('eligible modes differ from operator gates')
    required=set()
    if 1 in eligible:
        required.update(('2B-512','4B-512'))
        if all(summary['stages'].get(name,{}).get('advance') for name in ('2B-512','4B-512')):
            required.update(('2B-2048','4B-1024'))
    if 2 in eligible: required.update(('2B-decode64','4B-decode64'))
    if set(summary['stages'])!={'numeric','operators',*required}:
        raise ValueError('required model stages missing or extra stages present')
    result={}
    for name,stored in summary['stages'].items():
        if name in ('numeric','operators'): continue
        model=name.split('-')[0]; decode=name.endswith('decode64')
        tokens=256 if decode else int(name.split('-')[1])
        output_tokens=64 if decode else 1; candidate=2 if decode else 1
        labels=[f'{name}-q{mode}-pass{i+1}' for i,mode in enumerate((0,candidate,candidate,0))]
        records=[]
        for label,mode in zip(labels,(0,candidate,candidate,0)):
            data=[json.loads(l) for l in (root/(label+'.jsonl')).read_text().splitlines()]
            configs=[r for r in data if r.get('kind')=='config']
            if len(configs)!=1: raise ValueError('config missing/duplicated')
            check_config(configs[0],expected['models'][model]['path'],mode,output_tokens)
            log=(root/(label+'.server.log')).read_text()
            route.check_activation(log,mode,('prefill','single'))
            if 'SPINE_FA_WIDE_TILE: RVV tiled attention enabled for 256-dim heads' not in log:
                raise ValueError('wide attention activation missing')
            records.extend(data)
        measurements=fast.check_model_records(records,labels,tokens,output_tokens)
        if decode and any(r['results'][0]['timings'].get('predicted_n')!=64 for r in measurements):
            raise ValueError('decode timing token count mismatch')
        field='predicted_ms' if decode else 'prompt_ms'
        arms={m:[r['results'][0]['timings'][field] for r in measurements if f'-q{m}-' in r['label']] for m in (0,candidate)}
        comparison=fast.gate(arms[0],arms[candidate])
        if any(stored[k]!=v for k,v in comparison.items()): raise ValueError('model summary differs from request timings')
        if decode:
            prompt_arms={m:[r['results'][0]['timings']['prompt_ms'] for r in measurements if f'-q{m}-' in r['label']] for m in (0,candidate)}
            prefill=fast.gate(prompt_arms[0],prompt_arms[candidate])
            if stored['prefill_check']!=prefill: raise ValueError('decode prefill check differs from requests')
        result[name]=comparison
    qualified=[]
    if all(summary['stages'].get(name,{}).get('advance') for name in ('2B-512','4B-512','2B-2048','4B-1024')):
        qualified.append(1)
    if all(summary['stages'].get(name,{}).get('advance') and not summary['stages'][name]['prefill_check']['clear_regression'] for name in ('2B-decode64','4B-decode64')):
        qualified.append(2)
    if qualified!=summary.get('qualified_modes'): raise ValueError('qualified modes differ from completed gates')
    if summary['status']!=('screen eligible' if qualified else 'inconclusive'):
        raise ValueError('terminal status differs from qualified gates')
    return {'verified_artifacts':len(receipt['files_sha256']),'numeric_cases_per_arm':104,
            'routing_evidence':'Required actual per-phase kernel mode/eligibility/bypass markers; routing env field checked when recorded.',
            'operator_records':144,'qualified_modes':qualified,'model_comparisons':result}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('run_dir',type=Path)
    a=p.parse_args(); print(json.dumps(verify(a.run_dir.resolve()),indent=2))
