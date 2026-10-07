#!/usr/bin/env python3
"""Hybrid SSM qualification followed by naturally stopped complete answers."""
import argparse
import hashlib
import json
import re
import signal
import socket
import statistics
import subprocess
import sys

from pathlib import Path
import importlib.util

HERE = Path(__file__).resolve().parent
def module(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + '.py'))
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result); return result
ssm = module('k1-ssm-conv')
pilot = module('mtp-quality')
fast, chat, checks = ssm.fast, pilot.chat, pilot.checks
MARKER = re.compile(r'K1_SSM_CONV mode=(\d) layout=(\w+) rs=(\d+) cpu_only=(\d+) tokens=(\d+) requested=(\d+)')

def audit_result(answer, payload, count):
    audit = pilot.audit_result(answer, payload, count)
    t = answer.get('timings', {})
    audit.update(draft_disabled=t.get('draft_n', 0) == 0,
                 positive_timings=t.get('prompt_ms', 0) > 0 and t.get('predicted_ms', 0) > 0)
    return audit

def check_activation(text, requested, require_both=True):
    rows = MARKER.findall(text)
    if not rows: raise ValueError('hybrid activation markers absent')
    seen = set()
    for mode, layout, rs, cpu, tokens, actual_requested in rows:
        tokens, mode = int(tokens), int(mode)
        selected = 2 if requested == 3 and tokens >= 32 and rs == '0' else 0
        if (mode, layout, cpu, int(actual_requested)) != (selected, 'channels' if selected else 'time', '1', requested):
            raise ValueError('hybrid graph dispatch differs from protocol')
        if rs == '0': seen.add((mode, tokens))
    if require_both and ((0, 1) not in seen or requested == 3 and (2, 32) not in seen):
        raise ValueError('prefill/decode graph activation incomplete')
    return {'markers':len(rows), 'selected_shapes':sorted(seen)}

