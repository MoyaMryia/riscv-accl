import sys,json,hashlib,re,statistics
from pathlib import Path
sys.path.insert(0,str(Path('spacemit/bench/local-candidates').resolve()))
import prefill
import importlib.util
spec=importlib.util.spec_from_file_location('model_b1','spacemit/bench/local-candidates/model-b1.py');b1=importlib.util.module_from_spec(spec);spec.loader.exec_module(b1)
raw=Path('spacemit/reports/raw')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(root,obj):
 (root/'local-review.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n') if not (root/'local-review.json').exists() else None
 print(root.name,json.dumps(obj,ensure_ascii=False)[:1200])
def cold(root,sub,summary,reference,candidate,bmode=False):
 for cell in summary:
  m,t,n=cell['model'],cell['tokens'],cell['outputs']; labels=[f'{m}-p{t}-n{n}-{a}-{i}' for i,a in enumerate([reference,candidate,candidate,reference])];rows=[]
  for label in labels:
   path=root/sub/(label+'.jsonl');rs=[json.loads(x) for x in path.read_text().splitlines()];rows+=rs
   config=next(x for x in rs if x['kind']=='config')
   assert all(config[k]==v for k,v in {'threads':4,'batch_size':32,'ubatch_size':32,'cache_type_k':'f16','cache_type_v':'f16','ctx_size':4096,'gpu_layers':0}.items())
   text=(root/sub/(label+'.server.log')).read_text()
   if bmode:b1.activation(text,int('-B1-' in label),8 if m=='2B' else 16,'-B1-' in label and n==65)
   else:prefill.activation(text,label.split('-')[-2])
   assert 'num_perfer_cores: 4' in text
  requests=prefill.FAST.check_model_records(rows,labels,t,n)
  for metric,expected in cell['metrics'].items():
   key={'prefill':'prompt_ms','decode':'predicted_ms','ttft':None}[metric]
   times=[[r['results'][0]['timings'][key] if key else r['results'][0]['ttft_ms'] for r in requests if '-'+arm+'-' in r['label']] for arm in [reference,candidate]]
   actual=prefill.FAST.gate(*times)
   assert actual==expected,(actual,expected)
  passed=not any(v['clear_regression'] for v in cell['metrics'].values()) if bmode else (all(cell['metrics'][k]['advance'] for k in ['prefill','ttft']) if n==1 else not cell['metrics']['decode']['clear_regression'])
  if bmode and t==2048 and n==65:passed=passed and cell['metrics']['decode']['advance']
  assert passed==cell['passed'] and passed
 return len(summary)*4
b=raw/'k1-local-candidates-B1-r2-model-result-20261009-130000';s=json.loads((b/'summary.json').read_text());assert (b/'exit-status').read_text().strip()=='0';assert len(s['comparisons'])==8
states={}
for m in ['2B','4B']:
 hs=[]
 for arm in ['original','B0','B1']:
  rec=s['state'][m][arm];text=(b/(m+'-'+arm+'-state.log')).read_text();rows=[json.loads(x) for x in text.splitlines() if x.startswith('{')]
  assert rows==rec['rows'];assert [(r['rs'],r['reset'],r['prefix']) for r in rows]==[(rs,reset,p) for rs in [0,3] for reset in [0,1] for p in [32,33,64,96,255,256,511,512,2047,2048]]
  assert all(r['bitwise_equal'] and r['max_abs']==0 for r in rows)
  dump=b/(m+'-'+arm+'-state.bin');assert dump.stat().st_size==sum(r['vocab']*4 for r in rows);assert digest(dump)==rec['dump_sha256'];assert digest(b/(m+'-'+arm+'-state.log'))==rec['log_sha256'];hs.append(digest(dump))
  threads=re.findall(r'B1_STATE threads=(\d+) batch_threads=(\d+) rs=(\d+)',text);assert len(threads)==(4 if arm=='B1' else 2);assert all(a==c=='4' for a,c,_ in threads)
  if arm=='B1':
   b1.activation(text,1,8 if m=='2B' else 16,True,True)
   spans=re.findall(r'B1_STATE begin arm=(\d)[^\n]*\n(.*?)B1_STATE end arm=\1',text,re.S);assert len(spans)==80;assert all('K1_FA path=B1 ' not in span or a=='1' for a,span in spans)
 assert len(set(hs))==1;states[m]={'records_per_path':40,'three_paths_equal':True,'sha256':hs[0]}
count=cold(b,Path('cold'),s['comparisons'],'B0','B1',True)
write(b,{'状态':'初筛通过','完整状态':states,'冷请求数':count,'门槛重算':True,'实际路径与四线程':True,'限制':'每臂每配置两次请求。路径日志开销计入计时。独立复验与完整回答待验证。'})
c=raw/'k1-local-candidates-C2-r2-result-20261009-130000';s=json.loads((c/'summary.json').read_text());assert s['strict_operator_gate']['eligible'];assert (c/'exit-status').read_text().strip()=='0'
rows=[json.loads(x) for x in (c/'C2-r2-operators.log').read_text().splitlines() if x.startswith('{')];assert len(rows)==48
for r in rows:assert r['wall_ms']>=100 and r['state_size']==128 and r['key_heads']==16
for cell in s['candidates']['C']['operators']['C2']:
 times=[[r['ms_per_call'] for r in rows if r['heads']==cell['heads'] and r['tokens']==cell['tokens'] and r['mode']==a] for a in [0,1]];assert all(len(x)==6 for x in times);assert prefill.FAST.gate(*times)=={k:v for k,v in cell.items() if k not in ['heads','tokens']}
assert len(set(s['candidates']['C']['numeric']['gdn_original_control_sha256'].values()))==1
for name in ['original','control','C']:
 text=(c/('C2-r2-'+name+'-numeric.log')).read_text();assert 'PASS: 158' in text
 if name=='C':assert {int(x) for x in re.findall(r'K1_GDN_R2 worker=(\d+)',text)}=={0,1,2,3}
write(c,{'状态':'算子门槛通过','算子记录数':48,'逐形状重算':True,'汇编控制器结果':s['revision_assembly'],'限制':'模型状态和模型收益待验证。'})
c=raw/'k1-local-candidates-C3-final-20261009-130000';s=json.loads((c/'repeat-2-vs-C1/result.json').read_text());count=cold(c,Path('repeat-2-vs-C1'),s['comparisons'],'C1','C3');write(c,{'状态':'第四组独立比较通过','冷请求数':count,'门槛重算':True,'限制':'完整回答全文复核另存。每臂每配置两次请求，不能证明总体置信区间。'})
