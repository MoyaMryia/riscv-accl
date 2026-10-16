"""检查尚未覆盖的候选组合，保留编译与数值证据。"""
import importlib.util,json,os,subprocess,sys
from pathlib import Path
root=Path.cwd();tool=root/'tools'
sys.path.insert(0,str(tool))
import experiment as e
assert os.environ.get('TMUX') and os.environ.get('K1_PACKAGE_LOCK_FD')=='9'
os.fstat(9)
old=Path.home()/'Projects/riscv-accl-bench-2026-09-27/k1-unified-20261013-rc1'
source=old/'source';build=old/'build';output=root/'native-check'
assert not output.exists();output.mkdir()
cxx=Path.home()/'Projects/llm-bench/.toolchain/gcc14/usr/bin/g++-14'
spert=Path.home()/'Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2'
tcm=Path.home()/'Projects/llm-bench/.toolchain/spine-tcm'
env=e.environment(build/'bin',spert,tcm,dict(mask=0,threads=4,ubatch=32))
argv=[str(cxx),'-O3','-std=c++17','-DSPINE_K1_BOARD','-march=rv64gcv_zfh_zvfh_zicbop_zihintpause_zba','-mabi=lp64d']
argv+=['-I'+str(source/p) for p in ('include','ggml/include','ggml/src','ggml/src/ggml-cpu','ggml/src/ggml-cpu/spacemit','src/models')]
argv+=[str(tool/'test-state-all-masks.cpp'),'-L'+str(build/'bin'),'-Wl,-rpath,$ORIGIN','-lllama','-lggml','-lggml-cpu','-lggml-base','-pthread','-o',str(tool/'test-state-all-masks')]
e.save(output/'compile.json',dict(argv=argv,compiler_sha256=e.sha(cxx)))
with (output/'compile.log').open('w') as log:subprocess.run(argv,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
pins=json.loads((old/'validation/receipts.json').read_text())
assert e.sha(old/'validation/state.json')==pins['state.json']
reference=json.loads((old/'validation/state.json').read_text())
records={}
for model,item in e.MODELS.items():
 for arm in (3,5):
  label=f'{model}-m{arm}';dump=output/(label+'.data')
  env['SPINE_K1_TRACE']='1'
  argv=[str(tool/'test-state-all-masks'),str(Path.home()/'Projects/spacemit-llama/models'/item[0]),str(arm),str(dump),'short']
  e.save(output/(label+'.command.json'),dict(argv=argv,environment={k:v for k,v in env.items() if k.startswith('SPINE_') or k=='LD_LIBRARY_PATH'}))
  with (output/(label+'.log')).open('w') as log:proc=subprocess.run(argv,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
  (output/(label+'.exit-status')).write_text(str(proc.returncode)+'\n');proc.check_returncode()
  log=(output/(label+'.log')).read_text();rows=[json.loads(s) for s in log.splitlines() if s.startswith('{')]
  assert len(rows)==16 and all(v['bitwise_equal'] and v['max_abs']==0 for v in rows)
  assert 'PASS: 16 full-vocabulary records' in log
  expected=reference[f'state-{model}-0']['sha256']
  assert e.sha(dump)==expected
  assert ('SPINE_GDN_PREFILL_R2:' in log)==bool(arm & 4)
  if model=='4B':assert 'K1_FA path=B1 ' in log
  records[label]=dict(sha256=expected,rows=rows)
e.save(output/'summary.json',dict(status='pass',records=records,reference_state_sha256=e.sha(old/'validation/state.json')))
e.save(output/'receipts.json',{p.name:e.sha(p) for p in output.iterdir() if p.is_file()})
print('PASS: four new combination checks; 64 full-vocabulary records')