class Run(ssm.Run):
    title = 'K1 hybrid SSM complete-answer pilot'

    def hybrid_native(self):
        self.phase('original/control/hybrid exact native graph gate')
        hashes = {}
        for name, mode, original in (('original',0,True),('control',0,False),('hybrid',3,False)):
            dump = self.root / ('numeric-' + name + '.bin')
            self.command([self.root/'test-ssm',mode,'--dump',dump], 'numeric-'+name+'.log',600,self.arm_env(mode,original))
            if 'PASS: 432 convolution graph cases;' not in (self.root/('numeric-'+name+'.log')).read_text():
                raise ValueError('native case count incomplete')
            hashes[name] = fast.digest(dump); dump.unlink()
        if len(set(hashes.values())) != 1: raise ValueError('native output or history identity failed')
        self.summary['stages']['numeric'] = {'cases_per_arm':432,'sha256':hashes,'bitwise_equal':True}
        for model,shape in self.shapes.items():
            for tokens in (31,32):
                self.command([self.root/'test-ssm','--case',3,shape['channels'],shape['taps'],tokens,2,3],
                             f'boundary-{model}-t{tokens}.log',60,self.arm_env(3))
        self.summary['stages']['dispatch_boundary'] = {'targeted_cases':4,'tokens':[31,32],
            'sequences':2,'projection_padding':3,'reference_state_output_checks':True}
        self.save(); self.phase('hybrid graph operator timing')
        rows = []
        for block in range(6):
            for model, shape in self.shapes.items():
                for tokens in (1,32):
                    for mode in ((0,3) if block%2 == 0 else (3,0)):
                        label = f'op-{model}-t{tokens}-b{block}-m{mode}'
                        self.command([self.root/'test-ssm','--bench',mode,shape['channels'],shape['taps'],tokens,1],
                                     label+'.log',30,self.arm_env(mode))
                        records = [json.loads(x) for x in (self.root/(label+'.log')).read_text().splitlines() if x.startswith('{')]
                        if len(records) != 1: raise ValueError('operator sample missing')
                        record = records[0]
                        if record['wall_ms'] < 200 or not 0 < record['ms_per_call'] < float('inf'):
                            raise ValueError('invalid operator measurement')
                        if (record['mode'],record['channels'],record['taps'],record['tokens'],record['sequences']) != (mode,shape['channels'],shape['taps'],tokens,1):
                            raise ValueError('operator shape differs')
                        rows.append(dict(record,model=model,block=block))
                        (self.root/'operator.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
        comparisons = []
        for model in self.shapes:
            for tokens in (1,32):
                arms = {mode:[r['ms_per_call'] for r in rows if (r['model'],r['tokens'],r['mode']) == (model,tokens,mode)] for mode in (0,3)}
                comparisons.append(dict(model=model,tokens=tokens,**fast.gate(arms[0],arms[3])))
        eligible = not any(c['clear_regression'] for c in comparisons) and sum(c['advance'] for c in comparisons) >= 2
        self.summary['stages']['operators'] = {'records':len(rows),'comparisons':comparisons,'eligible':eligible}
        self.save()

    def hybrid_state(self):
        self.phase('full-model hybrid transitions/reset/RS reference fallback')
        for model, info in self.expected['models'].items():
            label = 'state-' + model
            self.command([self.root/'test-state',info['path'],3],label+'.log',1800,self.arm_env(3))
            text = (self.root/(label+'.log')).read_text()
            records = [json.loads(x) for x in text.splitlines() if x.startswith('{')]
            if len(records) != 16 or not all(r['bitwise_equal'] for r in records):
                raise ValueError('mixed batch/decode state identity incomplete')
            markers = MARKER.findall(text)
            for wanted in ((2,'channels',0,32,3),(0,'time',0,1,3),(0,'time',0,31,3),(0,'time',3,32,3)):
                if not any((int(m),lay,int(rs),int(t),int(req)) == wanted and cpu == '1' for m,lay,rs,cpu,t,req in markers):
                    raise ValueError('mixed state/fallback marker missing: '+str(wanted))
            self.summary['stages'][label] = {'comparisons':16,'bitwise_equal':True,'chunks':[32,1,31,32],
                                          'reset':True,'rs3_reference_fallback':True}
            self.save()

    def complete_model(self, model):
        url = 'http://127.0.0.1:18085'
        with socket.socket() as probe:
            if probe.connect_ex(('127.0.0.1',18085)) == 0: raise ValueError('benchmark port occupied')
        readme = (self.source/'tools/server/README.md').read_text()
        blocks, base_cases = pilot.doc_blocks(readme)
        document = None; cases = None; pairs = {}; configs = {}; counts = {}
        for arm in (('control','hybrid') if model == '2B' else ('hybrid','control')):
            requested = 0 if arm == 'control' else 3
            self.phase(model+' '+arm+' server startup')
            argv = [str(self.server),'-m',self.expected['models'][model]['path'],'--alias','local',
                    '-t','4','-c','6144','--parallel','1','-b','32','-ub','32','-fa','on',
                    '-ctk','f16','-ctv','f16','-ngl','0','--no-context-shift','--host','127.0.0.1','--port','18085']
            env = self.arm_env(requested)
            configs[arm] = {'command':argv,'runtime':{k:v for k,v in env.items() if k.startswith('SPINE_') or k == 'LD_LIBRARY_PATH'}}
            fast.write_json(self.root/(model+'-configs.json'),configs)
            logpath = self.root/(model+'-'+arm+'.server.log')
            with logpath.open('w') as log:
                proc = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, env=env)
                try:
                    pilot.bench.wait_healthy(proc,url,120)
                    if document is None:
                        document, count = pilot.quality.make_document(url,chat,blocks,readme,2048,120)
                        (self.root/(model+'-document.txt')).write_text(document)
                        cases = pilot.task_cases(document,base_cases)
                        for case in cases:
                            if case['kind'] == 'code' or case['case_id'] == 'chinese_policy': case['max_tokens'] = 2048
                        fast.write_json(self.root/(model+'-cases.json'),{'cases':cases,'blocks':blocks,'document_tokens':count})
                    for case in (cases if arm == 'control' else list(reversed(cases))):
                        self.phase(model+' '+arm+' '+case['case_id'])
                        payload = chat.request_body([{'role':'system','content':case['system']},{'role':'user','content':case['user']}],'local',0,case['max_tokens'])
                        payload.update(cache_prompt=False,stream_options={'include_usage':True},verbose=True)
                        count = chat.count_prompt_tokens(url,payload,120)
                        if count+case['max_tokens'] > 6144: raise ValueError('full prompt/output exceed context')
                        if case['case_id'] in counts and counts[case['case_id']] != count: raise ValueError('paired input counts differ')
                        counts[case['case_id']] = count
                        record = {'case_id':case['case_id'],'arm':arm,'model':model,'request':payload,'prompt_tokens':count,
                                  'request_sha256':hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest()}
                        try:
                            signal.alarm(1800)
                            answer = chat.complete(url,payload,1800,display=False)
                            record.update(answer,audit=audit_result(answer,payload,count),facts=checks.fact_check(case,answer['answer']))
                            if case['kind'] == 'code': record['code_test'] = checks.check_code(case['case_id'],answer['answer'])
                        except Exception as error:
                            record['error'] = type(error).__name__+': '+str(error)[:200]
                            raise
                        finally:
                            signal.alarm(0)
                            pairs.setdefault(case['case_id'],{})[arm] = record
                            fast.write_json(self.root/(model+'-pairs.json'),pairs)
                            self.summary['requests_completed'] = sum(len(v) for v in pairs.values())+self.summary.get('previous_model_requests',0)
                            self.save()
                        invalid = [name for name,ok in record['audit'].items() if not ok and name != 'complete']
                        if invalid: raise ValueError('invalid complete-answer measurement: '+', '.join(invalid))
                        # A length-capped answer is retained as a quality failure, never
                        # counted as useful. Its server has finished and can continue.
                        (self.root/(model+'-'+arm+'-'+case['case_id']+'-answer.md')).write_text(record['answer']+'\n')
                finally:
                    proc.terminate()
                    try: proc.wait(timeout=10)
                    except subprocess.TimeoutExpired: proc.kill(); proc.wait()
            text = logpath.read_text()
            activation = check_activation(text,requested)
            routing = re.findall(r'K1_GEMM_ROUTE mode=(\d) phase=(prefill|single)',text)
            if {phase for _,phase in routing} != {'prefill','single'} or any(mode != '3' for mode,_ in routing):
                raise ValueError('route-3 activation differs')
            if 'SPINE_FA_WIDE_TILE: RVV tiled attention enabled for 256-dim heads' not in text:
                raise ValueError('wide attention activation absent')
            self.summary['stages'][model+'-'+arm+'-activation'] = activation; self.save()
        if len(pairs) != 6 or not all(set(v) == {'control','hybrid'} for v in pairs.values()):
            raise ValueError('complete-answer paired coverage incomplete')
        self.summary['previous_model_requests'] = self.summary['requests_completed']
        self.summary['models'][model] = {'requests_completed':12,'status':'generation completed'}; self.save()

    def run(self):
        def expired(signum,frame): raise TimeoutError('request or campaign budget expired')
        signal.signal(signal.SIGALRM,expired); signal.signal(signal.SIGTERM,expired)
        self.summary.update(models={},requests_completed=0,planned_requests=24,
            protocol={'candidate_mode':3,'threshold_per_sequence_tokens':32,'route':3,'mtp':False,'threads':4,
                      'batch':32,'ubatch':32,'context':6144,'document_budget':2048,'natural_stop':True,
                      'facts_output_guard':512,'code_prose_output_guard':2048,'requests_per_case_arm':1,
                      'tasks':['routes','trace','aggregation','free_windows','unicode_runs','chinese_policy'],
                      'order':{'2B':['control','hybrid'],'4B':['hybrid','control']},'request_budget_s':1800},
            limitations='Complete answers, full prompts and cold input; one pair per task/model is descriptive, not statistical speedup. Operator gates retain their thresholds; quality is collected after exact state checks even if timing is inconclusive. No production defaults change.')
        try:
            self.prepare(); self.hybrid_native(); self.hybrid_state()
            for model in ('2B','4B'): self.complete_model(model)
            self.phase('verify preserved baseline')
            for path,digest in self.baseline_hashes.items():
                if fast.digest(path) != digest: raise ValueError('baseline changed: '+path)
            self.summary.update(status='generation completed; judging pending',baseline_preserved=True)
            self.save(); self.phase(self.summary['status'])
        except BaseException as error:
            self.summary.update(status='failed',reason=type(error).__name__+': '+str(error)[:200]); self.save(); self.phase('failed'); raise

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('root',type=Path)
    Run(parser.parse_args().root.resolve()).run()
