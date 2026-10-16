"""记录收集时的系统工具身份，不补写历史构建状态。"""
import hashlib,json,os,shutil,subprocess
from pathlib import Path
assert os.environ.get('TMUX') and os.environ.get('K1_PACKAGE_LOCK_FD')=='9'
os.fstat(9)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
rows={}
for name,option in [('cmake','--version'),('ninja','--version'),('python3','--version'),('git','--version'),('tmux','-V'),('flock','--version'),('ldd','--version'),('ld','--version')]:
 p=shutil.which(name)
 result=subprocess.run([p,option],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=True)
 rows[name]={'path':p,'resolved_path':str(Path(p).resolve()),'sha256':sha(p),'version':result.stdout}
libraries={}
for log in Path('validation').glob('ldd-*.log'):
 for word in log.read_text().split():
  if word.startswith('/') and Path(word).is_file():
   libraries[word]={'resolved_path':str(Path(word).resolve()),'sha256':sha(word)}
Path('post-validation-tools.json').write_text(json.dumps({'scope':'post-validation tool and library identity','tools':rows,'resolved_libraries':libraries},indent=2)+'\n')
