import sys,json,hashlib,re,math
from pathlib import Path
sys.path.insert(0,str(Path('spacemit/bench/local-candidates').resolve()))
import prefill_c2_r2 as prefill
root=Path('spacemit/reports/raw/k1-local-candidates-C2-r2-repeat1-20261009-191500');sub=root/'repeat-1'
r=json.loads((sub/'result.json').read_text());s=json.loads((root/'summary.json').read_text());state=Path('spacemit/reports/raw/k1-local-candidates-C2-r2-state-20261009-171400');qual=json.loads((state/'C2-qualification.json').read_text());plan=json.loads((state/'model-protocol.json').read_text())
assert r['status']=='eligible' and len(r['comparisons'])==8
assert r['identity']==s['identity']==qual['identity']
assert json.loads((sub/'protocol.json').read_text())==prefill.protocol('C2')
assert [(x['tokens'],x['model'],x['outputs']) for x in r['comparisons']]==[(t,m,n) for t in [512,2048] for m in ['2B','4B'] for n in [1,65]]
source_hashes={}
for relative in ['spacemit/bench/local-candidates/prefill_c2_r2.py','spacemit/bench/bench-lifecycle.py','spacemit/bench/k1-fast-test.py']:
 h=hashlib.sha256(Path(relative).read_bytes()).hexdigest();assert h==next(v for k,v in plan['fixed_files_sha256'].items() if k.endswith('/'+relative));source_hashes[relative]=h
primary=[];records=0
for cell in r['comparisons']:
 m,t,n=cell['model'],cell['tokens'],cell['outputs'];rows=[];labels=[]
 for i,arm in enumerate(['C0','C2','C2','C0']):
  label=f'{m}-p{t}-n{n}-{arm}-{i}';labels.append(label);data=[json.loads(x) for x in (sub/(label+'.jsonl')).read_text().splitlines()];rows+=data
  c=next(x for x in data if x['kind']=='config');assert all(c[k]==v for k,v in {'threads':4,'batch_size':32,'ubatch_size':32,'ctx_size':4096,'cache_type_k':'f16','cache_type_v':'f16','gpu_layers':0,'parallel':1,'mode':'plain','ignore_eos':True,'capture_token_ids':True}.items())
  assert c['runtime_env']=={'SPINE_FA_K1_LAYOUT':'0','SPINE_FA_WIDE_TILE':'1','SPINE_GDN_PREFILL':str(int(arm=='C2')),'SPINE_K1_GEMM_ROUTE':'3'}
  assert not any(x in c['command'] for x in ['--spec-type','--model-draft','-md'])
  text=(sub/(label+'.server.log')).read_text();prefill.activation(text,arm);assert 'num_perfer_cores: 4' in text
  assert 'K1_FA path=B1 ' not in text and 'K1_FA path=A1 ' not in text and 'SPINE_K1_CONV_SILU:' not in text
 requests=prefill.FAST.check_model_records(rows,labels,t,n);records+=len(requests)
 for metric,expected in cell['metrics'].items():
  key={'prefill':'prompt_ms','decode':'predicted_ms','ttft':None}[metric]
  times=[[x['results'][0]['timings'][key] if key else x['results'][0]['ttft_ms'] for x in requests if '-'+arm+'-' in x['label']] for arm in ['C0','C2']]
  assert all(math.isfinite(v) and v>0 for group in times for v in group)
  assert prefill.FAST.gate(*times)==expected
 passed=all(cell['metrics'][k]['advance'] for k in ['prefill','ttft']) if n==1 else not cell['metrics']['decode']['clear_regression']
 assert cell['passed']==passed and passed
 if n==1:primary.append({'模型':m,'输入词元':t,'预填充':cell['metrics']['prefill'],'首词元延迟':cell['metrics']['ttft']})
initial=Path('spacemit/reports/raw/k1-local-candidates-C2-r2-initial-20261009-181500/C2-vs-C0')
for path in sub.glob('*.jsonl'):
 now=next(json.loads(x) for x in path.read_text().splitlines() if json.loads(x)['kind']=='measurement');before=next(json.loads(x) for x in (initial/path.name).read_text().splitlines() if json.loads(x)['kind']=='measurement');assert now['prompt_token_sha256']==before['prompt_token_sha256'];assert now['results'][0]['token_ids']==before['results'][0]['token_ids']
result={'完整输入哈希及输出词元与初筛相同':True,'独立轮次':1,'状态':'C2-r2 第一轮独立复验八项比较通过','冷请求数':records,'完整输入哈希及完整输出词元一致':True,'冷缓存与固定配置通过':True,'实际修订内核与四个工作线程通过':True,'全部门槛独立重算':True,'身份与新状态资格相同':True,'冻结依赖源文件 SHA-256':source_hashes,'一词元主指标':primary,'限制':'每臂每配置两次请求不能证明总体置信区间。路径日志开销计入计时。第二轮独立复验和完整回答仍待完成。'}
(root/'local-review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
