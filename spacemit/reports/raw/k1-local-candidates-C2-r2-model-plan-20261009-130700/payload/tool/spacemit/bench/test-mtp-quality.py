#!/usr/bin/env python3
"""Check natural completion, relative usefulness, and generated-code isolation."""
import copy
import importlib.util
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
def module(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'))
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
runner,scorer,checks=[module(n) for n in ('mtp-quality','score-mtp-quality','mtp-quality-checks')]

GOOD_RUNS='''def encode_runs(text):
    out = []
    for ch in text:
        if out and out[-1][0] == ch:
            out[-1] = (ch, out[-1][1]+1)
        else:
            out.append((ch,1))
    return out
def decode_runs(runs):
    out = []
    for item in runs:
        if not isinstance(item,(list,tuple)) or len(item)!=2:
            raise ValueError('bad item')
        ch,count = item
        if not isinstance(ch,str) or len(ch)!=1 or not isinstance(count,int) or isinstance(count,bool) or count<=0:
            raise ValueError('bad count')
        out.append(ch*count)
    return ''.join(out)
'''

GOOD_WINDOWS='''def merge_intervals(busy):
    out = []
    for a,b in sorted(busy):
        if b<a:
            raise ValueError('reversed')
        if a==b:
            continue
        if out and a<=out[-1][1]:
            out[-1]=(out[-1][0],max(out[-1][1],b))
        else:
            out.append((a,b))
    return out
def free_windows(busy,start,end):
    if end<start:
        raise ValueError('reversed query')
    merged=merge_intervals(busy)
    out=[]
    pos=start
    for a,b in merged:
        a=max(a,start)
        b=min(b,end)
        if a>=b:
            continue
        if a>pos:
            out.append((pos,a))
        pos=max(pos,b)
    if pos<end:
        out.append((pos,end))
    return out
'''


class Quality(unittest.TestCase):
    def test_judge_receives_full_document(self):
        document='[S1] 17 units. [S3] 23 units. [S5] 38 units.'
        case={'case_id':'aggregation','question':'Add all receipts.',
              'evidence':'[S5] 38 units.','required_facts':['78']}
        tasks=runner.task_cases(document,[case])
        self.assertEqual(tasks[0]['evidence'],document)
        self.assertIn(document,tasks[0]['user'])
    def test_natural_stop_and_cold_counts(self):
        payload={'cache_prompt':False,'max_tokens':512}
        r={'answer':'cobalt','finish_reason':'stop','server_slot':0,'usage':{
            'prompt_tokens':2000,'completion_tokens':20,'prompt_tokens_details':{'cached_tokens':0}},
            'timings':{'prompt_n':2000,'predicted_n':20}}
        self.assertTrue(all(runner.audit_result(r,payload,2000).values()))
        for field,bad in (('finish_reason','length'),('reasoning_text','thinking'),('server_slot',1)):
            changed=copy.deepcopy(r); changed[field]=bad
            self.assertFalse(all(runner.audit_result(changed,payload,2000).values()))
        changed=copy.deepcopy(r); changed['usage']['prompt_tokens_details']['cached_tokens']=1900
        self.assertFalse(all(runner.audit_result(changed,payload,2000).values()))
        self.assertFalse(all(runner.audit_result(r,payload,1999).values()))
    def test_shared_failure_is_not_a_regression(self):
        self.assertFalse(scorer.regression([True,False],[True,False]))
        self.assertTrue(scorer.regression([True,True],[True,False]))
    def test_score_and_coverage_gate(self):
        scores=[{'cold_mean_score':4.5,'warm_mean_score':4.5}]*6
        pairs=[{'deterministic_regression':False}]*6
        self.assertTrue(scorer.judge_gate(scores,pairs)['pass'])
        self.assertFalse(scorer.judge_gate(scores[:-1],pairs)['pass'])
        bad=copy.deepcopy(scores); bad[0]['warm_mean_score']=3.5
        self.assertFalse(scorer.judge_gate(bad,pairs)['pass'])
        bad=copy.deepcopy(pairs); bad[0]['deterministic_regression']=True
        self.assertFalse(scorer.judge_gate(scores,bad)['pass'])
    def test_correct_functions_pass_heldout_cases(self):
        a=checks.check_code('unicode_runs',GOOD_RUNS)
        b=checks.check_code('free_windows',GOOD_WINDOWS)
        self.assertTrue(a['pass'],a); self.assertTrue(b['pass'],b)
        exact_type=checks.check_code('unicode_runs',GOOD_RUNS.replace(
            'not isinstance(count,int) or isinstance(count,bool)', 'type(count) is not int'))
        self.assertTrue(exact_type['pass'],exact_type)
        self.assertGreater(a['checks'],90); self.assertGreater(b['checks'],60)
    def test_wrong_code_and_imports_fail(self):
        self.assertFalse(checks.check_code('unicode_runs',GOOD_RUNS.replace("return ''.join(out)","return ''"))['pass'])
        for source in ('import os\n'+GOOD_RUNS,GOOD_RUNS+'\nprint(1)',
                       GOOD_RUNS.replace('out = []','out = (1).__class__',1)):
            self.assertFalse(checks.check_code('unicode_runs',source)['pass'])


if __name__=='__main__': unittest.main()
