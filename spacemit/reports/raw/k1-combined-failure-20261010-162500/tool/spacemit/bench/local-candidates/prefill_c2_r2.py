#!/usr/bin/env python3
"""Run the fixed C2-r2 cold gate with actual worker evidence."""
import argparse
import fcntl
import json
import math
import os
import re
from pathlib import Path
import subprocess
import sys

import prepare

FAST = prepare.module('local_fast', prepare.HERE.parent/'k1-fast-test.py')
ARMS = prepare.FLAGS['C']


def arm_env(arm, library):
    env = {k:v for k,v in os.environ.items() if not k.startswith(('SPINE_', 'SPACEMIT_'))}
    env.update(SPINE_FA_WIDE_TILE='1', SPINE_FA_K1_LAYOUT='0', SPINE_K1_GEMM_ROUTE='3')
    env['LD_LIBRARY_PATH'] = str(library) + (':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
    env.update(SPINE_K1_TRACE='1', SPINE_K1_FA_GQA='0', SPINE_K1_FA_DECODE='0',
               SPINE_K1_CONV_SILU='0', SPINE_K1_SSM_CONV='0', SPINE_GDN_PREFILL='0')
    env.update(ARMS[arm])
    return env


def protocol(candidate, reference='C0'):
    if candidate != 'C2' or reference != 'C0':
        raise ValueError('invalid arm pair')
    if candidate != 'C3' and reference != 'C0':
        raise ValueError('invalid arm pair')
    return {'candidate':candidate, 'reference':reference,
            'order':[reference,candidate,candidate,reference], 'prompt_tokens':[512,2048],
            'output_tokens':[1,65], 'threads':4, 'batch':32, 'ubatch':32,
            'kv':'f16', 'route':3, 'mtp':False, 'temperature':0, 'seed':42,
            'models':['2B','4B'], 'threshold_pct':3.0,
            'prerequisites':['native outputs and state pass', 'operator gate passes', 'mixed chunks and RS fallback pass']}


def activation(text, arm):
    ssm = prepare.module('local_ssm_quality', prepare.HERE.parent/'k1-ssm-quality.py')
    ssm.check_activation(text, 3 if 'SPINE_K1_SSM_CONV' in ARMS[arm] else 0, require_both=False)
    if ('SPINE_GDN_PREFILL: scalar-gate K1 RVV fusion enabled' in text) != ('SPINE_GDN_PREFILL' in ARMS[arm]):
        raise ValueError('GDN activation differs from the arm')
    if 'K1_GEMM_ROUTE mode=3' not in text or 'SPINE_FA_WIDE_TILE: RVV tiled attention enabled for 256-dim heads' not in text:
        raise ValueError('control path evidence absent')
    if arm == 'C2':
        if 'SPINE_GDN_PREFILL_R2: retained two state segments; S=128; VLEN=256' not in text:
            raise ValueError('C2-r2 activation is absent')
        workers = set(re.findall(r'K1_GDN_R2 worker=(\d+) workers=4 state=128', text))
        if workers != {'0', '1', '2', '3'}:
            raise ValueError('C2-r2 worker evidence is incomplete')
    elif 'SPINE_GDN_PREFILL_R2:' in text or 'K1_GDN_R2 worker=' in text:
        raise ValueError('control activates C2-r2')


def compare(args, benchmark_lock=None):
    plan = protocol(args.candidate, args.reference)
    args.destination.mkdir(parents=True, exist_ok=False)
    (args.destination/'protocol.json').write_text(json.dumps(plan, indent=2)+'\n')
    if not args.execute:
        return {'status':'prepared', **plan}
    if not all((args.server, args.library, args.model_2b, args.model_4b)):
        raise ValueError('execute requires a server, a library directory and two models')
    if benchmark_lock is None:
        benchmark_lock = args.lock.open('a')
        fcntl.flock(benchmark_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    library = args.library/'libggml-cpu.so'
    identity = {'library_sha256':FAST.digest(library),
                'model_library_sha256':FAST.digest(args.library/'libllama.so'),
                'server_sha256':FAST.digest(args.server),
                'models_sha256':{m:FAST.digest(path) for m,path in (('2B',args.model_2b),('4B',args.model_4b))}}
    release = json.loads((prepare.REPO/'spacemit/release/manifest.json').read_text())
    if identity['models_sha256'] != {m:v['sha256'] for m,v in release['models'].items()}:
        raise ValueError('model identity differs from the protocol')
    if args.qualification is None:
        raise ValueError('execute requires a qualification receipt')
    qualification = json.loads(args.qualification.read_text())
    if qualification.get('identity') != identity or any(qualification.get(key) is not True
            for key in ('numeric_passed','state_passed','operators_passed')):
        raise ValueError('qualification gate or identity differs')
    if args.candidate not in qualification.get('qualified_arms', []):
        raise ValueError('qualification does not include this arm')
    if args.candidate == 'C3':
        receipts = [json.loads(p.read_text()) for p in args.single_results]
        if {r.get('candidate') for r in receipts} != {'C1','C2'} or len(receipts) != 2:
            raise ValueError('C3 requires C1 and C2 results')
        for receipt in receipts:
            if receipt.get('status') != 'eligible' or receipt.get('identity') != identity:
                raise ValueError('single-arm gate or identity differs')
    result = {'candidate':args.candidate, 'reference':args.reference, 'identity':identity,
              'status':'running', 'comparisons':[], 'limitations':'Cold timing screen. Full-answer quality and independent repeats remain unverified.'}
    for tokens in plan['prompt_tokens']:
        for model,path in (('2B',args.model_2b),('4B',args.model_4b)):
            for outputs in plan['output_tokens']:
                records, labels = [], []
                for repeat,arm in enumerate(plan['order']):
                    label = f'{model}-p{tokens}-n{outputs}-{arm}-{repeat}'
                    labels.append(label)
                    log = args.destination/(label+'.server.log')
                    data = args.destination/(label+'.jsonl')
                    command = [sys.executable,prepare.HERE.parent/'bench-lifecycle.py','--server',args.server,
                        '--model',path,'--label',label,'--mode','plain','--contexts',str(tokens),
                        '--n-predict',str(outputs),'--ignore-eos','--verify-cold','--capture-token-ids',
                        '--threads','4','--batch-size','32','--ubatch-size','32','--gpu-layers','0',
                        '--ctx-size','4096','--cache-type-k','f16','--cache-type-v','f16',
                        '--timeout','600','--output',data,'--log',log]
                    with (args.destination/(label+'.driver.log')).open('w') as output:
                        subprocess.run(list(map(str,command)),stdout=output,stderr=subprocess.STDOUT,
                                       env=arm_env(arm,args.library),check=True,timeout=700)
                    activation(log.read_text(),arm)
                    records.extend(json.loads(line) for line in data.read_text().splitlines())
                requests = FAST.check_model_records(records, labels, tokens, outputs)
                values = {arm:[r['results'][0] for r in requests if '-'+arm+'-' in r['label']]
                          for arm in (args.reference,args.candidate)}
                metrics = {}
                for metric,key in (('prefill','prompt_ms'),('decode','predicted_ms'),('ttft',None)):
                    if metric == 'decode' and outputs == 1:
                        continue
                    times = {arm:[r['timings'][key] if key else r['ttft_ms'] for r in rows] for arm,rows in values.items()}
                    if any(not math.isfinite(t) or t <= 0 for rows in times.values() for t in rows):
                        raise ValueError('invalid phase time')
                    metrics[metric] = FAST.gate(times[args.reference],times[args.candidate])
                passed = (metrics['prefill']['advance'] and metrics['ttft']['advance']) if outputs == 1 else not metrics['decode']['clear_regression']
                result['comparisons'].append({'model':model,'tokens':tokens,'outputs':outputs,'metrics':metrics,'passed':passed})
                result['status'] = 'running' if passed else 'stopped'
                (args.destination/'result.json').write_text(json.dumps(result,indent=2)+'\n')
                if not passed:
                    return result
    result['status'] = 'eligible'
    (args.destination/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('destination',type=Path)
    p.add_argument('--candidate',choices=('C1','C2','C3'),required=True)
    p.add_argument('--reference',choices=ARMS,default='C0')
    p.add_argument('--execute',action='store_true')
    p.add_argument('--server',type=Path)
    p.add_argument('--library',type=Path)
    p.add_argument('--model-2b',type=Path)
    p.add_argument('--model-4b',type=Path)
    p.add_argument('--single-results',type=Path,nargs='*',default=[])
    p.add_argument('--qualification',type=Path)
    p.add_argument('--lock',type=Path,default=Path.home()/'Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock')
    arguments = p.parse_args()
    print(json.dumps(compare(arguments),indent=2))
