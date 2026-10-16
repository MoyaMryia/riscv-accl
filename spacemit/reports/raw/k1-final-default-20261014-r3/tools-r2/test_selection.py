"""检查均衡选型、明确退化拒绝和失败证据处理。"""
import os
import io
import json
import unittest
from unittest.mock import patch
from selection import choose
from experiment import stream

BASE = dict(mask=0, threads=4, ubatch=32)
FAST = dict(mask=3, threads=4, ubatch=32)
ALL = dict(mask=7, threads=4, ubatch=32)

def data(config, prefill, decode):
 return [dict(config=config, status='pass', model=model, input_tokens=tokens,
  ttft_ms=prefill, decode_ms=decode) for model in ('2B','4B') for tokens in (512,2048) for repeat in range(2)]

class SelectionTests(unittest.TestCase):
 def test_balanced_gain(self):
  decision=choose(data(BASE,100,100)+data(FAST,90,80),[BASE,FAST],BASE)
  self.assertEqual(decision['selected'],FAST)
 def test_single_metric_regression(self):
  decision=choose(data(BASE,100,100)+data(FAST,60,104),[BASE,FAST],BASE)
  self.assertEqual(decision['selected'],BASE)
 def test_indistinguishable_prefers_fewer_candidates(self):
  decision=choose(data(BASE,100,100)+data(FAST,90,80)+data(ALL,89,79),[BASE,FAST,ALL],BASE)
  self.assertEqual(decision['selected'],FAST)
 def test_failed_control_is_rejected(self):
  rows=data(BASE,100,100)+data(FAST,90,80)
  rows[0]['status']='failed'
  with self.assertRaises(ValueError):choose(rows,[BASE,FAST],BASE)
 def test_missing_shape_cannot_win(self):
  rows=data(BASE,100,100)+data(FAST,50,50)[:2]
  self.assertEqual(choose(rows,[BASE,FAST],BASE)['selected'],BASE)
 def test_nonfinite_is_rejected(self):
  with self.assertRaises(ValueError):choose(data(BASE,100,100)+data(FAST,float('nan'),80),[BASE,FAST],BASE)
 def test_stream_retains_exact_tokens(self):
  events=[{'tokens':[264],'content':' a'},{'tokens':[264],'content':' a'},
   {'stop':True,'tokens_predicted':2,'timings':{'prompt_ms':10.0,'predicted_ms':5.0}}]
  raw=b''.join(b'data: '+json.dumps(e).encode()+b'\n' for e in events)
  with patch('urllib.request.urlopen',return_value=io.BytesIO(raw)):
   result=stream('http://127.0.0.1:1',{},1)
  self.assertEqual(result['token_ids'],[264,264])
  self.assertEqual(result['text'],' a a')
 def test_stream_missing_final_is_rejected(self):
  with patch('urllib.request.urlopen',return_value=io.BytesIO(b'data: {"tokens":[264]}\n')):
   with self.assertRaises(ValueError):stream('http://127.0.0.1:1',{},1)

if __name__=='__main__':
 if not os.environ.get('TMUX'):raise SystemExit('Run tests in tmux.')
 unittest.main(verbosity=2)
