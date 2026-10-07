#!/usr/bin/env python3
"""Gate fixed K32 M1 specialization against the preserved route-3 library."""
import argparse
import json
import math
from pathlib import Path
import signal
import sys

HERE = Path(__file__).resolve().parent
import importlib.util


def module(name):
    spec = importlib.util.spec_from_file_location(name, HERE/(name+'.py'))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


ime = module('k1-ime-test'); fast = ime.fast
patcher = module('make-k1-ime-m1-k32'); routing = module('k1-gemm-routing')


class Run(ime.Run):
    tag = 'ime-m1-k32'
    harness = 'test-k1-ime-m1.cpp'
    binary = 'test-ime-m1'
    switch = 'SPINE_IME_M1_K32'
    title = 'K1 fixed K32 M1 specialization'
    compile_timeout = 600

    def generate(self, text):
        return patcher.generate(text)

    def arm_env(self, mode):
        env = dict(self.env, SPINE_K1_GEMM_ROUTE='3', SPINE_IME_M1_K32=str(max(mode, 0)))
        if mode == -1:
            env['LD_LIBRARY_PATH'] = self.route['runtime']['LD_LIBRARY_PATH']
        return env

    def activation(self, text, mode, phases=('single',)):
        routing.check_activation(text, 3, phases)
        marker = 'SPINE_IME_M1_K32:'
        if mode == -1:
            if marker in text: raise ValueError('preserved baseline has a new M1 marker')
        elif 'single' in phases and f'{marker} mode={mode} Q4_0 M1 K32 enabled' not in text:
            raise ValueError('M1 candidate/control activation missing')

    def prepare(self):
        self.route = json.loads((self.root/'routing-provenance.json').read_text())
        self.base_library = Path(self.route['link'][self.route['link'].index('-o')+1])
        if fast.digest(self.base_library) != self.route['candidate_library_sha256']:
            raise ValueError('preserved route-3 library changed')
        for name, digest in self.route['original_object_sha256'].items():
            if fast.digest(name) != digest: raise ValueError('preserved base object changed: '+name)
        route_source = Path(self.route['compile'][self.route['compile'].index('-c')+1])
        if fast.digest(route_source) != self.route['candidate_source_sha256']:
            raise ValueError('route-3 source changed')
        super().prepare()
        # Validate the whole saved link recipe, including the route object, by
        # recreating the immutable route-3 library before replacing just M1.
        baseline_link = list(self.route['link'])
        rebuilt = self.root/'route3-relinked.so'
        baseline_link[baseline_link.index('-o')+1] = str(rebuilt)
        self.command(baseline_link, 'baseline-relink.log', 120, cwd=self.build)
        if fast.digest(rebuilt) != self.route['candidate_library_sha256']:
            raise ValueError('route object/link recipe does not reproduce preserved library')
        link = list(self.route['link'])
        link[link.index('-o')+1] = str(self.root/'lib/libggml-cpu.so.0.16.0')
        indices = [i for i, arg in enumerate(link) if arg.endswith('/spacemit/ime1_kernels.cpp.o')]
        if len(indices) != 1: raise ValueError('M1 object replacement is not unique')
        link[indices[0]] = str(self.root/'candidate-ime-m1-k32.o')
        self.command(link, 'route3-candidate-link.log', 120, cwd=self.build)
        tool = self.provenance['compile'][0]
        common = [tool, '-O3', '-std=c++17', '-march=rv64gcv_zfh_zvfh_zicbop_zihintpause_zba', '-mabi=lp64d',
                  '-I'+str(self.source/'ggml/include'), '-I'+str(self.source/'ggml/src'),
                  '-I'+str(self.source/'ggml/src/ggml-cpu/spacemit'), '-I'+str(self.source/'include'),
                  '-L'+str(self.root/'lib'), '-L'+str(self.server.parent)]
        for source, binary, libs in (
                ('test-k1-ime-m1-graph.cpp', 'test-m1-graph', ['-lggml-cpu','-lggml-base']),
                ('test-k1-ime-m1-state.cpp', 'test-m1-state', ['-lllama','-lggml','-lggml-cpu','-lggml-base'])):
            self.command([*common, HERE/source, *libs, '-pthread', '-o', self.root/binary],
                         binary+'.build.log', 180, self.arm_env(0))
        # Save decoded machine code for verifying the fixed helper and preserved
        # original loop; missing stack frames are not used as absence evidence.
        objdump = Path(tool).with_name('objdump')
        if not objdump.exists(): objdump = Path('objdump')
        self.command([objdump, '-d', '-C', self.root/'candidate-ime-m1-k32.o'], 'assembly.txt', 120)
        self.provenance.update(link=link, candidate_library_sha256=fast.digest(self.root/'lib/libggml-cpu.so.0.16.0'),
            baseline_route3_library={'path':str(self.base_library),'sha256':fast.digest(self.base_library)},
            baseline_relink_sha256=fast.digest(rebuilt),
            linked_object_sha256={str((self.build/arg).resolve()):fast.digest(self.build/arg) for arg in link if arg.endswith('.o')},
            settings={'threads':4,'batch':32,'ubatch':32,'kv':'f16','attention_layout':0,'route':3,
                      'mtp':False,'seed':42,'temperature':0,'output_tokens':64},
            runtime={k:v for k,v in self.arm_env(0).items() if k.startswith('SPINE_') or k=='LD_LIBRARY_PATH'})
        fast.write_json(self.root/'provenance.json', self.provenance)

    def numerical(self):
        self.phase('raw M1 scalar and fallback correctness')
        self.command([self.root/self.binary], 'raw-numeric.log', 180, self.arm_env(0))
        if 'PASS: 480 cases;' not in (self.root/'raw-numeric.log').read_text():
            raise ValueError('raw numerical gate incomplete')
        self.summary['stages']['raw_numeric'] = dict(cases=480, bitwise_equal=True,
            checks='M1 Q4_0 scalar reference; K32/K64, M1/2/3/4/7, zero points, N tails, input and output guards')
        self.save(); self.phase('production graph and full vocabulary correctness')
        hashes = {}
        shapes = []
        for model, dims in self.shapes.items():
            e, f = dims['embedding_length'], dims['feed_forward_length']
            shapes.extend([(model,1,e,f),(model,1,f,e),(model,1,e,248320)])
        for mode in (-1,0,1):
            name = f'graph-{mode}'
            self.command([self.root/'test-m1-graph','--dump',self.root/(name+'.data')], name+'.log', 240, self.arm_env(mode))
            if 'PASS: 104 production graph cases;' not in (self.root/(name+'.log')).read_text():
                raise ValueError('production graph cases incomplete')
            self.activation((self.root/(name+'.log')).read_text(), mode, ('single','prefill'))
            hashes[str(mode)] = fast.digest(self.root/(name+'.data'))
        if len(set(hashes.values())) != 1: raise ValueError('production outputs differ')
        full = []
        for model,m,k,n in shapes:
            digests = {}
            for mode in (-1,0,1):
                name=f'full-{model}-k{k}-n{n}-q{mode}'
                self.command([self.root/'test-m1-graph','--dump-shape',self.root/(name+'.data'),m,k,n],
                             name+'.log', 300, self.arm_env(mode))
                self.activation((self.root/(name+'.log')).read_text(), mode)
                if (self.root/(name+'.data')).stat().st_size != n*4: raise ValueError('full output missing')
                digests[str(mode)] = fast.digest(self.root/(name+'.data'))
            if len(set(digests.values())) != 1: raise ValueError('actual FFN/full-vocabulary outputs differ')
            full.append(dict(model=model,m=m,k=k,n=n,sha256=digests))
        self.summary['stages']['production_numeric'] = dict(cases_per_arm=104,arms=[-1,0,1],
            bitwise_equal=True,sha256=hashes,full_shape_checks=full)
        self.save(); return shapes

    def operators(self, shapes):
        self.phase('repeated production operators')
        shapes = shapes + [(model,32,d['embedding_length'],d['feed_forward_length']) for model,d in self.shapes.items()]
        rows=[]
        for block in range(6):
            for model,m,k,n in shapes:
                for mode in ((-1,0,1) if block%2==0 else (1,0,-1)):
                    name=f'op-{model}-m{m}-k{k}-n{n}-b{block}-q{mode}'
                    self.command([self.root/'test-m1-graph','--bench',m,k,n],name+'.log',300,self.arm_env(mode))
                    text=(self.root/(name+'.log')).read_text()
                    self.activation(text,mode,('single',) if m==1 else ('prefill',))
                    found=[json.loads(line) for line in text.splitlines() if line.startswith('{')]
                    if len(found)!=1: raise ValueError('operator measurement missing/extra')
                    r=found[0]
                    if (r['m'],r['k'],r['n'])!=(m,k,n) or r['wall_ms']<100 or not math.isfinite(r['ms_per_call']) or r['ms_per_call']<=0:
                        raise ValueError('invalid operator timing')
                    rows.append(dict(r,model=model,block=block,mode=mode))
                    (self.root/'operator.jsonl').write_text(''.join(json.dumps(v)+'\n' for v in rows))
        comparisons=[]; controls=[]
        for model,m,k,n in shapes:
            arms={mode:[r['ms_per_call'] for r in rows if (r['model'],r['m'],r['k'],r['n'],r['mode'])==(model,m,k,n,mode)] for mode in (-1,0,1)}
            if any(len(a)!=6 for a in arms.values()): raise ValueError('operator arms incomplete')
            ident=dict(model=model,m=m,k=k,n=n)
            comparisons.append(dict(ident,**fast.gate(arms[0],arms[1])))
            controls.append(dict(ident,**fast.gate(arms[-1],arms[0])))
        self.summary['stages']['operators']=dict(records=len(rows),comparisons=comparisons,original_control_checks=controls)
        self.save()
        # Each model needs at least one actual M1 win. All shapes, including the
        # complete output head and unchanged M32 path, must avoid clear loss.
        return (not any(r['clear_regression'] for r in comparisons+controls)
                and all(any(r['advance'] and r['m']==1 and r['model']==model for r in comparisons) for model in self.shapes))

    def state(self):
        self.phase('full vocabulary mixed chunk and reset state')
        results=[]
        for model, info in self.expected['models'].items():
            hashes={}
            for mode in (-1,0,1):
                name=f'state-{model}-q{mode}'
                self.command([self.root/'test-m1-state',info['path'],self.root/(name+'.data')],name+'.log',1800,self.arm_env(mode))
                text=(self.root/(name+'.log')).read_text(); self.activation(text,mode,('single','prefill'))
                if 'PASS: 16 full-vocabulary snapshots;' not in text: raise ValueError('state snapshots incomplete')
                records=[json.loads(line) for line in text.splitlines() if line.startswith('{')]
                if len(records)!=16 or any(r['vocab']!=248320 for r in records): raise ValueError('state vocabulary/count wrong')
                if (self.root/(name+'.data')).stat().st_size!=16*248320*4: raise ValueError('state dump truncated')
                hashes[str(mode)]=fast.digest(self.root/(name+'.data'))
            if len(set(hashes.values()))!=1: raise ValueError('mixed chunk/reset/RS logits differ')
            results.append(dict(model=model,comparisons=16,sha256=hashes,bitwise_equal=True))
        self.summary['stages']['state']=results; self.save()

    def decode(self, model, tokens):
        name=f'{model}-{tokens}-decode64'; self.phase('cold model ABBA '+name)
        rows=[]; labels=[]
        for i,mode in enumerate((0,1,1,0)):
            label=f'{name}-q{mode}-pass{i+1}'; labels.append(label)
            self.command([sys.executable,HERE/'bench-lifecycle.py','--server',self.server,'--model',self.expected['models'][model]['path'],
                '--label',label,'--mode','plain','--contexts',tokens,'--n-predict',64,'--ignore-eos','--verify-cold',
                '--capture-token-ids','--gpu-layers',0,'--ctx-size',4096,'--timeout',1500,
                '--output',self.root/(label+'.jsonl'),'--log',self.root/(label+'.server.log')],label+'.driver.log',1600,self.arm_env(mode))
            text=(self.root/(label+'.server.log')).read_text(); self.activation(text,mode,('prefill','single'))
            if 'SPINE_FA_WIDE_TILE: RVV tiled attention enabled for 256-dim heads' not in text:
                raise ValueError('wide attention activation missing')
            rows.extend(json.loads(line) for line in (self.root/(label+'.jsonl')).read_text().splitlines())
        requests=fast.check_model_records(rows,labels,tokens,output_tokens=64)
        arms={mode:[r['results'][0] for r in requests if f'-q{mode}-' in r['label']] for mode in (0,1)}
        if any(r['timings'].get('predicted_n')!=64 or r['timings'].get('predicted_ms',0)<=0 for values in arms.values() for r in values):
            raise ValueError('sustained decode timing incomplete')
        result=fast.gate([r['timings']['predicted_ms'] for r in arms[0]],[r['timings']['predicted_ms'] for r in arms[1]])
        result.update(outputs_equal=True,uncached_verified=True,requests=4,output_tokens=64,
            prefill_check=fast.gate([r['timings']['prompt_ms'] for r in arms[0]],[r['timings']['prompt_ms'] for r in arms[1]]),
            rates={str(mode):{'decode_tps':[r['timings']['predicted_per_second'] for r in arm],
                             'prefill_tps':[r['timings']['prompt_per_second'] for r in arm]} for mode,arm in arms.items()})
        self.summary['stages'][name]=result; self.save(); return result

    def run(self):
        self.summary['limitations']='One fixed K32 M1 specialization only. Repeated production operators are warm; cold ABBA uses complete prompts and 64 capped tokens, which does not establish useful-answer speedup. RS reference behavior is not rollback qualification. No production defaults changed.'
        try:
            self.prepare(); shapes=self.numerical()
            if not self.operators(shapes):
                self.summary.update(status='inconclusive',reason='Operator/control gates did not justify long model tests; candidate remains disabled.')
            else:
                self.state()
                pilots=[self.decode(model,256) for model in ('2B','4B')]
                if all(r['advance'] and not r['prefill_check']['clear_regression'] for r in pilots):
                    long=[self.decode(model,2048) for model in ('2B','4B')]
                    eligible=all(r['advance'] and not r['prefill_check']['clear_regression'] for r in long)
                    self.summary.update(status='screen eligible' if eligible else 'inconclusive',
                        reason='Naturally complete useful-answer qualification remains; retain opt-in.' if eligible else 'Long-context model gate failed; candidate remains disabled.')
                else:
                    self.summary.update(status='inconclusive',reason='256-token model benefit/control-spread gate failed; long-context and quality skipped.')
            self.save(); self.phase(self.summary['status'])
        except BaseException as exc:
            self.summary.update(status='failed',reason=f'{type(exc).__name__}: {exc}'); self.save(); self.phase('failed'); raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('root',type=Path)
    args=parser.parse_args()
    def interrupted(signum,frame): raise TimeoutError('board budget expired')
    signal.signal(signal.SIGTERM,interrupted); Run(args.root.resolve()).run()
