#!/usr/bin/env python3
"""Build isolated channels-major SSM convolution and gate K1 model timing."""
import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shlex
import signal
import statistics
import subprocess
import sys

HERE = Path(__file__).resolve().parent
def module(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'))
    value=importlib.util.module_from_spec(spec); spec.loader.exec_module(value); return value
ime=module('k1-ime-test'); fast=ime.fast
patcher=module('make-k1-ssm-conv'); routing=module('make-k1-gemm-routing')
SOURCE_HASHES={
    'ggml/src/ggml-cpu/ops.cpp':'d03e80d18d117047b5f6cc007a277c80cab90e9d6c9f7f97ef4d8002db1a8192',
    'src/models/delta-net-base.cpp':'0120dd95d56d3eac0e0c3e2cd72af9cf13fc4f894022533d243d6577e5016f0d',
    'src/models/qwen35.cpp':'7643d4ce05ee44fa6f46b47436e82a2b7db171f04189a73fa5b2305fff82b30e',
}

def rewrite_link(line, output, replacements):
    segments=line.split(' && ')
    if len(segments)!=3 or segments[0]!=':' or segments[-1]!=':':
        raise ValueError('unexpected link recipe')
    args=shlex.split(segments[1]); counts={k:0 for k in replacements}
    for i, arg in enumerate(args):
        if i and args[i-1]=='-o': args[i]=str(output)
        for suffix, replacement in replacements.items():
            if arg.endswith(suffix):
                args[i]=str(replacement); counts[suffix]+=1
    if any(v!=1 for v in counts.values()): raise ValueError('link replacement not unique')
    return args

def check_marker(text, mode):
    expected=f'K1_SSM_CONV mode={mode} layout={"channels" if mode else "time"} rs=0 gpu=0'
    if expected not in text: raise ValueError('missing convolution activation: '+expected)

class Run(ime.Run):
    title='K1 channels-major SSM convolution screen'
    switch='SPINE_K1_SSM_CONV'
    def arm_env(self, mode, original=False):
        env=dict(self.env,SPINE_K1_SSM_CONV=str(mode),SPINE_K1_GEMM_ROUTE='3')
        if original: env['LD_LIBRARY_PATH']=self.expected['runtime']['LD_LIBRARY_PATH']
        return env

    def prepare(self):
        self.phase('verify and build isolated convolution libraries')
        self.server=next(Path(p) for p in self.expected['artifacts_sha256'] if p.endswith('/llama-server'))
        self.source=self.server.parents[2]; self.build=self.source/'build'
        if subprocess.check_output(['git','-C',self.source,'rev-parse','--short=7','HEAD'],text=True).strip()!='a990751':
            raise ValueError('baseline revision differs')
        changed=set(subprocess.check_output(['git','-C',self.source,'diff','HEAD','--name-only'],text=True).splitlines())
        if changed!=set(self.expected['source_sha256']): raise ValueError('unexpected source modifications')
        self.baseline_hashes={}
        for relative, digest in dict(self.expected['source_sha256'],**SOURCE_HASHES).items():
            if fast.digest(self.source/relative)!=digest: raise ValueError('baseline source changed: '+relative)
            self.baseline_hashes[str(self.source/relative)]=digest
        for path,digest in self.expected['artifacts_sha256'].items():
            if '/build/' in path or '/.toolchain/' in path or '/spert/' in path:
                if fast.digest(path)!=digest: raise ValueError('baseline artifact changed: '+path)
                self.baseline_hashes[path]=digest
        keys=('qwen35.ssm.inner_size','qwen35.ssm.state_size','qwen35.ssm.group_count','qwen35.ssm.conv_kernel')
        self.shapes={}
        for model, info in self.expected['models'].items():
            if fast.digest(info['path'])!=info['sha256']: raise ValueError('model changed')
            dims=ime.dimensions(info['path'],keys)
            self.shapes[model]={'channels':dims['inner_size']+2*dims['group_count']*dims['state_size'],'taps':dims['conv_kernel']}
        patcher.write_candidate(self.source,self.root)
        relative='ggml/src/ggml-cpu/spacemit/ime.cpp'
        route=self.root/'candidate'/relative; route.parent.mkdir(parents=True,exist_ok=True)
        route.write_text(routing.generate((self.source/relative).read_text()))
        overlay=self.root/'lib'; overlay.mkdir()
        compiled={}; commands=[]; recipes={}
        for target in ('bin/libggml-cpu.so.0.16.0','bin/libllama.so.0.0.7'):
            recipes[target]=subprocess.check_output(['ninja','-C',self.build,'-t','commands',target],text=True).splitlines()
        for relative in (*patcher.PATHS,'ggml/src/ggml-cpu/spacemit/ime.cpp'):
            original=self.source/relative; candidate=self.root/'candidate'/relative
            lines=[line for lines in recipes.values() for line in lines if ' -c '+str(original) in line]
            unique=list(dict.fromkeys(lines))
            if len(unique)!=1: raise ValueError('compile recipe not unique: '+relative)
            obj=self.root/(relative.replace('/','_')+'.o')
            argv=ime.compile_argv(unique[0],candidate,obj,original.parent)
            argv.insert(1,'-I'+str(HERE))
            self.command(argv,obj.stem+'.compile.log',600,cwd=self.build)
            compiled['/'+relative.split('/')[-1]+'.o']=obj; commands.append(argv)
        link_commands=[]
        for target, names in (('bin/libggml-cpu.so.0.16.0',('/ops.cpp.o','/ime.cpp.o')),
                              ('bin/libllama.so.0.0.7',('/delta-net-base.cpp.o','/qwen35.cpp.o'))):
            matches=[line for line in recipes[target] if ' -shared ' in line and ' -o '+target+' ' in line]
            if len(matches)!=1: raise ValueError('link recipe not unique')
            for arg in shlex.split(matches[0].split(' && ')[1]):
                if arg.endswith('.o'):
                    path=self.build/arg; self.baseline_hashes[str(path)]=fast.digest(path)
            library=overlay/Path(target).name
            argv=rewrite_link(matches[0],library,{name:compiled[name] for name in names})
            self.command(argv,library.name+'.link.log',120,cwd=self.build); link_commands.append(argv)
        for name, version in (('libggml-cpu','0.16.0'),('libllama','0.0.7')):
            for suffix in ('.so','.so.0'): (overlay/(name+suffix)).symlink_to(name+'.so.'+version)
        self.env=dict(os.environ,LD_LIBRARY_PATH=str(overlay)+':'+self.expected['runtime']['LD_LIBRARY_PATH'],
            SPINE_FA_WIDE_TILE='1',SPINE_FA_K1_LAYOUT='0',SPINE_K1_GEMM_ROUTE='3')
        compiler=commands[0][0]
        for source, binary, libraries in (('test-k1-ssm-conv.cpp','test-ssm',['-lggml-cpu','-lggml-base']),
                                          ('test-k1-ssm-state.cpp','test-state',['-lllama','-lggml','-lggml-cpu','-lggml-base'])):
            argv=[compiler,'-O3','-std=c++17','-march=rv64gcv_zfh_zvfh_zicbop_zihintpause_zba','-mabi=lp64d',
                '-I'+str(HERE),'-I'+str(self.source/'include'),'-I'+str(self.source/'ggml/include'),
                HERE/source,'-L'+str(overlay),'-L'+str(self.server.parent),*libraries,'-pthread','-o',self.root/binary]
            self.command(argv,binary+'.build.log',120,env=self.env)
        self.provenance={'source_revision':'a990751','source_hashes':SOURCE_HASHES,'models':self.expected['models'],
            'shapes':self.shapes,'compile':commands,'link':link_commands,'baseline_files_sha256':self.baseline_hashes,
            'candidate_library_sha256':{p.name:fast.digest(p) for p in overlay.iterdir() if not p.is_symlink()},
            'code_sha256':{p.name:fast.digest(p) for p in HERE.iterdir() if p.suffix in ('.h','.py','.cpp','.sh')},
            'runtime':{k:v for k,v in self.env.items() if k.startswith('SPINE_') or k=='LD_LIBRARY_PATH'},
            'settings':{'threads':4,'ubatch':32,'kv':'f16','rs':0,'gpu_layers':0,'routing':3,'mtp':False}}
        fast.write_json(self.root/'provenance.json',self.provenance)
        # Keep disassembly evidence for actual instruction selection.
        self.command(['objdump','-d','-C',self.root/'ggml_src_ggml-cpu_ops.cpp.o'],'candidate-ops-assembly.txt',60)

    def native(self):
        self.phase('convolution graph correctness')
        hashes={}
        for mode in (-1,0,1,2):
            label=f'numeric-{mode}'; dump=self.root/(label+'.bin')
            self.command([self.root/'test-ssm',max(mode,0),'--dump',dump],label+'.log',600,self.arm_env(max(mode,0),mode==-1))
            if 'PASS: 432 convolution graph cases;' not in (self.root/(label+'.log')).read_text():
                raise ValueError('native correctness incomplete')
            hashes[str(mode)]=fast.digest(dump); dump.unlink()
        if len(set(hashes.values()))!=1: raise ValueError('original/control/scalar/RVV outputs or state differ')
        self.summary['stages']['numeric']={'cases_per_arm':432,'sha256':hashes,'bitwise_equal':True}; self.save()
        self.phase('convolution graph operator timing')
        rows=[]
        for block in range(6):
            for model,shape in self.shapes.items():
                for tokens in (1,32):
                    for mode in ((0,1,2) if block%2==0 else (2,1,0)):
                        name=f'op-{model}-t{tokens}-b{block}-m{mode}'
                        self.command([self.root/'test-ssm','--bench',mode,shape['channels'],shape['taps'],tokens,1],name+'.log',30,self.arm_env(mode))
                        records=[json.loads(line) for line in (self.root/(name+'.log')).read_text().splitlines() if line.startswith('{')]
                        if len(records)!=1: raise ValueError('operator timing count')
                        r=records[0]
                        if r['wall_ms']<200 or not math.isfinite(r['ms_per_call']) or r['ms_per_call']<=0:
                            raise ValueError('invalid operator timing')
                        if (r['mode'],r['channels'],r['taps'],r['tokens'],r['sequences'])!=(mode,shape['channels'],shape['taps'],tokens,1):
                            raise ValueError('operator timing shape mismatch')
                        rows.append(dict(r,model=model,block=block))
                        (self.root/'operator.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
        comparisons=[]
        for model in self.shapes:
            for tokens in (1,32):
                arms={mode:[r['ms_per_call'] for r in rows if (r['model'],r['tokens'],r['mode'])==(model,tokens,mode)] for mode in (0,1,2)}
                for mode in (1,2): comparisons.append(dict(model=model,tokens=tokens,mode=mode,**fast.gate(arms[0],arms[mode])))
        self.summary['stages']['operators']={'records':len(rows),'comparisons':comparisons}; self.save()
        eligible=[]
        for mode in (1,2):
            comparisons_mode=[c for c in comparisons if c['mode']==mode]
            if not any(c['clear_regression'] for c in comparisons_mode) and sum(c['advance'] for c in comparisons_mode)>=2:
                eligible.append((statistics.mean(c['reduction_pct'] for c in comparisons_mode),mode))
        return max(eligible)[1] if eligible else None

    def state(self, mode):
        self.phase('full-model chunk/decode/reset state gate')
        for model, info in self.expected['models'].items():
            label=f'state-{model}-m{mode}'
            self.command([self.root/'test-state',info['path'],mode],label+'.log',900,self.arm_env(mode))
            text=(self.root/(label+'.log')).read_text(); check_marker(text,0); check_marker(text,mode)
            if 'K1_SSM_CONV mode=0 layout=time rs=3 gpu=0' not in text:
                raise ValueError('RS fallback activation missing')
            records=[json.loads(line) for line in text.splitlines() if line.startswith('{')]
            if len(records)!=16 or not all(r['bitwise_equal'] for r in records): raise ValueError('state gate incomplete')
            self.summary['stages'][label]={'comparisons':16,'bitwise_equal':True,'rs3_reference_fallback':True}; self.save()

    def model_pair(self, model, tokens, mode):
        label=f'{model}-p{tokens}'; self.phase('model '+label)
        rows=[]; labels=[]
        for repeat, arm in enumerate((0,mode,mode,0)):
            name=f'{label}-q{arm}-r{repeat}'; labels.append(name)
            self.command([sys.executable,HERE/'bench-lifecycle.py','--server',self.server,'--model',self.expected['models'][model]['path'],
                '--label',name,'--mode','plain','--contexts',tokens,'--n-predict',64,'--ignore-eos','--verify-cold',
                '--capture-token-ids','--gpu-layers',0,'--ctx-size',4096,'--timeout',600,
                '--output',self.root/(name+'.jsonl'),'--log',self.root/(name+'.server.log')],name+'.driver.log',700,self.arm_env(arm))
            text=(self.root/(name+'.server.log')).read_text(); check_marker(text,arm)
            if 'K1_GEMM_ROUTE mode=3' not in text or 'SPINE_FA_WIDE_TILE: RVV tiled attention enabled for 256-dim heads' not in text:
                raise ValueError('existing optimization activation missing')
            rows.extend(json.loads(line) for line in (self.root/(name+'.jsonl')).read_text().splitlines())
            self.summary['requests_completed']=self.summary.get('requests_completed',0)+1; self.save()
        requests=fast.check_model_records(rows,labels,tokens,64)
        arms={arm:[r['results'][0] for r in requests if f'-q{arm}-' in r['label']] for arm in (0,mode)}
        if any(r['timings'].get('predicted_n')!=64 or r['timings'].get('predicted_ms',0)<=0 for values in arms.values() for r in values):
            raise ValueError('invalid decode timing')
        comparison={phase:fast.gate([r['timings'][key] for r in arms[0]],[r['timings'][key] for r in arms[mode]])
                    for phase,key in (('prefill','prompt_ms'),('decode','predicted_ms'))}
        comparison.update(outputs_equal=True,uncached_verified=True,requests=4,output_tokens=64)
        self.summary['stages'][label]=comparison; self.save()
        return comparison['prefill']['advance'] and not comparison['decode']['clear_regression']

    def run(self):
        try:
            self.summary.update(requests_completed=0,requests_planned_max=16,
                limitations='Warm graph operator screen followed by cold ABBA capped timing. Same route 3, precision and full prompts. No useful-answer, GPU or RS-rollback qualification; default unchanged.')
            self.prepare(); mode=self.native()
            if mode is None:
                self.summary.update(status='inconclusive',reason='Operator gate failed; model timing skipped.')
            else:
                self.summary['winner']=mode; self.save(); self.state(mode)
                passed=True
                for model,tokens in (('2B',256),('2B',2048),('4B',256),('4B',2048)):
                    if not self.model_pair(model,tokens,mode): passed=False; break
                self.summary.update(status='screen eligible' if passed else 'inconclusive',
                    reason='All bounded timing gates pass; complete-answer confirmation remains.' if passed else 'Whole-model benefit/no-regression gate failed; retain reference.')
            self.phase('verify preserved baseline')
            for path,digest in self.baseline_hashes.items():
                if fast.digest(path)!=digest: raise ValueError('baseline changed during run: '+path)
            self.summary['baseline_preserved']=True; self.save(); self.phase(self.summary['status'])
        except BaseException as e:
            self.summary.update(status='failed',reason=f'{type(e).__name__}: {e}'); self.save(); self.phase('failed'); raise

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('root',type=Path); args=p.parse_args()
    def interrupted(signum,frame): raise TimeoutError('board budget expired')
    signal.signal(signal.SIGTERM,interrupted); Run(args.root.resolve()).run()
