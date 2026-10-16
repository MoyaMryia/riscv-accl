"""核对现有 C1 的原生图耗时和短模型请求热点。"""
import datetime,fcntl,hashlib,importlib.util,json,os,subprocess,sys,traceback
from pathlib import Path
root=Path(sys.argv[1]).resolve()
base=Path.home()/'Projects/riscv-accl-bench-2026-09-27'
screen=base/'k1-local-candidates-20261008-184350'
lib=screen/'C/lib'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(name,data): (root/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def command(argv,name,env=None):
    with (root/name).open('w') as out:subprocess.run(list(map(str,argv)),env=env,stdout=out,stderr=subprocess.STDOUT,check=True,timeout=600)
status={'status':'running','started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'现有 C1 诊断，不测试新补丁。'}
write('status.json',status)
try:
 with (base/'document-quality-suite.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  identity=json.loads((base/'k1-local-candidates-C1-repeat-20261008-202900/repeat-1/result.json').read_text())['identity']
  if digest(lib/'libggml-cpu.so')!=identity['library_sha256'] or digest(lib/'libllama.so')!=identity['model_library_sha256']:raise ValueError('C1 库身份不同。')
  expected=json.loads((screen/'expected-provenance.json').read_text())
  env={k:v for k,v in os.environ.items() if not k.startswith('SPINE_')}
  env.update(SPINE_FA_WIDE_TILE='1',SPINE_FA_K1_LAYOUT='0',SPINE_K1_GEMM_ROUTE='3',SPINE_GDN_PREFILL='0',LD_LIBRARY_PATH=str(lib)+':'+expected['runtime']['LD_LIBRARY_PATH'])
  write('identity.json',dict(identity=identity,environment={k:v for k,v in env.items() if k.startswith('SPINE_') or k=='LD_LIBRARY_PATH'},binary_sha256=digest(screen/'C/test-ssm'),uname=subprocess.check_output(['uname','-a'],text=True),meminfo=Path('/proc/meminfo').read_text(),cpuinfo=Path('/proc/cpuinfo').read_text(),frequency_khz=Path('/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq').read_text().strip()))
  rows=[]
  for block in range(3):
   for c in (6144,8192):
    for tokens in (1,32):
     for mode in ((0,3) if block%2==0 else (3,0)):
      name=f'conv-c{c}-t{tokens}-b{block}-m{mode}.log'
      command([screen/'C/test-ssm','--bench',mode,c,4,tokens,1],name,env)
      data=[json.loads(s) for s in (root/name).read_text().splitlines() if s.startswith('{')]
      if len(data)!=1:raise ValueError('算子记录数量不同。')
      rows.append(dict(data[0],block=block))
      write('operators.json',rows)
  spec=importlib.util.spec_from_file_location('live_profile',root/'profile-k1-prefill.py')
  profile=importlib.util.module_from_spec(spec);spec.loader.exec_module(profile)
  class Live(profile.Profile):
   def prepare(self):
    super().prepare()
    self.env=env|{'SPINE_K1_SSM_CONV':'3'}
    receipt=json.loads((self.root/'provenance.json').read_text())
    receipt.update(c1_identity=identity,scope='现有 C1、route 3、512 输入、1 输出的诊断；每模型一次。',runtime={k:v for k,v in self.env.items() if k.startswith('SPINE_') or k=='LD_LIBRARY_PATH'})
    (self.root/'provenance.json').write_text(json.dumps(receipt,indent=2)+'\n')
  target=root/'profile';target.mkdir()
  (target/'expected-provenance.json').write_text(json.dumps(expected,indent=2)+'\n')
  Live(target,512).run()
  status['status']='complete'
except BaseException as exc:
 status.update(status='failed',error=str(exc));traceback.print_exc()
finally:
 status['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();write('status.json',status)
 (root/'exit-status').write_text('0\n' if status['status']=='complete' else '1\n')
 if status['status']!='complete':sys.exit(1)
