#!/usr/bin/env python3
"""Run bounded production GEMM attribution after acquiring the board lock."""
import argparse
import importlib.util
import json
import math
from pathlib import Path
import signal
import sys

HERE=Path(__file__).resolve().parent
def module(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'))
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
ime,patcher=module('k1-ime-test'),module('make-k1-gemm-audit')
fast=ime.fast
NAMES=('activation_quantization','staging_copies','gemm','grid_wait','pair_wait')


class Run(ime.Run):
    verified_modified_kernel=True
    compile_timeout=480
    kernel_relative='ggml/src/ggml-cpu/spacemit/ime.cpp'
    tag='gemm-audit'
    # This existing harness supplies a separate unchanged-operator sanity gate.
    harness='test-k1-gdn.cpp'
    binary='test-gdn'
    title='K1 production GEMM attribution'
    def generate(self,text): return patcher.generate(text)
    def run(self):
        try:
            self.prepare()
            self.summary['limitations']='Instrumented diagnostic: summed worker elapsed time includes overlapping waits and clock overhead. No speedup or removable wall-time claim.'
            self.provenance['diagnostic']={'prompt_tokens':256,'output_tokens':1,'sections':NAMES,'not_a_speed_comparison':True}
            fast.write_json(self.root/'provenance.json',self.provenance)
            self.command([self.root/self.binary],'numeric.log',180,self.env)
            if 'PASS: 158 cases;' not in (self.root/'numeric.log').read_text(): raise ValueError('unchanged-operator sanity failed')
            for model in ('2B','4B'):
                self.phase('production GEMM '+model)
                records=[]; labels=[]; profile=[]
                for mode in (0,1):
                    label=f'{model}-256-audit{mode}'; labels.append(label)
                    env=dict(self.env,SPINE_GEMM_AUDIT=str(mode))
                    if mode==0: env['LD_LIBRARY_PATH']=self.expected['runtime']['LD_LIBRARY_PATH']
                    self.command([sys.executable,HERE/'bench-lifecycle.py','--server',self.server,'--model',self.expected['models'][model]['path'],
                        '--label',label,'--mode','plain','--contexts',256,'--n-predict',1,'--ignore-eos','--verify-cold',
                        '--capture-token-ids','--gpu-layers',0,'--ctx-size',4096,'--timeout',180,
                        '--output',self.root/(label+'.jsonl'),'--log',self.root/(label+'.server.log')],label+'.driver.log',240,env)
                    records.extend(json.loads(l) for l in (self.root/(label+'.jsonl')).read_text().splitlines())
                    lines=(self.root/(label+'.server.log')).read_text().splitlines()
                    extracted=[json.loads(l.split('K1_GEMM_AUDIT ',1)[1]) for l in lines if l.startswith('K1_GEMM_AUDIT ')]
                    if bool(extracted)!=bool(mode): raise ValueError('GEMM attribution activation mismatch')
                    profile.extend(extracted)
                fast.check_model_records(records,labels,256)
                if not profile or any(len(r['section_ns'])!=5 or any(not math.isfinite(v) or v<0 for v in r['section_ns']) or
                                      sum(r['section_ns'])>r['total_ns']*1.001 for r in profile):
                    raise ValueError('invalid GEMM timing sections')
                (self.root/(model+'-gemm.jsonl')).write_text(''.join(json.dumps(r)+'\n' for r in profile))
                prefill=[r for r in profile if r['m']>1]; decode=[r for r in profile if r['m']==1]
                def aggregate(rows):
                    total=sum(r['total_ns'] for r in rows)
                    sections={name:sum(r['section_ns'][i] for r in rows) for i,name in enumerate(NAMES)}
                    return {'records':len(rows),'worker_elapsed_ns':total,'section_ns':sections,
                            'elapsed_fraction':{name:v/total if total else 0 for name,v in sections.items()},
                            'staging_copy_bytes':sum(r['copy_bytes'] for r in rows),
                            'buffer_sizes':sorted({r['buffer_size'] for r in rows})}
                if not prefill: raise ValueError('missing prefill GEMM records')
                self.summary['stages'][model]={'prefill':aggregate(prefill),'single_row':aggregate(decode),
                    'outputs_equal_to_original':True,'uncached_verified':True,
                    'single_row_note':'First-token work only; not sustained decode.'}
                self.save()
            self.summary.update(status='diagnostic complete',reason='Use section attribution to choose a packing/staging experiment; no optimized candidate enabled.')
            self.save(); self.phase(self.summary['status'])
        except BaseException as exc:
            self.summary.update(status='failed',reason=f'{type(exc).__name__}: {exc}'); self.save(); self.phase('failed'); raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('root',type=Path); args=p.parse_args()
    def interrupted(signum,frame): raise TimeoutError('board budget expired')
    signal.signal(signal.SIGTERM,interrupted); Run(args.root.resolve()).run()
