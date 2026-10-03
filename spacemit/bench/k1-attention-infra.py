#!/usr/bin/env python3
"""Attribute long-history attention and gate independent exact layout candidates."""
import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import statistics
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
def module(name):
    s = importlib.util.spec_from_file_location(name, HERE / (name + '.py'))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
ime, patcher = module('k1-ime-test'), module('make-k1-attention-infra')
fast = ime.fast
STAGES = ('setup_q', 'scratch_mask', 'k_pack', 'qk', 'softmax', 'v_pack', 'pv', 'output')
ORDERS = ((-1, 0, 1, 2), (2, 1, 0, -1), (0, 2, -1, 1),
          (1, -1, 2, 0), (-1, 1, 0, 2), (2, 0, 1, -1))


def parse_operator(text, mode, profile, block, shape, history, mask):
    rows = [json.loads(line) for line in text.splitlines() if line.startswith('{')]
    if len(rows) != 1: raise ValueError('expected exactly one operator record')
    row = rows[0]
    if (row['mode'], row['profile'], row['block'], row['heads'], row['kv_heads'], row['kv_rows'], row['mask']) != (
            max(mode, 0), profile, block, shape['heads'], shape['kv_heads'], history, mask):
        raise ValueError('operator shape/arm mismatch')
    if row['cpus'] != [0, 1, 2, 3] or row['slowest_ms'] < 100 or not math.isfinite(row['ms_per_call']) or row['ms_per_call'] <= 0:
        raise ValueError('invalid operator timing')
    if len(row['stage_sum_ns']) != 8 or any(not math.isfinite(v) or v < 0 for v in row['stage_sum_ns']):
        raise ValueError('invalid stage timing')
    if profile and sum(row['stage_sum_ns']) <= 0: raise ValueError('profile API unavailable')
    if not profile and any(row['stage_sum_ns']): raise ValueError('timers unexpectedly enabled')
    row['mode'] = mode
    return row


def choose(comparisons, eligible_modes):
    qualified = []
    for mode in eligible_modes:
        c = [v for v in comparisons if v['mode'] == mode]
        long_c = [v for v in c if v['history'] >= 8192 and v['mask'] == 1]
        if len(long_c) != 4: raise ValueError('missing long causal shapes')
        if sum(v['advance'] for v in long_c) >= 2 and not any(v['clear_regression'] for v in c):
            qualified.append((statistics.mean(v['reduction_pct'] for v in long_c), mode))
    return max(qualified)[1] if qualified else None


