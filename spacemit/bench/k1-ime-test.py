#!/usr/bin/env python3
"""Build one isolated CPU object, gate IME scheduling variants, then screen models."""
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shlex
import statistics
import struct
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
def module(name):
    s=importlib.util.spec_from_file_location(name,HERE/(name+'.py'))
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
fast, patcher = module('k1-fast-test'), module('make-k1-ime-candidate')


def dimensions(path, keys=('qwen35.embedding_length','qwen35.feed_forward_length')):
    formats={0:'B',1:'b',2:'H',3:'h',4:'I',5:'i',6:'f',7:'?',10:'Q',11:'q',12:'d'}
    with Path(path).open('rb') as f:
        def number(fmt):
            n=struct.calcsize('<'+fmt); b=f.read(n)
            if len(b)!=n: raise ValueError('truncated metadata')
            return struct.unpack('<'+fmt,b)[0]
        def string(read=True):
            n=number('Q')
            if n>Path(path).stat().st_size: raise ValueError('invalid metadata length')
            if not read: f.seek(n,1); return None
            b=f.read(n)
            if len(b)!=n: raise ValueError('truncated string')
            return b.decode()
        def value(kind,read=False):
            if kind==8: return string(read)
            if kind==9:
                element,count=number('I'),number('Q')
                if count>Path(path).stat().st_size: raise ValueError('invalid array length')
                if element in formats: f.seek(count*struct.calcsize('<'+formats[element]),1)
                else:
                    for _ in range(count): value(element)
                return None
            return number(formats[kind])
        if f.read(4)!=b'GGUF' or number('I') not in (2,3): raise ValueError('not GGUF')
        number('Q'); count=number('Q'); found={}
        if count>100000: raise ValueError('invalid metadata count')
        for _ in range(count):
            key=string(); wanted=key in keys
            v=value(number('I'),wanted)
            if wanted: found[key.split('.')[-1]]=v
    if set(found)!={k.split('.')[-1] for k in keys} or any(not isinstance(v,int) or v<=0 for v in found.values()):
        raise ValueError('invalid model GEMM dimensions')
    if any(v%32 for k,v in found.items() if k in ('embedding_length','feed_forward_length')):
        raise ValueError('invalid model GEMM dimensions')
    return found


def compile_argv(line, source, output, include):
    old=shlex.split(line); new=[]; i=0
    while i<len(old):
        if old[i] in ('-o','-c','-MT','-MF'): i+=2; continue
        if old[i]=='-MD': i+=1; continue
        new.append(old[i]); i+=1
    return new+['-I'+str(include),'-o',str(output),'-c',str(source)]


def link_argv(line, output, object_file, object_suffix='/spacemit/ime1_kernels.cpp.o'):
    segments=line.split(' && ')
    if len(segments)!=3 or segments[0]!=':' or segments[-1]!=':': raise ValueError('unexpected link recipe')
    args=shlex.split(segments[1]); replaced=0
    for i,arg in enumerate(args):
        if i and args[i-1]=='-o': args[i]=str(output)
        if arg.endswith(object_suffix):
            args[i]=str(object_file); replaced+=1
    if replaced!=1: raise ValueError('kernel object not unique')
    return args


