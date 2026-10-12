from pathlib import Path
import json,hashlib
root=Path('spacemit/reports/raw/k1-local-candidates-C2-r2-final-20261009-221900')
s=json.loads((root/'summary.json').read_text());a=json.loads((root/'complete-answers/summary.json').read_text());initial=json.loads(Path('spacemit/reports/raw/k1-local-candidates-C2-r2-initial-20261009-181500/summary.json').read_text())
assert (root/'exit-status').read_text().strip()=='0'
assert s['status']=='complete-answers-generated; review-pending' and s['full_answers']=='review-pending' and s['baseline_preserved']
assert s['identity']==initial['identity'] and len(s['repeats'])==2
for n,stamp in [(1,'191500'),(2,'211700')]:
 prior=Path(f'spacemit/reports/raw/k1-local-candidates-C2-r2-repeat{n}-20261009-{stamp}')
 expected=json.loads((prior/f'repeat-{n}/result.json').read_text());expected['independent_repeat']=n
 assert s['repeats'][n-1]==expected
 assert s['repeats'][n-1]['status']=='eligible'
assert s['initial']==json.loads(Path('spacemit/reports/raw/k1-local-candidates-C2-r2-initial-20261009-181500/C2-vs-C0/result.json').read_text())
assert s['state']==initial['state']
assert s['probe_sha256']==initial['probe_sha256']
assert a['status']=='generation completed; review pending' and a['requests_completed']==24
assert a['protocol']=={'tasks':['routes','trace','aggregation','free_windows','unicode_runs','chinese_policy'],'threads':4,'batch':32,'ubatch':32,'context':6144,'document_budget':2048,'facts_output_guard':512,'code_prose_output_guard':2048,'natural_stop':True,'request_budget_s':1800,'mtp':False,'route':3,'kv':'f16','temperature':0,'seed':42,'order':{'2B':['C0','C2'],'4B':['C2','C0']}}
for m in ['2B','4B']:
 pairs=json.loads((root/'complete-answers'/(m+'-pairs.json')).read_text());assert len(pairs)==6
 for case,pair in pairs.items():
  for arm,r in pair.items():
   assert (root/'complete-answers'/f'{m}-{arm}-{case}-answer.md').read_text()==r['answer']+'\n'
   req=r['request'];assert req['temperature']==0 and req['seed']==42 and not req['cache_prompt']
   assert req['max_tokens']==(2048 if case in ['free_windows','unicode_runs','chinese_policy'] else 512)
review={'状态':'完整回答与最终阶段记录已核验','退出码':0,'两轮原始证据与最终摘要相同':True,'完整回答数':24,'完整回答协议与保护上限核验':True,'模型及库身份与初筛相同':True,'控制器最终基线身份核验通过':True,'限制':'最终板端身份由持锁控制器核验。本机比对其记录，未再次读取板端全部模型文件。绝对质量结论另存。'}
(root/'final-stage-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(review,ensure_ascii=False,indent=2))
