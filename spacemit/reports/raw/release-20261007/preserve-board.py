#!/usr/bin/env python3
"""Read post-run hashes and build/source state from the declared board run."""
import json,subprocess,shlex,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve(); output=Path(sys.argv[2]).resolve()
run=json.loads((root/'run.json').read_text()); provenance=json.loads((root/'provenance.json').read_text())
manifest=json.loads((root/'manifest.json').read_text()); target=run['remote_root']
files=[target+'/source/'+n for n in manifest['patched_source_sha256']]
files += [target+'/build/bin/llama-server',target+'/build/bin/libggml-cpu.so.0.16.0',target+'/build/CMakeCache.txt',target+'/build/compile_commands.json']
files += [target+'/'+n for n in run['code_sha256']]
code="""import hashlib,json,subprocess,sys
from pathlib import Path
p=Path(sys.argv[1]); files=json.loads(sys.argv[2]); settings={}
for line in (p/'build/CMakeCache.txt').read_text().splitlines():
 if line and not line.startswith(('#','//')) and '=' in line:
  name,value=line.split('=',1); settings[name.split(':')[0]]=value
source=p/'source'
expected=json.loads((p/'expected-provenance.json').read_text())
baseline=Path(next(n for n in expected['artifacts_sha256'] if n.endswith('/llama-server'))).parents[2]
baseline_modified=subprocess.check_output(['git','-C',str(baseline),'diff','--name-only','HEAD'],text=True).splitlines()
runtime={n:h for n,h in expected['artifacts_sha256'].items() if n.endswith(('libspine_tcm.so.3.0.1','libspert.so.0.6.2'))}
modified=set()
for args in (['diff','--name-only'],['diff','--cached','--name-only'],['ls-files','--others','--exclude-standard']):
 modified.update(subprocess.check_output(['git','-C',str(source),*args],text=True).splitlines())
def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as stream:
  for block in iter(lambda:stream.read(4194304),b''):h.update(block)
 return h.hexdigest()
print(json.dumps(dict(board_exit_status=int((p/'exit-status').read_text().strip()),files_sha256={n:digest(n) for n in files},source_commit=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip(),modified_source_files=sorted(modified),cmake_settings=settings,
 baseline_source_commit=subprocess.check_output(['git','-C',str(baseline),'rev-parse','HEAD'],text=True).strip(),baseline_modified_source_files=baseline_modified,baseline_source_sha256={n:digest(baseline/n) for n in expected['source_sha256']},runtime_files_sha256={n:digest(n) for n in runtime},compiler_version=subprocess.check_output([settings['CMAKE_CXX_COMPILER'],'--version'],text=True).splitlines()[0]),indent=2))
"""
command=shlex.join(['python3','-c',code,target,json.dumps(files)])
result=subprocess.check_output(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15',run['board'],command],text=True,timeout=180)
data=json.loads(result);output.write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(dict(status='post-run preservation collected',files=len(data['files_sha256']),output=str(output))))
