import sys,json,hashlib,re
from pathlib import Path
sys.path.insert(0,str(Path('spacemit/bench/local-candidates').resolve()))
import prefill_c2_r2 as prefill
q=prefill.prepare.module('state_review_quality',prefill.prepare.HERE.parent/'k1-ssm-quality.py')
root=Path('spacemit/reports/raw/k1-local-candidates-C2-r2-state-20261009-171400')
s=json.loads((root/'summary.json').read_text());qual=json.loads((root/'C2-qualification.json').read_text());old=Path('spacemit/reports/raw/k1-local-candidates-C2-r2-result-20261009-130000')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert qual['state_evidence']==s['state'] and qual['identity']==s['identity']
assert all(qual[k] for k in ['numeric_passed','state_passed','operators_passed'])
assert qual['qualified_arms']==['C2'] and digest(root/'test-c2-r2-state')==s['probe_sha256']
libs=json.loads((old/'libraries.json').read_text())
for name,key in [('libggml-cpu.so','library_sha256'),('libllama.so','model_library_sha256')]:
 h=digest(root/'lib'/name);assert h==s['identity'][key]
 assert h==next(v for k,v in libs.items() if k.endswith('/C/lib/'+name+'.0'))
commands=json.loads((root/'commands.json').read_text());assert len(commands)==9
for command in commands:
 env=command['runtime'];label=command['label'];assert env['SPINE_GDN_PREFILL']==str(int('-C2-' in label));assert all(env[k]=='0' for k in ['SPINE_K1_FA_GQA','SPINE_K1_FA_DECODE','SPINE_K1_SSM_CONV','SPINE_K1_CONV_SILU']);assert env['SPINE_K1_TRACE']=='1' and env['SPINE_K1_GEMM_ROUTE']=='3' and env['SPINE_FA_WIDE_TILE']=='1' and env['SPINE_FA_K1_LAYOUT']=='0'
 if label!='state-build':assert command['argv'][2]==str(int('-C2-' in label))
 if label.endswith('rs3-fallback'):assert command['argv'][-1]=='rs3'
plan=json.loads((root/'model-protocol.json').read_text())
source=Path('spacemit/bench/local-candidates/test-c2-r2-state.cpp')
assert digest(source)==next(v for k,v in plan['fixed_files_sha256'].items() if k.endswith('/test-c2-r2-state.cpp'))
result={'状态':'两个模型的三路完整词表与独立 RS=3 回退均通过','模型':{},'实际修订库身份核验':True,'探针哈希核验':True,'固定源文件核验':True,'限制':'本次只确认新模型状态资格。模型初筛、两轮独立复验和完整回答仍待验证。'}
for m in ['2B','4B']:
 data=[]
 for arm in ['original','C0','C2']:
  stem=m+'-'+arm+'-state';text=(root/(stem+'.log')).read_text();record=s['state'][m][arm];rows=[json.loads(x) for x in text.splitlines() if x.startswith('{')]
  assert rows==record['rows']
  assert [(r['rs'],r['reset'],r['prefix']) for r in rows]==[(rs,reset,p) for rs in [0,3] for reset in [0,1] for p in [32,33,64,96]]
  assert all(r['bitwise_equal'] and r['max_abs']==0 for r in rows)
  binary=(root/(stem+'.bin')).read_bytes();assert len(binary)==sum(r['vocab']*4 for r in rows)
  assert digest(root/(stem+'.bin'))==record['dump_sha256'] and digest(root/(stem+'.log'))==record['log_sha256'];data.append(binary)
  threads=re.findall(r'C2_STATE threads=(\d+) batch_threads=(\d+) rs=(\d+)',text);assert len(threads)==(4 if arm=='C2' else 2) and all(a==b=='4' for a,b,_ in threads)
  if arm!='original':prefill.activation(text,'C2' if arm=='C2' else 'C0');q.check_activation(text,0)
  else:assert 'SPINE_GDN_PREFILL_R2:' not in text and 'K1_GDN_R2 worker=' not in text
  if arm=='C2':
   spans=re.findall(r'C2_STATE begin arm=(\d)[^\n]*\n(.*?)C2_STATE end arm=\1',text,re.S);assert len(spans)==32
   for active,span in spans:
    assert not ('K1_GDN_R2 worker=' in span or 'SPINE_GDN_PREFILL_R2:' in span) or active=='1'
 assert data[0]==data[1]==data[2]
 stem=m+'-C2-rs3-fallback';text=(root/(stem+'.log')).read_text();record=s['state'][m]['fresh_rs3_fallback'];rows=[json.loads(x) for x in text.splitlines() if x.startswith('{')]
 assert rows==record['rows']==[r for r in s['state'][m]['C2']['rows'] if r['rs']==3]
 assert digest(root/(stem+'.bin'))==record['dump_sha256'] and digest(root/(stem+'.log'))==record['log_sha256']
 assert (root/(stem+'.bin')).read_bytes()==data[2][len(data[2])//2:]
 assert re.findall(r'C2_STATE threads=(\d+) batch_threads=(\d+) rs=(\d+)',text)==[('4','4','3'),('4','4','3')]
 assert all(x not in text for x in ['SPINE_GDN_PREFILL_R2:','K1_GDN_R2 worker=','SPINE_GDN_PREFILL: scalar-gate K1 RVV fusion enabled'])
 q.check_activation(text,0,require_both=False);markers=q.MARKER.findall(text);assert markers and all(row[2]=='3' for row in markers)
 result['模型'][m]={'每路完整词表份数':16,'三路实际字节逐位相同':True,'独立进程回退份数':8,'回退实际字节与主探针 RS=3 部分相同':True,'修订内核及四个工作线程':True,'三路转储哈希':hashlib.sha256(data[0]).hexdigest()}
(root/'local-review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
