#!/usr/bin/env python3
"""Regression checks for rejected evidence and independent model execution."""
import importlib.util
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

spec=importlib.util.spec_from_file_location('adaptive',Path(__file__).with_name('adaptive-mtp-test.py'))
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
spec=importlib.util.spec_from_file_location('scorer',Path(__file__).with_name('score-adaptive-mtp.py'))
scorer=importlib.util.module_from_spec(spec);spec.loader.exec_module(scorer)


class RecoveryTests(unittest.TestCase):
    def bare_run(self,root):
        run=runner.Run.__new__(runner.Run)
        run.root=Path(root);run.samples=[];run.url='http://unused'
        run.summary={'models':{}};run.save=lambda:None
        run.logpath=run.root/'server.log';run.logpath.write_text('')
        return run

    def test_length_rejection_preserves_answer_before_gate(self):
        with tempfile.TemporaryDirectory() as root:
            run=self.bare_run(root)
            case={'case_id':'unicode_offsets','kind':'code','system':'source','user':'full specification','max_tokens':3072}
            answer={'answer':'def unfinished(', 'finish_reason':'length','server_slot':0,
                'usage':{'completion_tokens':3072,'prompt_tokens':200,'prompt_tokens_details':{'cached_tokens':0}},
                'timings':{'prompt_n':200,'predicted_n':3072},'reasoning_text':''}
            with patch.object(runner.chat,'count_prompt_tokens',return_value=200), \
                 patch.object(runner.chat,'complete',return_value=answer), \
                 patch.object(runner.signal,'alarm'), \
                 patch.object(runner.checks,'fact_check',return_value={}), \
                 patch.object(runner.checks,'check_code') as functional:
                with self.assertRaisesRegex(ValueError,'complete.*finish_reason=length'):
                    run.request('2B',case,'2B calibrate unicode_offsets')
                functional.assert_not_called()
            saved=json.loads((run.root/'2B-requests.jsonl').read_text())
            self.assertEqual(saved['answer'],answer['answer'])
            self.assertEqual(saved['request']['messages'][1]['content'],case['user'])
            self.assertEqual(saved['validation_failures'],['complete'])
            self.assertEqual(saved['request']['max_tokens'],3072)

    def test_model_failure_does_not_prevent_other_model(self):
        with tempfile.TemporaryDirectory() as root:
            run=self.bare_run(root);run.prepare=lambda:None
            calls=[]
            def smoke(size):
                calls.append(('smoke',size));run.phase(size+' smoke')
                run.summary['models'][size]={'state_gate':'pass'}
            def model(size):
                calls.append(('model',size));run.phase(size+' calibrate code')
                if size=='2B':raise ValueError('incomplete baseline')
                run.summary['models'][size]['status']='generation completed'
            run.smoke=smoke;run.model=model
            with patch.object(runner.signal,'signal'):
                self.assertFalse(run.run())
            self.assertIn(('model','4B'),calls)
            self.assertEqual(run.summary['models']['2B']['status'],'failed')
            self.assertEqual(run.summary['models']['4B']['status'],'generation completed')

    def test_overall_stop_prevents_launching_next_model(self):
        with tempfile.TemporaryDirectory() as root:
            run=self.bare_run(root);run.prepare=lambda:None;calls=[]
            def smoke(size):
                calls.append(size);raise runner.RunInterrupted('stop')
            run.smoke=smoke
            with patch.object(runner.signal,'signal'),self.assertRaises(runner.RunInterrupted):run.run()
            self.assertEqual(calls,['2B'])

    def test_new_code_budget_fits_full_context(self):
        tasks=runner.cases('',[{'case_id':'routes','question':'routes','required_facts':[]}])
        self.assertEqual(tasks[0]['max_tokens'],3072)
        self.assertLessEqual(205+tasks[0]['max_tokens'],6144)

    def test_capped_timing_is_not_complete_quality_evidence(self):
        payload={'max_tokens':1024,'cache_prompt':False}
        answer={'answer':'def unfinished(', 'finish_reason':'length','server_slot':0,
            'usage':{'completion_tokens':1024,'prompt_tokens':200,'prompt_tokens_details':{'cached_tokens':0}},
            'timings':{'prompt_n':200,'predicted_n':1024},'reasoning_text':''}
        self.assertTrue(all(runner.timing_audit(answer,payload,200,True).values()))
        self.assertFalse(all(runner.timing_audit(answer,payload,200,False).values()))
        answer['usage']['completion_tokens']=1023
        answer['timings']['predicted_n']=1023
        self.assertFalse(all(runner.timing_audit(answer,payload,200,True).values()))
        answer['finish_reason']='stop'
        answer['usage']['prompt_tokens_details']['cached_tokens']=3
        self.assertFalse(all(runner.timing_audit(answer,payload,200,True).values()))

    def test_scoring_retains_capped_timing_without_judging_it(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root)
            def save(name,value):(root/name).write_text(json.dumps(value))
            save('collection-receipt.json',{'files_sha256':{}})
            save('run.json',{'screen':'infrastructure','code_sha256':{},'judge':{'base_url':'https://unused','model':'fake'}})
            save('summary.json',{'models':{s:{'status':'generation completed'} for s in ('2B','4B')}})
            (root/'exit-status').write_text('0');(root/'key').write_text('fake-key')
            save('server-configs.json',{arm:{'arm':arm,'command':['server','-t','4','-c','6144','-b','32','-ub','32',
                '-ctk','f16','-ctv','f16','-ngl','0']+(['--spec-type','draft-mtp'] if arm!='direct' else []),
                'runtime':{'SPINE_SPEC_RS':'0','SPINE_K1_GEMM_ROUTE':'0'}} for arm in ('direct','loaded_off','adaptive')})
            tasks=[{'case_id':name,'kind':'code' if name=='unicode_offsets' else 'facts',
                'system':'full system','user':'full input','max_tokens':10} for name in ('unicode_offsets','chinese_policy','routes')]
            for size in ('2B','4B'):
                save(size+'-cases.json',tasks);records=[]
                for repeat in range(3):
                    for case in tasks:
                        for arm in ('direct','loaded_off','adaptive'):
                            payload={'messages':[{'role':'system','content':case['system']},{'role':'user','content':case['user']}],
                                'max_tokens':10,'cache_prompt':False}
                            records.append({'case_id':case['case_id'],'request':payload,'prompt_tokens':200,'answer':'unfinished',
                                'answer_sha256':hashlib.sha256(b'unfinished').hexdigest(),
                                'request_sha256':hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),
                                'finish_reason':'length','server_slot':0,'wall_s':10,'ttft_s':1,
                                'usage':{'prompt_tokens':200,'completion_tokens':10,'prompt_tokens_details':{'cached_tokens':0}},
                                'timings':{'prompt_n':200,'predicted_n':10,'predicted_per_second':2,
                                    'spine_mtp':{'initially_enabled':arm=='adaptive' and case['kind']=='code','cycles':2}},
                                'arm':arm,'repeat':repeat,'server_label':arm})
                save(size+'-responses.json',records)
            helper=runner.module('score-mtp-quality')
            checks=SimpleNamespace(fact_check=lambda *a:{'facts':[],'citations':[]},check_code=lambda *a:{'pass':False})
            fake_runner=SimpleNamespace(pilot=runner.pilot,timing_audit=runner.timing_audit,checks=checks)
            judge=SimpleNamespace(endpoint=lambda *a:'unused',grade_case=lambda *a: self.fail('capped answer sent to judge'))
            def load(name,unused):return {'adaptive-mtp-test':fake_runner,'score-mtp-quality':helper,'judge-shared-document-cache':judge}[name]
            with patch.object(scorer,'load',side_effect=load):result=scorer.score(root,root/'key')
            self.assertFalse(result['candidate_qualified'])
            for model in result['models'].values():
                self.assertTrue(model['infrastructure_timing_available'])
                self.assertEqual(model['pairs'],9)
                self.assertEqual(model['quality_pairs'],0)
                self.assertFalse(model['absolute_checks'])


if __name__=='__main__':unittest.main()
