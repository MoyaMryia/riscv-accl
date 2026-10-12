import sys,json,hashlib,re
from pathlib import Path
sys.path.insert(0,str(Path('spacemit/bench/local-candidates').resolve()))
import prefill
q=prefill.prepare.module('handoff_answer_quality',prefill.prepare.HERE.parent/'k1-ssm-quality.py')
b1=prefill.prepare.module('b1_answer_review',prefill.prepare.HERE/'model-b1.py')
raw=Path('spacemit/reports/raw');root=raw/'k1-local-candidates-B1-r2-final-20261009-171400';c=root/'complete-answers';prior=raw/'k1-local-candidates-C1-complete-20261009-040000';old=json.loads((prior/'local-review.json').read_text());result={'状态':'全部 24 次完整回答复核结束；绝对质量未通过','独立复验':'两轮共 64 次冷请求通过','模型':{},'限制':'每任务每模型一组配对。完整回答没有逐请求线程快照。共同错误来源待验证。'}
for m in ['2B','4B']:
 pairs=json.loads((c/(m+'-pairs.json')).read_text());before=json.loads((prior/'complete-answers'/(m+'-pairs.json')).read_text());cases=json.loads((c/(m+'-cases.json')).read_text())['cases'];reviews={}
 for case in cases:
  name=case['case_id'];pair=pairs[name];assert set(pair)=={'B0','B1'}
  a,b=pair['B0'],pair['B1'];assert a['request']==b['request'] and a['prompt_tokens']==b['prompt_tokens'];assert a['answer']==b['answer']
  old_a=next(iter(before[name].values()));assert old_a['request']==a['request'] and old_a['answer']==a['answer']
  for arm,record in pair.items():
   h=hashlib.sha256(json.dumps(record['request'],sort_keys=True,ensure_ascii=False).encode()).hexdigest();assert h==record['request_sha256'];assert hashlib.sha256(record['answer'].encode()).hexdigest()==record['answer_sha256'];assert q.audit_result(record,record['request'],record['prompt_tokens'])==record['audit'];assert all(record['audit'].values());assert record['finish_reason']=='stop';assert q.checks.fact_check(case,record['answer'])==record['facts']
   if case['kind']=='code':assert q.checks.check_code(name,record['answer'])==record['code_test']
  review=old[m+'_full_answers']['task_reviews'][name]
  reviews[name]={'通过':review['pass'],'与 C1 复核文本和请求相同':True,'错误':review['errors']}
  if name=='chinese_policy':reviews[name]['汉字数']=len(re.findall(r'[\u4e00-\u9fff]',a['answer']))
 for arm in ['B0','B1']:
  text=(c/(m+'-'+arm+'.server.log')).read_text();b1.activation(text,int(arm=='B1'),8 if m=='2B' else 16,arm=='B1');assert 'SPINE_GDN_PREFILL: scalar-gate K1 RVV fusion enabled' not in text;route=re.findall(r'K1_GEMM_ROUTE mode=(\d) phase=(prefill|single)',text);assert {p for _,p in route}=={'prefill','single'} and all(mode=='3' for mode,_ in route);assert 'num_perfer_cores: 4' in text
 configs=json.loads((c/(m+'-configs.json')).read_text())
 for arm,conf in configs.items():
  args=conf['command'];assert args[args.index('-t')+1]=='4';assert args[args.index('-b')+1]=='32';assert args[args.index('-ub')+1]=='32'
 assert set(configs)=={'B0','B1'}
 for arm,conf in configs.items():
  args=conf['command'];env=conf['runtime'];assert env['SPINE_K1_FA_GQA']==str(int(arm=='B1'));assert all(env[k]=='0' for k in ['SPINE_K1_FA_DECODE','SPINE_GDN_PREFILL','SPINE_K1_SSM_CONV','SPINE_K1_CONV_SILU']);assert env['SPINE_K1_TRACE']=='1';assert env['SPINE_FA_WIDE_TILE']=='1';assert env['SPINE_FA_K1_LAYOUT']=='0';assert env['SPINE_K1_GEMM_ROUTE']=='3';assert args[args.index('-c')+1]=='6144';assert args[args.index('-ctk')+1]==args[args.index('-ctv')+1]=='f16';assert '--no-context-shift' in args
 result['模型'][m]={'请求数':12,'配对数':6,'请求与全文相同':True,'全部自然停止与审计通过':True,'观察到候选新增回归数':0,'绝对质量通过数':sum(x['通过'] for x in reviews.values()),'全文复核':reviews}
(root/'complete-answer-review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