class Run:
    kernel_relative='ggml/src/ggml-cpu/spacemit/ime1_kernels.cpp'
    tag='ime1'
    harness='test-k1-ime.cpp'
    binary='test-ime'
    switch='SPINE_IME_M4_SCHEDULE'
    title='K1 IME scheduling screen'
    def generate(self,text): return patcher.generate(text)
    def model_dimensions(self,path): return dimensions(path)
    def activation(self,text,mode):
        if f'SPINE_IME_M4_SCHEDULE: mode={mode} Q4_0 M4 K32 enabled' not in text:
            raise ValueError('candidate/control activation missing')
    def __init__(self,root):
        self.root=root; self.expected=json.loads((root/'expected-provenance.json').read_text())
        self.started=time.monotonic(); self.summary={'status':'running','stages':{},
            'limitations':'Engineering screen; warm DDR operator tensors omit production packing, staging and SPERT synchronization. No significance, decode or quality claim.'}
    def phase(self,name):
        (self.root/'phase').write_text(name+'\n'); print(name,flush=True)
    def command(self,argv,log,timeout=180,env=None,cwd=None):
        if cwd is None: return fast.command(argv,self.root/log,timeout,env)
        # Compilation runs synchronously under the board job's overall timeout.
        with (self.root/log).open('w') as output:
            subprocess.run(list(map(str,argv)),stdout=output,stderr=subprocess.STDOUT,
                           check=True,timeout=timeout,cwd=cwd,env=env)
    def save(self):
        self.summary['elapsed_s']=time.monotonic()-self.started
        fast.write_json(self.root/'summary.json',self.summary)
        lines=['# '+self.title,'','Status: '+self.summary['status'],'',self.summary['limitations'],'']
        for name,result in self.summary['stages'].items():
            lines += ['## '+name,'',json.dumps(result,indent=2),'']
        lines += [self.summary.get('reason','')]
        (self.root/'summary.md').write_text('\n'.join(lines)+'\n')
    def prepare(self):
        self.phase('verify and build isolated kernel')
        artifacts=self.expected['artifacts_sha256']
        self.server=next(Path(p) for p in artifacts if p.endswith('/llama-server'))
        self.source=self.server.parents[2]; self.build=self.source/'build'
        changed=set(subprocess.check_output(['git','-C',self.source,'diff','HEAD','--name-only'],text=True).splitlines())
        if changed!=set(self.expected['source_sha256']): raise ValueError('unexpected source changes')
        if subprocess.check_output(['git','-C',self.source,'rev-parse','--short=7','HEAD'],text=True).strip()!='a990751':
            raise ValueError('unexpected source revision')
        for p,h in self.expected['source_sha256'].items():
            if fast.digest(self.source/p)!=h: raise ValueError('source changed')
        for p,h in artifacts.items():
            if '/build/' in p or '/.toolchain/' in p or '/spert/' in p:
                if fast.digest(p)!=h: raise ValueError('binary/runtime changed')
        self.shapes={}
        for model,info in self.expected['models'].items():
            if fast.digest(info['path'])!=info['sha256']: raise ValueError('model changed')
            self.shapes[model]=self.model_dimensions(info['path'])
        original=self.source/self.kernel_relative
        text=original.read_text()
        if hashlib.sha256(subprocess.check_output(['git','-C',self.source,'show','HEAD:'+self.kernel_relative])).hexdigest()!=fast.digest(original):
            raise ValueError('kernel differs from committed baseline')
        (self.root/f'baseline-{self.tag}.cpp').write_text(text)
        candidate=self.root/f'candidate-{self.tag}.cpp'; candidate.write_text(self.generate(text))
        import difflib
        (self.root/f'candidate-{self.tag}.patch').write_text(''.join(difflib.unified_diff(text.splitlines(True),candidate.read_text().splitlines(True),
            fromfile='a/'+self.kernel_relative,tofile='b/'+self.kernel_relative)))
        recipes=subprocess.check_output(['ninja','-C',self.build,'-t','commands','bin/libggml-cpu.so.0.16.0'],text=True).splitlines()
        compile_line=next(s for s in recipes if ' -c '+str(original) in s)
        link_line=next(s for s in recipes if ' -shared ' in s and ' -o bin/libggml-cpu.so.0.16.0 ' in s)
        overlay=self.root/'lib'; overlay.mkdir()
        obj=self.root/f'candidate-{self.tag}.o'; library=overlay/'libggml-cpu.so.0.16.0'
        c=compile_argv(compile_line,candidate,obj,original.parent); l=link_argv(link_line,library,obj,'/'+original.name+'.o')
        original_objects=[self.build/p for p in shlex.split(link_line.split(' && ')[1]) if p.endswith('.o')]
        object_hashes={str(p):fast.digest(p) for p in original_objects}
        self.command(c,'compile.log',180,cwd=self.build); self.command(l,'link.log',120,cwd=self.build)
        for name in ('libggml-cpu.so','libggml-cpu.so.0'): (overlay/name).symlink_to(library.name)
        self.env=dict(os.environ,LD_LIBRARY_PATH=str(overlay)+':'+self.expected['runtime']['LD_LIBRARY_PATH'],SPINE_FA_WIDE_TILE='1',SPINE_FA_K1_LAYOUT='0')
        tool=c[0]
        self.command([tool,'-O3','-std=c++17','-march=rv64gcv_zfh_zvfh_zicbop_zihintpause_zba','-mabi=lp64d',
            '-I'+str(self.source/'ggml/include'),'-I'+str(original.parent),HERE/self.harness,'-L'+str(overlay),
            '-L'+str(self.server.parent),'-lggml-cpu','-lggml-base','-pthread','-o',self.root/self.binary],
            'harness-build.log',120,env=self.env)
        self.provenance={'source_revision':'a990751','baseline_kernel_sha256':fast.digest(original),
            'candidate_source_sha256':fast.digest(candidate),'candidate_library_sha256':fast.digest(library),
            'original_object_sha256':object_hashes,'compile':c,'link':l,'models':self.expected['models'],
            'shapes':self.shapes,'code_sha256':{p.name:fast.digest(p) for p in HERE.iterdir() if p.suffix in ('.py','.cpp','.sh')},
            'settings':{'threads':4,'batch':32,'ubatch':32,'kv':'f16','attention_layout':0,'output_tokens':1},
            'runtime':{k:v for k,v in self.env.items() if k.startswith('SPINE_') or k=='LD_LIBRARY_PATH'}}
        fast.write_json(self.root/'provenance.json',self.provenance)
    def native(self):
        self.phase('native numerical gate')
        self.command([self.root/'test-ime'],'numeric.log',120,self.env)
        if 'PASS: 288 cases;' not in (self.root/'numeric.log').read_text(): raise ValueError('numerical gate incomplete')
        self.summary['stages']['numeric']={'cases':288,'bitwise_equal':True,'modes':[1,2,3,4,5],
            'scalar_m4_reference':True}; self.save()
        self.phase('operator timing')
        ks=sorted({v for s in self.shapes.values() for v in s.values()})
        log=self.root/'operator.jsonl'
        with log.open('w') as output, (self.root/'operator.err').open('w') as err:
            subprocess.run([str(self.root/'test-ime'),'--bench',*map(str,ks)],stdout=output,stderr=err,
                           check=True,timeout=300,env=self.env)
        rows=[json.loads(l) for l in log.read_text().splitlines()]
        expected={(k,n,b,m) for k in ks for n in (16,32) for b in range(6) for m in (0,4,5)}
        if len(rows)!=len(expected) or {(r['k'],r['n'],r['block'],r['mode']) for r in rows}!=expected:
            raise ValueError('missing operator arms')
        if any(r['slowest_ms']<50 or r['cpus']!=[0,1,2,3] or not math.isfinite(r['ms_per_call']) or r['ms_per_call']<=0 for r in rows):
            raise ValueError('invalid timing')
        comparisons=[]
        for k in ks:
            for n in (16,32):
                arm={m:[r['ms_per_call'] for r in rows if (r['k'],r['n'],r['mode'])==(k,n,m)] for m in (0,4,5)}
                for mode in (4,5): comparisons.append({'k':k,'n':n,'mode':mode,**fast.gate(arm[0],arm[mode])})
        self.summary['stages']['operators']={'records':len(rows),'comparisons':comparisons}; self.save()
        eligible=[]
        for mode in (4,5):
            c=[r for r in comparisons if r['mode']==mode]
            if not any(r['clear_regression'] for r in c) and sum(r['advance'] for r in c)>=2:
                eligible.append((statistics.mean(r['reduction_pct'] for r in c),mode))
        return max(eligible)[1] if eligible else None
    def model(self,model,tokens,winner):
        name=f'{model}-{tokens}'; self.phase('model '+name)
        rows=[]; labels=[]
        for i,mode in enumerate((0,winner,winner,0)):
            label=f'{model}-{tokens}-q{mode}-pass{i+1}'; out=self.root/(label+'.jsonl'); labels.append(label)
            env=dict(self.env,**{self.switch:str(mode)})
            self.command([sys.executable,HERE/'bench-lifecycle.py','--server',self.server,'--model',self.expected['models'][model]['path'],
                '--label',label,'--mode','plain','--contexts',tokens,'--n-predict',1,'--ignore-eos','--verify-cold',
                '--capture-token-ids','--gpu-layers',0,'--ctx-size',4096,'--timeout',600,'--output',out,
                '--log',self.root/(label+'.server.log')],label+'.driver.log',700,env)
            text=(self.root/(label+'.server.log')).read_text()
            self.activation(text,mode)
            if 'SPINE_FA_WIDE_TILE: RVV tiled attention enabled for 256-dim heads' not in text: raise ValueError('attention activation missing')
            rows += [json.loads(l) for l in out.read_text().splitlines()]
        requests=fast.check_model_records(rows,labels,tokens)
        arm={m:[r['results'][0] for r in requests if f'-q{m}-' in r['label']] for m in (0,winner)}
        comparison=fast.gate([r['timings']['prompt_ms'] for r in arm[0]],[r['timings']['prompt_ms'] for r in arm[winner]])
        comparison['ttft_ms']={str(m):[r['ttft_ms'] for r in values] for m,values in arm.items()}
        comparison.update(outputs_equal=True,uncached_verified=True,requests=4)
        self.summary['stages'][name]=comparison; self.save(); return comparison
    def run(self):
        try:
            self.prepare(); winner=self.native()
            if winner is None:
                self.summary.update(status='inconclusive',reason='No operator candidate meets benefit/no-regression gates; model tests skipped.')
            else:
                self.summary['winner']=winner
                first=self.model('2B',512,winner)
                if first['advance']:
                    second=self.model('2B',2048,winner)
                    if second['advance']:
                        third=self.model('4B',1024,winner)
                        self.summary.update(status='screen eligible' if third['advance'] else 'inconclusive',
                            reason='8k/quality confirmation remains.' if third['advance'] else '4B benefit gate failed; retain control.')
                    else: self.summary.update(status='inconclusive',reason='2B/2k benefit gate failed; retain control.')
                else: self.summary.update(status='inconclusive',reason='2B/512 benefit gate failed; retain control.')
            self.save(); self.phase(self.summary['status'])
        except BaseException as exc:
            self.summary.update(status='failed',reason=f'{type(exc).__name__}: {exc}'); self.save(); self.phase('failed'); raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('root',type=Path); args=p.parse_args()
    import signal
    def interrupted(signum,frame): raise TimeoutError('board budget expired')
    signal.signal(signal.SIGTERM,interrupted)
    Run(args.root.resolve()).run()
