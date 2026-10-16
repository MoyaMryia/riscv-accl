"""从已封存重排证据构造片段比较的历史回归样例。"""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
root=Path('/home/moyamryia/Projects/riscv-accl')
here=root/'spacemit/bench/cpu-model'
sys.path.insert(0,str(here))
from common import digest, read, write
spec=importlib.util.spec_from_file_location('fragment_examples_binary',here/'binary-input.py')
binary=importlib.util.module_from_spec(spec);spec.loader.exec_module(binary)
work=Path(__file__).resolve().parent
bundle=work/'examples';bundle.mkdir()
for sub in ('models','traces','dumps','manifests','results','commands','logs'):(bundle/sub).mkdir()
prior=root/'lab/k1-cpu-completion-model-20261012-r8'
plan=read(prior/'payload/plan.json')
evaluation=read(prior/'evaluation.json')
shutil.copy2(prior/'payload/measure',bundle/'fixture.elf')
for name in ('fragment-compare.py','binary-input.py','common.py','state3.py','state6.py','state8.py'):
 shutil.copy2(here/name,bundle/name)
models=[]
for label,path,engine in (
 ('r3',root/'lab/k1-cpu-model-20261012-r3/frozen-model.json','state3.py'),
 ('r6',root/'lab/k1-cpu-queue-model-20261012-r6/frozen-model.json','state6.py'),
 ('r8',prior/'frozen-model.json','state8.py')):
 shutil.copy2(path,bundle/'models'/f'{label}.json')
 models.append(dict(id=label,model=dict(path=f'../models/{label}.json',sha256=digest(path)),
  engine=dict(path=f'../{engine}',sha256=digest(bundle/engine))))
plugin=root/'lab/k1-cpu-model-20261012-r3/adapter-traces/trace.so'
qemu=root/'lab/k1-qemu-feasibility-20261011/jdsk-qemu/bin/qemu-riscv64'
env=dict(os.environ,LD_LIBRARY_PATH=str(qemu.parent.parent/'lib'))
selected=['r8-reorder-add-mul-c1-p9','r8-reorder-mul-load-c1-p9',
 'r8-reorder-add-load-c1-p21','r8-reorder-add-mul-c4-p9']
write(work/'execution-budget.json',dict(examples=4,qemu_calls=8,timeout_seconds_per_call=45,
 maximum_recorded_instructions_per_call=20000,native_calls=0,scope='historical regression; not independent accuracy'))
total_trace=0;records=[]
for name in selected:
 old=next(row for row in evaluation['semantic_validation'] if row['group']==name)
 arms=[];checks=[];trace_cost=0
 for identifier in old['ids']:
  body=binary.loop(bundle/'fixture.elf',identifier)
  dumpdir=work/(identifier+'-qemu-dumps');dumpdir.mkdir()
  prefix=bundle/'traces'/identifier
  argv=[str(qemu),'-cpu','max,vlen=256,elen=64,vext_spec=v1.0','-plugin',
   f'{plugin},start={body["first"]},end={body["last"]+4},out={prefix},max=20000',
   str(bundle/'fixture.elf'),'check','test',str(dumpdir)]
  write(bundle/'commands'/f'{identifier}.json',argv)
  start=time.perf_counter()
  with (bundle/'logs'/f'{identifier}.log').open('x') as stream:
   subprocess.run(argv,env=env,stdout=stream,stderr=subprocess.STDOUT,check=True,timeout=45)
  elapsed=time.perf_counter()-start;trace_cost+=elapsed
  path=Path(str(prefix)+'-cpu0.jsonl')
  audit=binary.trace(path,body,[3,17])
  for n in (3,17):
   for mode,source in (('native',prior/'run-test/dumps'),('reference',prior/'qemu-dumps')):
    source=source/f'{identifier}-{n}.bin';target=bundle/'dumps'/f'{identifier}-{n}-{mode}.bin'
    shutil.copy2(source,target)
   if (dumpdir/f'{identifier}-{n}.bin').read_bytes()!=(prior/'qemu-dumps'/f'{identifier}-{n}.bin').read_bytes():
    raise ValueError('新 QEMU 完整输出与旧参考不同。')
  arms.append(dict(elf=dict(path='../fixture.elf',sha256=digest(bundle/'fixture.elf')),
   symbol=identifier,trace=dict(path='../traces/'+path.name,sha256=digest(path)),iterations=[3,17]))
  print(identifier,audit['instructions'],f'{elapsed:.4f} s',flush=True)
 for n in (3,17):
  def evidence(identifier,mode):
   path=bundle/'dumps'/f'{identifier}-{n}-{mode}.bin'
   return dict(path='../dumps/'+path.name,sha256=digest(path))
  checks.append(dict(id=f'length-{n}',baseline=evidence(old['ids'][0],'native'),
   candidate=evidence(old['ids'][1],'native'),reference=evidence(old['ids'][0],'reference'),
   elf_sha256=[digest(bundle/'fixture.elf')]*2))
 manifest=dict(schema=1,id=name,primary_model='r8',models=models,baseline=arms[0],candidate=arms[1],
  contract=dict(work_id=name,input_description='输入字节均为 1，整数计算，检查长度为 3 与 17。',
   boundary='固定循环体、计数减一与回边；不含函数首尾。',
   compile_context='原 R8 同一 ELF 的实际函数；历史受控片段，未提取重编译。',
   live_inputs=['寄存器初值见 R8 源码。','只读输入缓冲区。'],live_outputs=['完整输入、输出与保护区转储。'],
   memory_effects=['只读输入；结果在测量循环之外保存。'],equivalent_work_per_iteration=True,
   cpu=0,threads=1,boundary_kind='steady-loop',memory_scenario='hot-read-only',entry_state='repeated-steady-loop'),
  numerical_checks=checks,cost_seconds=dict(build=None,trace_acquisition=trace_cost,native_measurement=None))
 write(bundle/'manifests'/f'{name}.json',manifest)
 records.append(dict(id=name,ids=old['ids'],historical_native_cycles=old['observed_cycles'],
  historical_native_ratio=old['observed_ratio'],historical_repeat_ratio_range=old['paired_repeat_ratio_range'],
  trace_acquisition_seconds=trace_cost))
 total_trace+=trace_cost
write(bundle/'historical-oracle.json',dict(records=records,source_report='2026-10-12-k1-cpu-completion-model-r8.md',
 source_evaluation_sha256=digest(prior/'evaluation.json'),independent_validation=False))
write(work/'trace-acquisition-receipt.json',dict(qemu_sha256=digest(qemu),plugin_sha256=digest(plugin),
 binary_sha256=digest(bundle/'fixture.elf'),calls=8,total_seconds=total_trace,native_calls=0))
