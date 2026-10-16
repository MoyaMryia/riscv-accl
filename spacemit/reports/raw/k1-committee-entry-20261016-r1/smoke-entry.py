"""在新入口持有共用锁时检查迁移部署，不执行性能请求。"""
from pathlib import Path
import hashlib,json,os,re,signal,subprocess,time,urllib.request
root=Path(__file__).resolve().parent
assert os.environ.get('TMUX'), 'use tmux'
assert subprocess.run(['pgrep','-x','llama-server'],stdout=subprocess.DEVNULL).returncode==1,'another server is active'
lock=Path.home()/'Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock'
models={'2B':('Qwen3.5-2B-MTP-Q4_0-embQ4_0-dv64k.gguf','56f0ddd90dfa0e2456af6cb4718ece419678d21a75d65e27353319b5e431a2fa'),'4B':('Qwen3.5-4B-MTP-Q4_0-embQ4_0-dv64k.gguf','0adf6cce5df53921606033c39a13fae2054543b78af0e7ff98860e86f078ac0f')}
def children(pid):
 result=[]
 p=Path(f'/proc/{pid}/task/{pid}/children')
 if p.exists():
  for child in p.read_text().split(): result+=[int(child),*children(int(child))]
 return result
def get_json(path):
 with urllib.request.urlopen('http://127.0.0.1:18555'+path,timeout=5) as r: return json.load(r)
checks=[]
for size,(name,expected_sha) in models.items():
 session='k1_committee_smoke_'+size.lower();run=root/'runs'/session;pid=None
 try:
  subprocess.run(['bash',str(root/'deploy.sh'),str(Path.home()/'Projects/spacemit-llama/models'/name),'--session',session,'--port','18555','--runs',str(root/'runs')],check=True)
  deadline=time.monotonic()+300
  while time.monotonic()<deadline:
   if (run/'exit-status').exists(): raise RuntimeError('server exited before health: '+(run/'server.log').read_text()[-2500:])
   try:
    pane=int(subprocess.check_output(['tmux','list-panes','-t','='+session,'-F','#{pane_pid}'],text=True).strip())
    matching=[]
    for candidate in children(pane):
     try:
      if os.readlink(f'/proc/{candidate}/exe')==str(root/'runtime/build/bin/llama-server'): matching.append(candidate)
     except FileNotFoundError: pass
    if len(matching)==1:
     pid=matching[0]
     assert Path(f'/proc/{pid}/fd/9').stat().st_ino==lock.stat().st_ino
     fdinfo=Path(f'/proc/{pid}/fdinfo/9').read_text()
     assert 'FLOCK' in fdinfo and 'WRITE' in fdinfo,'server has no common lock'
     health=get_json('/health')
     if health.get('status')=='ok': break
   except (urllib.error.URLError,TimeoutError,ConnectionError,subprocess.CalledProcessError): pass
   time.sleep(1)
  else: raise RuntimeError('deployment health deadline')
  props=get_json('/props')
  assert props['total_slots']==1 and props['default_generation_settings']['n_ctx']==12288
  assert props['default_generation_settings']['params']['speculative.types']=='none'
  launch=json.loads((run/'launch.json').read_text())
  assert launch['model_sha256']==expected_sha
  assert launch['argv']==[str(root/'runtime/build/bin/llama-server'),'-m',str(Path.home()/'Projects/spacemit-llama/models'/name),'--alias','local','--port','18555']
  lines=re.findall(r'^K1_EFFECTIVE_DEFAULTS (.+)$',(run/'server.log').read_text(),re.M)
  expected=dict(threads='4',batch_threads='4',batch='32',ubatch='32',context='12288',slots='1',flash='1',gpu='0',key='f16',value='f16',mask='3')
  assert len(lines)==1 and dict(x.split('=',1) for x in lines[0].split())==expected
  (run/'properties.json').write_text(json.dumps(props,indent=2)+'\n')
  (run/'health.json').write_text(json.dumps(health,indent=2)+'\n')
  (run/'lock-fdinfo.txt').write_text(fdinfo)
  checks.append({'model':size,'status':'pass','model_sha256':expected_sha,'defaults':expected,'server_pid':pid,'common_lock_inode':lock.stat().st_ino,'inference_requests':0})
 finally:
  if pid is not None:
   try:
    assert os.readlink(f'/proc/{pid}/exe')==str(root/'runtime/build/bin/llama-server')
    os.kill(pid,signal.SIGTERM)
   except FileNotFoundError: pass
  if run.exists():
   for _ in range(30):
    if (run/'exit-status').exists(): break
    time.sleep(1)
   assert (run/'exit-status').read_text().strip()=='0','deployment exit differs'
record={'status':'pass','checks':checks,'scope':'new one-command entry; model identity, actual defaults, common lock and health only','performance_requests':0,'tool_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(root/'smoke-summary.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
