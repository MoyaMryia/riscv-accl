import contextlib,copy,importlib.util,io,json,os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path('spacemit/bench/local-candidates').resolve()))
spec=importlib.util.spec_from_file_location('driver','spacemit/bench/local-candidates/repeat-b1.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
fixture=Path('spacemit/reports/raw/k1-local-candidates-B1-r2-model-result-20261009-130000').resolve();pilot=json.loads((fixture/'summary.json').read_text());fixed=json.loads((fixture/'model-protocol.json').read_text());identity=pilot['identity']
for fail in [False,True]:
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp)/'root';root.mkdir();initial=Path(tmp)/'initial';initial.mkdir();screen=Path(tmp)/'screen';screen.mkdir();home=Path(tmp)/'home';(home/'Projects/riscv-accl-bench-2026-09-27').mkdir(parents=True)
  (root/'repeat-protocol.json').write_text(json.dumps({'repeats':2,'order':['B0','B1','B1','B0'],'fixed_files_sha256':{}}));(initial/'summary.json').write_text(json.dumps(pilot));server='/fake/source/build/bin/llama-server';expected={'artifacts_sha256':{server:identity['server_sha256']},'models':identity['models'],'runtime':{'LD_LIBRARY_PATH':'/fixed/runtime'}};(screen/'expected-provenance.json').write_text(json.dumps(expected));(screen/'baseline-before.json').write_text('{}')
  hashes={str(initial/'lib/libggml-cpu.so'):identity['candidate_cpu_sha256'],str(initial/'lib/libllama.so'):identity['model_library_sha256'],server:identity['server_sha256'],'/fake/source/build/bin/libggml-cpu.so':identity['original_cpu_sha256']}
  for name,info in identity['models'].items():
   hashes[info['path']]=info['sha256']
   for arm,receipt in pilot['state'][name].items():
    for suffix,key in [('.bin','dump_sha256'),('.log','log_sha256')]:hashes[str(initial/(name+'-'+arm+'-state'+suffix))]=receipt[key]
  calls=[];collected=[]
  def run(command,**kw):
   command=list(map(str,command));label=command[command.index('--label')+1];arm=int('-B1-' in label);environment=kw['env'];assert environment['SPINE_K1_FA_GQA']==str(arm);assert all(environment[k]=='0' for k in ['SPINE_K1_FA_DECODE','SPINE_GDN_PREFILL','SPINE_K1_SSM_CONV','SPINE_K1_CONV_SILU']);assert environment['SPINE_K1_TRACE']=='1';rows=[json.loads(line) for line in (fixture/'cold'/(label+'.jsonl')).read_text().splitlines()]
   if fail and label.startswith('2B-p2048-n65-B1'):
    next(r for r in rows if r['kind']=='measurement')['results'][0]['timings']['predicted_ms']=100000
   Path(command[command.index('--output')+1]).write_text('\n'.join(json.dumps(r) for r in rows));Path(command[command.index('--log')+1]).write_bytes((fixture/'cold'/(label+'.server.log')).read_bytes());calls.append(label)
  with patch.object(d.Path,'home',return_value=home),patch.object(d.board,'digest',side_effect=lambda p:hashes[str(p)]),patch.object(d.subprocess,'run',side_effect=run),patch.object(d.answers,'collect',side_effect=lambda *args:collected.append(args)),patch.object(sys,'argv',['repeat-b1',str(root),str(initial),str(screen)]),contextlib.redirect_stdout(io.StringIO()):
   assert d.main()==0
  summary=json.loads((root/'summary.json').read_text())
  if fail:assert len(calls)==24 and not collected and summary['status']=='repeat-gate-stopped'
  else:assert len(calls)==64 and len(collected)==1 and len(summary['repeats'])==2 and summary['full_answers']=='review-pending'
  print('PASS:', 'failed primary decode stops all later work' if fail else 'two independent B1 ABBA repeats use B1 switches and reach the answer collector')
from types import SimpleNamespace
q=d.prefill.prepare.module('collector_quality_test',d.prefill.prepare.HERE.parent/'k1-ssm-quality.py')
base=Path('spacemit/reports/raw/k1-local-candidates-C3-final-20261009-130000/complete-answers')
case_lists={m:json.loads((base/(m+'-cases.json')).read_text())['cases'] for m in ['2B','4B']};records={m:json.loads((base/(m+'-pairs.json')).read_text()) for m in ['2B','4B']}
active={'model':'2B'};environments=[]
class Process:
 def __init__(self,argv,stdout,stderr,env):
  m='2B' if '2B' in argv[argv.index('-m')+1] else '4B';active['model']=m;a=int(env['SPINE_K1_FA_GQA']);stdout.write((fixture/'cold'/f'{m}-p2048-n65-B{a}-{1 if a else 0}.server.log').read_text());environments.append((m,a,env))
 def terminate(self):pass
 def wait(self,timeout):return 0
 def kill(self):pass
class Socket:
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def connect_ex(self,*args):return 1

def record(payload):
 for pair in records[active['model']].values():
  if pair['C0']['request']==payload:return pair['C0']
 raise AssertionError('collector changes a fixed question or request')

def complete(url,payload,*args,**kwargs):
 r=record(payload);return {k:v for k,v in r.items() if k in ['answer','ttft_s','wall_s','finish_reason','answer_sha256','usage','timings','server_slot','reasoning_text']}
with tempfile.TemporaryDirectory() as tmp:
 source=Path(tmp)/'source';(source/'tools/server').mkdir(parents=True);(source/'tools/server/README.md').write_text('fixed reference')
 with patch.object(d.answers.prefill.prepare,'module',return_value=q),patch.object(q.pilot,'doc_blocks',return_value=([],[])),patch.object(q.pilot.quality,'make_document',return_value=('fixed document',2048)),patch.object(q.pilot,'task_cases',side_effect=lambda *a:copy.deepcopy(case_lists[active['model']])),patch.object(q.pilot.bench,'wait_healthy'),patch.object(q.chat,'count_prompt_tokens',side_effect=lambda u,p,t:record(p)['prompt_tokens']),patch.object(q.chat,'complete',side_effect=complete),patch.object(d.answers.socket,'socket',Socket),patch.object(d.answers.subprocess,'Popen',Process),patch.dict(os.environ,{'LD_LIBRARY_PATH':'/fixed/runtime'}):
  result=d.answers.collect(Path(tmp)/'answers',source,Path('/fake/server'),{'models':identity['models']},Path('/fake/B1/lib'),'B1')
 assert result['requests_completed']==24 and [(m,a) for m,a,e in environments]==[('2B',0),('2B',1),('4B',1),('4B',0)]
 for m,a,e in environments:assert all(e[k]=='0' for k in ['SPINE_GDN_PREFILL','SPINE_K1_SSM_CONV','SPINE_K1_CONV_SILU','SPINE_K1_FA_DECODE'])
 print('PASS: B1 collector preserves all 24 fixed requests, uses B1-only switches, and checks actual B1 paths')
