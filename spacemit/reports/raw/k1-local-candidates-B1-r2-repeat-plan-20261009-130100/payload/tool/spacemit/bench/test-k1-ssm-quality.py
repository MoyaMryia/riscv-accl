#!/usr/bin/env python3
"""Reject incorrect phase dispatch and incomplete or unusable answer evidence."""
import copy
import importlib.util
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
def module(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'))
    result=importlib.util.module_from_spec(spec); spec.loader.exec_module(result); return result
runner=module('k1-ssm-quality'); scorer=module('score-k1-ssm-quality')

class Qualification(unittest.TestCase):
    def test_small_batch_and_decode_use_reference(self):
        text='\n'.join(f'K1_SSM_CONV mode={mode} layout={layout} rs={rs} cpu_only=1 tokens={tokens} requested=3'
            for mode,layout,rs,tokens in ((0,'time',0,1),(0,'time',0,31),(2,'channels',0,32),(0,'time',3,32)))
        runner.check_activation(text,3)
        for old,new in (('tokens=32 requested=3','tokens=31 requested=3'),
                        ('mode=0 layout=time rs=0 cpu_only=1 tokens=1','mode=2 layout=channels rs=0 cpu_only=1 tokens=1'),
                        ('mode=0 layout=time rs=3','mode=2 layout=channels rs=3')):
            with self.assertRaises(ValueError): runner.check_activation(text.replace(old,new),3)
    def test_truncation_caching_and_drafting_are_not_useful_measurements(self):
        payload={'cache_prompt':False,'max_tokens':2048}
        r={'answer':'A complete answer','finish_reason':'stop','server_slot':0,'usage':{
            'prompt_tokens':2100,'completion_tokens':300,'prompt_tokens_details':{'cached_tokens':0}},
            'timings':{'prompt_n':2100,'predicted_n':300,'prompt_ms':100,'predicted_ms':200}}
        self.assertTrue(all(runner.audit_result(r,payload,2100).values()))
        for field,value in (('finish_reason','length'),('reasoning_text','hidden thinking')):
            bad=copy.deepcopy(r); bad[field]=value
            self.assertFalse(all(runner.audit_result(bad,payload,2100).values()))
        for field,value in (('draft_n',1),('prompt_ms',0),('predicted_n',301)):
            bad=copy.deepcopy(r); bad['timings'][field]=value
            self.assertFalse(all(runner.audit_result(bad,payload,2100).values()))
        bad=copy.deepcopy(r); bad['usage']['prompt_tokens_details']['cached_tokens']=2000
        self.assertFalse(all(runner.audit_result(bad,payload,2100).values()))
    def test_identical_wrong_code_or_missing_citations_still_fail(self):
        self.assertFalse(scorer.absolute_pass({'kind':'code'},{'facts':[],'citations':[]},{'pass':False}))
        self.assertFalse(scorer.absolute_pass({'kind':'facts'},{'facts':[True],'citations':[False]},{}))
        self.assertTrue(scorer.absolute_pass({'kind':'code'},{'facts':[],'citations':[]},{'pass':True}))

if __name__ == '__main__': unittest.main()
