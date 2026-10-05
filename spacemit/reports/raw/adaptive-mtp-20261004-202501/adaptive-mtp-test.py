#!/usr/bin/env python3
"""Gated switching checks and three-arm complete-answer adaptive MTP screen."""
import argparse
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import threading
import time
import urllib.error

HERE=Path(__file__).resolve().parent
def module(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
pilot=module('mtp-quality');checks=module('mtp-quality-checks')
fast,bench,chat=pilot.fast,pilot.bench,pilot.chat


def cases(document,base_cases):
    original=pilot.task_cases(document,base_cases)
    code=checks.ADAPTIVE_CODE_SPECS['unicode_offsets']
    return [dict(case_id='unicode_offsets',kind='code',system='Implement the specified Python functions. '
        'Use builtins only, no imports/classes. Give source directly without reasoning tags.',user=code,
        question=code,evidence=code,required_facts=['correct Unicode spans and strict offset validation'],max_tokens=1536),
        next(c for c in original if c['case_id']=='chinese_policy'),
        next(c for c in original if c['case_id']=='routes')]


class Run(pilot.Run):
    def __init__(self,root):
        super().__init__(root);self.candidate=False;self.hooks=False;self.configs={}
        self.url='http://127.0.0.1:18085'
        self.summary={'status':'running','models':{},'planned_timing_requests':54,
            'protocol':{'arms':['direct','loaded_off','adaptive'],'repeats':3,'tasks':3,
                'SPINE_SPEC_RS':'0','routing':0,'threads':4,'batch':32,'ubatch':32,'context':6144,
                'weights':'Q4_0','kv':'F16','whole_request_budget_s':1800,'overall_budget_s':21600,
                'eligibility':'explicit code hint, expected >=256, matched per-task direct calibration',
                'fallback':'two windows >105% direct; each >=12 cycles and >=32 committed tokens',
                'defaults_changed':False},
            'limitations':'Three repeats and three tasks/model, single slot. Calibration, diagnostics and timing are distinct. State/quality gates can skip timing.'}
    def env(self):
        env=super().env()
        if self.candidate:env['LD_LIBRARY_PATH']=str(self.root/'build/bin')+':'+env['LD_LIBRARY_PATH']
        if self.hooks:env['SPINE_MTP_TEST_HOOKS']='1'
        return env
    def prepare(self):
        deadline=time.monotonic()+3600
        while not (self.root/'build-exit-status').exists():
            if time.monotonic()>deadline:raise TimeoutError('candidate build deadline')
            time.sleep(5)
        if (self.root/'build-exit-status').read_text().strip()!='0':raise ValueError('candidate build failed')
        super().prepare()
        build=json.loads((self.root/'build-provenance.json').read_text())
        for path,digest in build['candidate_sha256'].items():
            if fast.digest(path)!=digest:raise ValueError('candidate binary changed')
        self.direct_server=self.server;self.candidate_server=self.root/'build/bin/llama-server'
        self.provenance=json.loads((self.root/'provenance.json').read_text())
        self.provenance['candidate_sha256']=build['candidate_sha256'];self.provenance['patch_sha256']=build['patch_sha256']
        fast.write_json(self.root/'provenance.json',self.provenance)
    @contextmanager
    def server_arm(self,size,arm,label,smoke=False):
        with socket.socket() as probe:
            if probe.connect_ex(('127.0.0.1',18085))==0:raise ValueError('benchmark port occupied')
        self.candidate=arm!='direct';self.hooks=smoke
        server=self.candidate_server if self.candidate else self.direct_server
        argv=[str(server),'-m',self.expected['models'][size]['path'],'--alias','local','-t','4','-c','6144',
            '--parallel','1','-b','32','-ub','32','-fa','on','-ctk','f16','-ctv','f16','-ngl','0',
            '--no-context-shift','--host','127.0.0.1','--port','18085']
        if self.candidate:argv+=['--spec-type','draft-mtp','--spec-draft-n-max','3']
        if smoke:argv+=['--log-verbosity','5']
        env=self.env();self.logpath=self.root/(label+'.server.log')
        self.configs[label]={'arm':arm,'model':size,'command':argv,
            'runtime':{k:v for k,v in env.items() if k.startswith('SPINE_') or k=='LD_LIBRARY_PATH'}}
        fast.write_json(self.root/'server-configs.json',self.configs)
        with self.logpath.open('w') as log:
            proc=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,env=env)
            stop=threading.Event();self.samples=[]
            sampler=threading.Thread(target=bench.sample_rss,args=(proc.pid,stop,self.samples,1));sampler.start()
            try:
                bench.wait_healthy(proc,self.url,120);yield
            finally:
                stop.set();sampler.join(timeout=3);proc.terminate()
                try:proc.wait(timeout=10)
                except subprocess.TimeoutExpired:proc.kill();proc.wait()
        self.hooks=False
    def request(self,size,case,label,policy=None,diagnostic=False,cache=False):
        self.phase(label);start_samples=len(self.samples);start_log=self.logpath.stat().st_size
        payload=chat.request_body([{'role':'system','content':case['system']},{'role':'user','content':case['user']}],
            'local',0,case['max_tokens'])
        payload.update(cache_prompt=cache,stream_options={'include_usage':True},verbose=True)
        if policy is not None:payload['spine_mtp']=policy
        count=chat.count_prompt_tokens(self.url,payload,120)
        if count+case['max_tokens']>6144:raise ValueError('full input plus output exceeds context')
        signal.alarm(1800)
        try:answer=chat.complete(self.url,payload,1800,display=False)
        finally:signal.alarm(0)
        audit=pilot.audit_result(answer,payload,count)
        if not diagnostic and not all(audit.values()):raise ValueError('incomplete/cached/count-invalid benchmark answer')
        if diagnostic and (not audit['slot_valid'] or not audit['output_count_valid'] or not audit['reasoning_disabled']):
            raise ValueError('state diagnostic returned invalid telemetry')
        result=dict(answer,request=payload,prompt_tokens=count,audit=audit,case_id=case['case_id'],model=size,
            request_sha256=hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),
            facts=checks.fact_check(case,answer['answer']))
        if case['kind']=='code' and not diagnostic:result['code_test']=checks.check_code(case['case_id'],answer['answer'])
        result['rss_kib']=bench.stats([r[1] for r in self.samples[start_samples:]])
        result['request_log']=self.logpath.read_bytes()[start_log:].decode(errors='replace')
        return result
    def smoke(self,size):
        records=[]
        def save_record(entry):
            records.append(entry)
            fast.write_json(self.root/(size+'-state-checks.json'),records)
        literal=dict(case_id='literal',kind='facts',system='Answer directly without reasoning.',
            user='Reply with exactly the word cobalt.',max_tokens=32,required_facts=['cobalt'],fact_patterns=[r'\bcobalt\b'])
        code=dict(case_id='unicode_offsets',kind='code',
            system='Return Python source directly without reasoning tags.',
            user=checks.ADAPTIVE_CODE_SPECS['unicode_offsets'],max_tokens=128)
        policy=lambda mode,**extra:dict(mode=mode,**extra)
        with self.server_arm(size,'adaptive',size+'-smoke',True):
            for invalid in [{'mode':'bad'},{'mode':'auto','expected_output_tokens':True},{'mode':'off','bogus':1}]:
                body=chat.request_body([{'role':'user','content':'Reply OK'}],'local',0,8);body['spine_mtp']=invalid
                try:chat.post_json(self.url+'/v1/chat/completions',body,30)
                except urllib.error.HTTPError as e:
                    if e.code!=400:raise
                    save_record({'invalid_policy':invalid,'http':e.code});continue
                raise ValueError('invalid policy was silently accepted')
            off=self.request(size,literal,size+' smoke off',policy('off'),True)
            save_record(off)
            if off['timings']['spine_mtp']['initially_enabled'] or off['timings'].get('draft_n',0):raise ValueError('off drafted')
            on=self.request(size,literal,size+' smoke on',policy('on'),True);save_record(on)
            if not on['timings']['spine_mtp']['initially_enabled']:raise ValueError('on ignored')
            if off['answer_sha256']!=on['answer_sha256']:raise ValueError('literal state check disagrees')
            prose=pilot.task_cases('',[])[-1];prose=dict(prose,max_tokens=128)
            forced=self.request(size,prose,size+' forced replay boundary',policy('on',test_fallback_after=12),True);save_record(forced)
            tele=forced['timings']['spine_mtp']
            if tele['reason']!='test_forced_boundary' or tele['fallback_at']<1:raise ValueError('forced switch absent')
            if 'restoring speculative checkpoint' not in forced['request_log']:raise ValueError('forced probe did not exercise checkpoint replay')
            measured=self.request(size,code,size+' measured-cost boundary',policy('on',direct_ms_per_token=0.001,
                calibration_id='synthetic-state-test-only'),True);save_record(measured)
            if measured['timings']['spine_mtp']['reason']!='measured_cost':raise ValueError('timed fallback absent')
            after=self.request(size,literal,size+' smoke off after fallback',policy('off'),True);save_record(after)
            if after['answer_sha256']!=off['answer_sha256'] or after['timings'].get('draft_n',0):raise ValueError('off reset failed')
            warm=self.request(size,literal,size+' cached on after off',policy('on'),True,True);save_record(warm)
            if warm['answer_sha256']!=off['answer_sha256'] or warm['usage']['prompt_tokens_details']['cached_tokens']<=0:
                raise ValueError('prefix reuse after mode change failed')
            missing=self.request(size,code,size+' missing calibration',policy('auto',workload='code',expected_output_tokens=512),True);save_record(missing)
            if missing['timings']['spine_mtp']['initially_enabled'] or missing['timings'].get('draft_n',0):raise ValueError('uncalibrated auto drafted')
        fast.write_json(self.root/(size+'-state-checks.json'),records)
        self.summary['models'][size]={'state_gate':'pass'};self.save()
    def model(self,size):
        readme=(self.source/'tools/server/README.md').read_text();blocks,base_cases=pilot.doc_blocks(readme)
        calibration={};results=[]
        with self.server_arm(size,'direct',size+'-calibration'):
            document,_=pilot.quality.make_document(self.url,chat,blocks,readme,2048,120)
            tasks=cases(document,base_cases)
            fast.write_json(self.root/(size+'-cases.json'),tasks)
            for case in tasks:
                result=self.request(size,case,size+' calibrate '+case['case_id'])
                calibration[case['case_id']]=result
                fast.write_json(self.root/(size+'-calibration.json'),calibration)
        if not calibration['unicode_offsets']['code_test']['pass']:
            self.summary['models'][size].update(status='timing skipped: held-out direct code failed functional checks')
            self.save();return
        self.summary['models'][size]['calibration_gate']='pass';self.save()
        orders=[['direct','loaded_off','adaptive'],['adaptive','direct','loaded_off'],['loaded_off','adaptive','direct']]
        for repeat,arms in enumerate(orders):
            for arm in arms:
                label=f'{size}-r{repeat}-{arm}'
                with self.server_arm(size,arm,label):
                    for case in (tasks if repeat%2==0 else list(reversed(tasks))):
                        baseline=calibration[case['case_id']]
                        cfg=None
                        if arm=='loaded_off':cfg={'mode':'off'}
                        if arm=='adaptive':
                            cfg={'mode':'auto','workload':'code' if case['kind']=='code' else ('qa' if case['case_id']=='routes' else 'prose'),
                                'expected_output_tokens':512 if case['kind']=='code' else (48 if case['case_id']=='routes' else 512),
                                'direct_ms_per_token':baseline['timings']['predicted_per_token_ms'],
                                'calibration_id':size+'-'+case['case_id']+'-'+baseline['answer_sha256'][:12],
                                'calibrated_prompt_max':baseline['prompt_tokens']}
                        record=self.request(size,case,label+' '+case['case_id'],cfg)
                        if record['prompt_tokens']!=baseline['prompt_tokens']:raise ValueError('paired full prompt count changed')
                        if cfg:
                            t=record['timings'].get('spine_mtp',{})
                            want=arm=='adaptive' and case['kind']=='code'
                            if t.get('initially_enabled') is not want:raise ValueError('request policy was ineffective')
                            if not want and record['timings'].get('draft_n',0):raise ValueError('ineligible task drafted')
                            if want and t.get('cycles',0)<=0:raise ValueError('eligible code did not draft')
                        record.update(arm=arm,repeat=repeat,server_label=label)
                        results.append(record);fast.write_json(self.root/(size+'-responses.json'),results)
                        self.summary['models'][size]['timing_requests']=len(results);self.save()
        self.summary['models'][size]['status']='generation completed';self.save()
    def run(self):
        def expired(signum,frame):raise TimeoutError('request or overall board budget expired')
        signal.signal(signal.SIGTERM,expired);signal.signal(signal.SIGALRM,expired)
        try:
            self.prepare()
            for size in ('2B','4B'):self.smoke(size)
            for size in ('2B','4B'):self.model(size)
            self.summary['status']='generation completed; collection/scoring pending';self.save();self.phase(self.summary['status'])
        except BaseException as error:
            self.summary.update(status='failed',reason=type(error).__name__+': '+str(error)[:200]);self.save();self.phase('failed');raise

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);Run(p.parse_args().root.resolve()).run()
