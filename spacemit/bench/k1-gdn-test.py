#!/usr/bin/env python3
"""Screen exact per-token RVV fusion for eligible recurrent prefill."""
import argparse
import json
import math
import os
from pathlib import Path
import signal
import subprocess

import importlib.util
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('ime',HERE/'k1-ime-test.py')
ime=importlib.util.module_from_spec(spec); spec.loader.exec_module(ime)


def generate(text):
    old='if (!kda && K == 1 && n_tokens == 1 && !(getenv("SPINE_GDN_RVV")'
    new='if (!kda && K == 1 && (n_tokens == 1 || (getenv("SPINE_GDN_PREFILL") != nullptr && strcmp(getenv("SPINE_GDN_PREFILL"), "1") == 0)) && !(getenv("SPINE_GDN_RVV")'
    if text.count(old)!=1: raise ValueError('unexpected recurrent dispatch')
    text=text.replace(old,new)
    call='                ggml_gdn_decode_step_rvv(s_out, k_d, v_d, q_d, expf(g_d[0]), beta_val, scale, S_v, attn_data);'
    if text.count(call)!=1: raise ValueError('unexpected fused call')
    marker='''                if (n_tokens > 1) {
                    static const bool logged = [] {
                        fprintf(stderr, "SPINE_GDN_PREFILL: scalar-gate K1 RVV fusion enabled\\n");
                        return true;
                    }();
                    (void) logged;
                }
'''
    return text.replace(call,marker+call).replace('#include <algorithm>','#include <algorithm>\n#include <cstdio>\n#include <cstdlib>\n#include <cstring>',1)


class Run(ime.Run):
    kernel_relative='ggml/src/ggml-cpu/ops.cpp'
    tag='gdn'
    harness='test-k1-gdn.cpp'
    binary='test-gdn'
    switch='SPINE_GDN_PREFILL'
    title='K1 recurrent prefill fusion screen'
    def __init__(self,root):
        super().__init__(root)
        self.summary['limitations']='Engineering screen; operator graph timing excludes full-model costs. No significance, decode or quality claim.'
    def generate(self,text): return generate(text)
    def model_dimensions(self,path):
        shape=ime.dimensions(path,('qwen35.ssm.state_size','qwen35.ssm.group_count',
                                   'qwen35.ssm.time_step_rank','qwen35.ssm.inner_size'))
        if shape not in ({'state_size':128,'group_count':16,'time_step_rank':16,'inner_size':2048},
                         {'state_size':128,'group_count':16,'time_step_rank':32,'inner_size':4096}):
            raise ValueError('operator benchmark does not cover this model shape')
        return shape
    def activation(self,text,mode):
        active='SPINE_GDN_PREFILL: scalar-gate K1 RVV fusion enabled' in text
        if active != bool(mode): raise ValueError('recurrent activation differs from selected arm')
    def native(self):
        self.phase('recurrent numerical gate')
        self.command([self.root/self.binary],'numeric.log',180,self.env)
        text=(self.root/'numeric.log').read_text()
        if 'PASS: 158 cases;' not in text or 'SPINE_GDN_PREFILL: scalar-gate K1 RVV fusion enabled' not in text:
            raise ValueError('recurrent numerical gate incomplete')
        self.summary['stages']['numeric']={'cases':158,'bitwise_equal':True,'attention_and_state':True}; self.save()
        self.phase('recurrent operator timing')
        env=dict(self.env,SPINE_GDN_RVV='1')
        with (self.root/'operator.jsonl').open('w') as out, (self.root/'operator.err').open('w') as err:
            subprocess.run([self.root/self.binary,'--bench'],env=env,stdout=out,stderr=err,check=True,timeout=240)
        rows=[json.loads(l) for l in (self.root/'operator.jsonl').read_text().splitlines()]
        expected={(h,t,b,m) for h in (16,32) for t in (8,32) for b in range(6) for m in (0,1)}
        if len(rows)!=48 or {(r['heads'],r['tokens'],r['block'],r['mode']) for r in rows}!=expected:
            raise ValueError('operator arms incomplete')
        if any(r['wall_ms']<100 or r['state_size']!=128 or r['key_heads']!=16 or
               not math.isfinite(r['ms_per_call']) or r['ms_per_call']<=0 for r in rows):
            raise ValueError('invalid operator timing')
        comparisons=[]
        for h in (16,32):
            for t in (8,32):
                arm={m:[r['ms_per_call'] for r in rows if (r['heads'],r['tokens'],r['mode'])==(h,t,m)] for m in (0,1)}
                comparisons.append({'heads':h,'tokens':t,**ime.fast.gate(arm[0],arm[1])})
        self.summary['stages']['operators']={'records':48,'comparisons':comparisons}; self.save()
        return 1 if sum(c['advance'] for c in comparisons)>=2 and not any(c['clear_regression'] for c in comparisons) else None


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('root',type=Path); args=parser.parse_args()
    def interrupted(signum,frame): raise TimeoutError('board budget expired')
    signal.signal(signal.SIGTERM,interrupted)
    Run(args.root.resolve()).run()
