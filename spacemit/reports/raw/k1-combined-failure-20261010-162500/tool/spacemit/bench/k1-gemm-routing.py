#!/usr/bin/env python3
"""Screen production Q4_0 staging bypass separately for prefill and decode."""
import argparse
import importlib.util
import json
import math
from pathlib import Path
import re
import signal
import sys

HERE = Path(__file__).resolve().parent
def module(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'))
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
ime,patcher=module('k1-ime-test'),module('make-k1-gemm-routing')
fast=ime.fast
MARKER=re.compile(r'K1_GEMM_ROUTE mode=(\d) phase=(prefill|single) eligible=(\d) bypass=(\d) buffer_size=(\d+)')


def check_activation(text, mode, phases):
    records={r[1]:r for r in MARKER.findall(text)}
    if mode==-1:
        if records: raise ValueError('original library unexpectedly has routing markers')
        return
    for phase in phases:
        r=records.get(phase)
        requested=mode==3 or (mode==1 and phase=='prefill') or (mode==2 and phase=='single')
        if not r or int(r[0])!=mode or r[2]!='1' or int(r[3])!=int(requested) or int(r[4])!=131072:
            raise ValueError('missing/wrong production routing activation: '+phase)


class Run(ime.Run):
    verified_modified_kernel=True
    compile_timeout=480
    kernel_relative='ggml/src/ggml-cpu/spacemit/ime.cpp'
    tag='gemm-routing'
    harness='test-k1-gemm-routing.cpp'
    binary='test-gemm-routing'
    switch='SPINE_K1_GEMM_ROUTE'
    title='K1 production GEMM routing screen'
    def generate(self,text): return patcher.generate(text)
    def arm_env(self,mode):
        env=dict(self.env,**{self.switch:str(max(mode,0))})
        if mode==-1: env['LD_LIBRARY_PATH']=self.expected['runtime']['LD_LIBRARY_PATH']
        return env
    def activation(self,text,mode):
        check_activation(text,mode,('prefill',))
    def native(self):
        self.phase('production graph numerical gate')
        hashes={}
        for mode in (-1,0,1,2,3):
            name=f'numeric-{mode}'
            self.command([self.root/self.binary,'--dump',self.root/(name+'.bin')],name+'.log',180,self.arm_env(mode))
            text=(self.root/(name+'.log')).read_text()
            if 'PASS: 104 production graph cases;' not in text: raise ValueError('incomplete native numerical gate')
            check_activation(text,mode,('prefill','single'))
            hashes[str(mode)]=fast.digest(self.root/(name+'.bin'))
        if len(set(hashes.values()))!=1: raise ValueError('production graph outputs differ from original library')
        self.summary['stages']['numeric']={'cases_per_arm':104,'output_sha256':hashes,'bitwise_equal':True,
            'checks':'production SpaceMiT weight repack and graph execution; M tails; original-library comparison; Q8 routing fallback; unchanged inputs and output/scratch guards'}
        self.save()
        self.phase('production operator timing')
        shapes=[]
        for model,dims in self.shapes.items():
            e,f=dims['embedding_length'],dims['feed_forward_length']
            for m in (1,32):
                for k,n in ((e,f),(f,e)): shapes.append((model,m,k,n))
        rows=[]
        for block in range(6):
            for model,m,k,n in shapes:
                candidate=1 if m>1 else 2
                modes=(-1,0,candidate) if block%2==0 else (candidate,0,-1)
                for mode in modes:
                    name=f'op-{model}-m{m}-k{k}-n{n}-b{block}-r{mode}'
                    self.command([self.root/self.binary,'--bench',m,k,n],name+'.log',45,self.arm_env(mode))
                    text=(self.root/(name+'.log')).read_text()
                    check_activation(text,mode,('prefill' if m>1 else 'single',))
                    found=[json.loads(l) for l in text.splitlines() if l.startswith('{')]
                    if len(found)!=1: raise ValueError('missing/extra operator record')
                    r=found[0]
                    if (r['m'],r['k'],r['n'])!=(m,k,n) or r['wall_ms']<100 or not math.isfinite(r['ms_per_call']) or r['ms_per_call']<=0:
                        raise ValueError('invalid operator timing')
                    rows.append(dict(r,model=model,block=block,mode=mode))
                    (self.root/'operator.jsonl').write_text(''.join(json.dumps(v)+'\n' for v in rows))
        comparisons=[]; controls=[]
        for model,m,k,n in shapes:
            candidate=1 if m>1 else 2
            arms={mode:[r['ms_per_call'] for r in rows if (r['model'],r['m'],r['k'],r['n'],r['mode'])==(model,m,k,n,mode)] for mode in (-1,0,candidate)}
            if any(len(v)!=6 for v in arms.values()): raise ValueError('missing operator arms')
            identity={'model':model,'m':m,'k':k,'n':n,'mode':candidate}
            comparisons.append(dict(identity,**fast.gate(arms[0],arms[candidate])))
            controls.append(dict(identity,**fast.gate(arms[-1],arms[0])))
        self.summary['stages']['operators']={'records':len(rows),'comparisons':comparisons,'original_control_checks':controls}
        self.save()
        eligible=[]
        for mode in (1,2):
            c=[r for r in comparisons if r['mode']==mode]
            ctrl=[r for r in controls if r['mode']==mode]
            if not any(r['clear_regression'] for r in c+ctrl) and sum(r['advance'] for r in c)>=2:
                eligible.append(mode)
        return eligible
    def decode(self,model):
        name=model+'-decode64'; self.phase('model '+name)
        rows=[]; labels=[]
        for i,mode in enumerate((0,2,2,0)):
            label=f'{name}-q{mode}-pass{i+1}'; labels.append(label)
            self.command([sys.executable,HERE/'bench-lifecycle.py','--server',self.server,'--model',self.expected['models'][model]['path'],
                '--label',label,'--mode','plain','--contexts',256,'--n-predict',64,'--ignore-eos','--verify-cold',
                '--capture-token-ids','--gpu-layers',0,'--ctx-size',4096,'--timeout',300,
                '--output',self.root/(label+'.jsonl'),'--log',self.root/(label+'.server.log')],label+'.driver.log',360,self.arm_env(mode))
            check_activation((self.root/(label+'.server.log')).read_text(),mode,('prefill','single'))
            rows.extend(json.loads(l) for l in (self.root/(label+'.jsonl')).read_text().splitlines())
        requests=fast.check_model_records(rows,labels,256,output_tokens=64)
        arms={m:[r['results'][0] for r in requests if f'-q{m}-' in r['label']] for m in (0,2)}
        for arm in arms.values():
            if any(r['timings'].get('predicted_n')!=64 or r['timings'].get('predicted_ms',0)<=0 for r in arm):
                raise ValueError('invalid sustained decode timing')
        comparison=fast.gate([r['timings']['predicted_ms'] for r in arms[0]],[r['timings']['predicted_ms'] for r in arms[2]])
        comparison.update(outputs_equal=True,uncached_verified=True,requests=4,output_tokens=64,
            prefill_check=fast.gate([r['timings']['prompt_ms'] for r in arms[0]],[r['timings']['prompt_ms'] for r in arms[2]]))
        self.summary['stages'][name]=comparison; self.save(); return comparison
    def run(self):
        try:
            self.prepare()
            self.summary['limitations']='Engineering screen on the current runtime: four workers, complete prompts, unchanged weights/quantization/IME arithmetic. Production graph operators use repeated weights; model ABBA pilots determine promotion. Decode64 is throughput evidence, not complete-answer quality.'
            eligible=self.native(); self.summary['eligible_modes']=eligible; self.save()
            qualified=[]
            if 1 in eligible:
                a=self.model('2B',512,1); b=self.model('4B',512,1)
                if a['advance'] and b['advance']:
                    c=self.model('2B',2048,1); d=self.model('4B',1024,1)
                    if c['advance'] and d['advance']: qualified.append(1)
            if 2 in eligible:
                a=self.decode('2B'); b=self.decode('4B')
                if a['advance'] and b['advance'] and not a['prefill_check']['clear_regression'] and not b['prefill_check']['clear_regression']:
                    qualified.append(2)
            self.summary.update(status='screen eligible' if qualified else 'inconclusive',qualified_modes=qualified,
                reason='Independent long-context and complete-answer confirmation remains; retain opt-in.' if qualified else 'No route cleared both model gates; retain original staging.')
            self.save(); self.phase(self.summary['status'])
        except BaseException as exc:
            self.summary.update(status='failed',reason=f'{type(exc).__name__}: {exc}'); self.save(); self.phase('failed'); raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('root',type=Path); args=p.parse_args()
    def interrupted(signum,frame): raise TimeoutError('board budget expired')
    signal.signal(signal.SIGTERM,interrupted); Run(args.root.resolve()).run()