class Run(ime.Run):
    verified_modified_kernel = True
    compile_timeout = 480
    kernel_relative = 'ggml/src/ggml-cpu/spacemit/rvv_kernels.cpp'
    tag = 'attention-infra'
    harness = 'test-k1-attention-infra.cpp'
    binary = 'test-attention'
    switch = 'SPINE_FA_K1_INFRA'
    title = 'K1 attention infrastructure screen'
    def generate(self, text): return patcher.generate(text)
    def model_dimensions(self, path): return fast.model_shape(Path(path))
    def activation(self, text, mode):
        if f'SPINE_FA_K1_INFRA: mode={mode} profile=0 legacy Q64 KV64' not in text:
            raise ValueError('attention activation missing')
    def prepare(self):
        super().prepare()
        self.env.update(SPINE_FA_K1_PROFILE='0', SPINE_FA_K1_INFRA='0')
        self.summary['limitations'] = ('Infrastructure-only: unchanged full prompts/model/quantization. '
            'Stage timings are summed active worker time in isolated attention calls, not full-model wall shares. '
            'Repeated deterministic DDR tensors; no production SPERT synchronization in the operator harness. '
            'Model screens are pilots with one generated token; no significance, decode or quality claim.')
        self.provenance['protocol'] = {'operator_histories': [2048,8192,16384], 'blocks': 6,
            'promotion': '>=2 long causal shapes above max(3%,control range), no clear shape regression',
            'attribution': 'direct V if V pack >=1%; QK grouping if QK >=20%, averaged over long causal shapes',
            'model_stages': ['2B/2048 ABBA','4B/1024 ABBA','conditional 2B/8192 AB','conditional 4B/8192 BA'],
            'old_control_gate': 'no clear regression against original library on any operator shape',
            'long_context_limit': 12288, 'timer_stage_names': STAGES}
        fast.write_json(self.root/'provenance.json', self.provenance)
    def original_env(self):
        return dict(self.env, LD_LIBRARY_PATH=self.expected['runtime']['LD_LIBRARY_PATH'])
    def runtime(self):
        self.phase('runtime geometry and production buffer audit')
        lib = next(Path(p) for p in self.expected['artifacts_sha256'] if p.endswith('/libspine_tcm.so'))
        self.command([sys.executable,HERE/'audit-k1-runtime.py',lib], 'runtime-audit.log',60,self.env)
        info = json.loads((self.root/'runtime-audit.log').read_text())
        fast.write_json(self.root/'runtime-audit.json', info)
        label = 'runtime-2B-32'; env = dict(self.original_env(),SPINE_TCM_DEBUG='1')
        self.command([sys.executable,HERE/'bench-lifecycle.py','--server',self.server,'--model',self.expected['models']['2B']['path'],
            '--label',label,'--mode','plain','--contexts',32,'--n-predict',1,'--ignore-eos','--verify-cold',
            '--capture-token-ids','--gpu-layers',0,'--ctx-size',4096,'--timeout',120,
            '--output',self.root/(label+'.jsonl'),'--log',self.root/(label+'.server.log')],label+'.driver.log',180,env)
        records = [json.loads(l) for l in (self.root/(label+'.jsonl')).read_text().splitlines()]
        fast.check_model_records(records,[label],32)
        log = (self.root/(label+'.server.log')).read_text()
        buffers = [line for line in log.splitlines() if '[tcmdbg]' in line]
        if not buffers: raise ValueError('production TCM buffer probe did not activate')
        self.summary['stages']['runtime'] = {'geometry':info['tcm'], 'production_buffer_records':buffers,
            'barrier_heap_fallback':'falling back to heap' in log,
            'note':'Missing sync device and compute buffer availability are separate observations; no OS settings changed.'}
        self.save()
    def operator(self, model, history, mask, mode, block, profile=0):
        env = self.original_env() if mode == -1 else dict(self.env)
        env.update(SPINE_FA_K1_INFRA=str(max(mode,0)), SPINE_FA_K1_PROFILE=str(profile))
        shape = self.shapes[model]
        name = f'op-{model}-{history}-m{mask}-v{mode}-b{block}-p{profile}.log'
        self.command([self.root/self.binary,'--bench',block,shape['heads'],shape['kv_heads'],history,mask],name,60,env)
        row = parse_operator((self.root/name).read_text(),mode,profile,block,shape,history,mask)
        row['model'] = model
        return row
    def native(self):
        self.phase('attention numerical gate against original library')
        hashes = {}
        for mode in (-1,0,1,2):
            env = self.original_env() if mode == -1 else dict(self.env)
            env.update(SPINE_FA_K1_INFRA=str(max(mode,0)),SPINE_FA_K1_PROFILE='0')
            self.command([self.root/self.binary,self.root/f'numeric-{mode}.bin'],f'numeric-{mode}.log',180,env)
            if 'PASS: 289 concurrent cases;' not in (self.root/f'numeric-{mode}.log').read_text():
                raise ValueError('numerical gate incomplete')
            hashes[str(mode)] = fast.digest(self.root/f'numeric-{mode}.bin')
        if len(set(hashes.values())) != 1: raise ValueError('attention output differs from original library')
        self.summary['stages']['numeric'] = {'cases_per_arm':289,'output_sha256':hashes,'bitwise_equal':True,
            'checks':'inputs/output/scratch guards, NaN padding, masks, strides, sinks/softcap, grouped heads and sequences'}
        self.save()
        self.phase('attention stage attribution at 2k 8k 16k')
        profiles = []
        with (self.root/'attribution.jsonl').open('w') as out:
            for model in self.shapes:
                for history in (2048,8192,16384):
                    for mask in (0,1):
                        row = self.operator(model,history,mask,0,0,1)
                        profiles.append(row); out.write(json.dumps(row)+'\n'); out.flush()
        long = [r for r in profiles if r['kv_rows'] >= 8192 and r['mask']==1]
        shares = {name:statistics.mean(r['stage_sum_ns'][i]/sum(r['stage_sum_ns']) for r in long)
                  for i,name in enumerate(STAGES)}
        modes = []
        if shares['v_pack'] >= .01: modes.append(1)
        if shares['qk'] >= .20: modes.append(2)
        self.summary['stages']['attribution'] = {'records':len(profiles),'long_causal_mean_active_time_shares':shares,
            'eligible_modes':modes,'stage_names':STAGES,'instrumented_diagnostic_only':True}
        self.save()
        if not modes: return None
        self.phase('uninstrumented attention operator comparisons')
        rows = []; deadline = time.monotonic()+600
        with (self.root/'operator.jsonl').open('w') as out:
            for block,order in enumerate(ORDERS):
                for model in self.shapes:
                    for history in (2048,8192,16384):
                        for mask in (0,1):
                            for mode in order:
                                if mode not in (-1,0,*modes): continue
                                if time.monotonic()>deadline: raise TimeoutError('operator budget exceeded')
                                row = self.operator(model,history,mask,mode,block)
                                rows.append(row); out.write(json.dumps(row)+'\n'); out.flush()
        comparisons = []; control_checks = []
        for model in self.shapes:
            for history in (2048,8192,16384):
                for mask in (0,1):
                    arm = {m:[r['ms_per_call'] for r in rows if (r['model'],r['kv_rows'],r['mask'],r['mode']) ==
                              (model,history,mask,m)] for m in (-1,0,*modes)}
                    if any(len(v)!=6 for v in arm.values()): raise ValueError('missing operator blocks')
                    common = {'model':model,'history':history,'mask':mask}
                    control_checks.append({**common,**fast.gate(arm[-1],arm[0])})
                    for mode in modes: comparisons.append({**common,'mode':mode,**fast.gate(arm[0],arm[mode])})
        self.summary['stages']['operators'] = {'records':len(rows),'comparisons':comparisons,
                                               'original_control_checks':control_checks}
        self.save()
        if any(c['clear_regression'] for c in control_checks):
            self.summary['reason'] = 'Instrument-free mode 0 regresses against original library; investigate control code generation.'
            return None
        return choose(comparisons,modes)
    def model(self,model,tokens,winner,long=False):
        name = f'{model}-{tokens}'; self.phase('model '+name)
        modes = (0,winner) if model=='2B' else (winner,0)
        if not long: modes = (0,winner,winner,0)
        rows = []; labels = []
        for i,mode in enumerate(modes):
            label = f'{model}-{tokens}-q{mode}-pass{i+1}'; labels.append(label)
            env = dict(self.env,SPINE_FA_K1_INFRA=str(mode),SPINE_FA_K1_PROFILE='0')
            timeout = 1800 if long else 600
            self.command([sys.executable,HERE/'bench-lifecycle.py','--server',self.server,'--model',self.expected['models'][model]['path'],
                '--label',label,'--mode','plain','--contexts',tokens,'--n-predict',1,'--ignore-eos','--verify-cold',
                '--capture-token-ids','--gpu-layers',0,'--ctx-size',12288 if long else 4096,'--timeout',timeout,
                '--output',self.root/(label+'.jsonl'),'--log',self.root/(label+'.server.log')],label+'.driver.log',timeout+100,env)
            log = (self.root/(label+'.server.log')).read_text(); self.activation(log,mode)
            if 'SPINE_FA_WIDE_TILE: RVV tiled attention enabled' not in log: raise ValueError('wide attention missing')
            rows.extend(json.loads(l) for l in (self.root/(label+'.jsonl')).read_text().splitlines())
        requests = fast.check_model_records(rows,labels,tokens)
        arm = {m:[r['results'][0] for r in requests if f'-q{m}-' in r['label']] for m in (0,winner)}
        values = {m:[r['timings']['prompt_ms'] for r in v] for m,v in arm.items()}
        if long:
            comparison = {'reduction_pct':100*(1-values[winner][0]/values[0][0]),'pilot_only':True,
                          'base_ms':values[0],'candidate_ms':values[winner]}
        else: comparison = fast.gate(values[0],values[winner])
        comparison.update(outputs_equal=True,uncached_verified=True,requests=len(modes),
            ttft_ms={str(m):[r['ttft_ms'] for r in v] for m,v in arm.items()})
        self.summary['stages'][name] = comparison; self.save(); return comparison
    def run(self):
        try:
            self.prepare(); self.runtime(); winner = self.native()
            if winner is None:
                self.summary.update(status='inconclusive',reason=self.summary.get('reason') or
                    'No candidate clears the predeclared long-history operator gates; model stages skipped.')
            else:
                self.summary['winner'] = winner
                first = self.model('2B',2048,winner)
                second = self.model('4B',1024,winner)
                if first['advance'] and second['advance']:
                    a = self.model('2B',8192,winner,True); b = self.model('4B',8192,winner,True)
                    self.summary.update(status='long pilot eligible' if min(a['reduction_pct'],b['reduction_pct'])>0 else 'inconclusive',
                        reason='Fresh independent replication and complete-answer validation required before adoption.')
                else: self.summary.update(status='inconclusive',reason='Short model gate failed; 8k and quality stages skipped.')
            self.save(); self.phase(self.summary['status'])
        except BaseException as exc:
            self.summary.update(status='failed',reason=f'{type(exc).__name__}: {exc}'); self.save(); self.phase('failed'); raise


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('root',type=Path); args=p.parse_args()
    def interrupted(signum,frame): raise TimeoutError('board budget expired')
    signal.signal(signal.SIGTERM,interrupted); Run(args.root.resolve()).run()
