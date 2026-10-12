import json
from pathlib import Path
root=Path('spacemit/reports/raw/k1-local-candidates-C2-r2-repeat2-20261009-211700')
s=json.loads((root/'summary.json').read_text())
prior=Path('spacemit/reports/raw')
initial=json.loads((prior/'k1-local-candidates-C2-r2-initial-20261009-181500/C2-vs-C0/result.json').read_text())
first=json.loads((prior/'k1-local-candidates-C2-r2-repeat1-20261009-191500/repeat-1/result.json').read_text())
second=json.loads((root/'repeat-2/result.json').read_text())
assert s['initial']==initial and s['repeats'][0]==dict(first,independent_repeat=1) and s['repeats'][1]==dict(second,independent_repeat=2)
assert all(r['status']=='eligible' and len(r['comparisons'])==8 for r in [initial,first,second])
assert s['identity']==initial['identity']==first['identity']==second['identity']
c=root/'complete-answers-2B';pairs=json.loads((c/'2B-pairs.json').read_text())
for case,pair in pairs.items():
 for arm,r in pair.items():
  assert (c/f'2B-{arm}-{case}-answer.md').read_text()==r['answer']+'\n'
  req=r['request'];assert req['temperature']==0 and req['seed']==42 and not req['cache_prompt']
  assert req['max_tokens']==(2048 if case in ['free_windows','unicode_runs','chinese_policy'] else 512)
review={'状态':'三组冷请求分别通过；2B 全文保护上限与文件核验通过','冷请求总数':96,'全部原始结果与控制器归档相同':True,'模型与库身份一致':True,'控制器已通过第二轮末身份核验':True,'完整回答':'2B 的 12 次已复核，4B 仍待完成。','范围':'共有绝对质量错误保留为基线限制，不阻塞加速验收。候选新增回归、完整回答异常和最终身份仍须核验。'}
(root/'rounds-and-answer-guards-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(review,ensure_ascii=False,indent=2))
