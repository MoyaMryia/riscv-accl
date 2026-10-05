#!/usr/bin/env python3
"""Dispatch adaptive policy state checks and a gated paired screen in tmux."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
profile=load('profile',HERE/'start-k1-prefill-profile.py')
FILES=('adaptive-mtp-test.py','score-adaptive-mtp.py','run-adaptive-mtp-board.sh','mtp-quality.py',
    'mtp-quality-checks.py','score-mtp-quality.py','k1-fast-test.py','bench-lifecycle.py',
    'document_quality_suite.py','judge-shared-document-cache.py')

def prepare_build(root,evidence,reuse_build=None):
    if (root/'build-run.json').exists():return
    root.mkdir(parents=True,exist_ok=False)
    expected=json.loads((evidence/'expected-provenance.json').read_text())
    source=Path(next(p for p in expected['artifacts_sha256'] if p.endswith('/llama-server'))).parents[2]
    board=json.loads((evidence/'run.json').read_text())['board']
    home=profile.launch.remote(board,['python3','-c','from pathlib import Path; print(Path.home())'])
    target=home+'/Projects/riscv-accl-bench-2026-09-27/'+root.name
    original=root/'patch-base';original.mkdir()
    names=('server-context.cpp','server-schema.cpp','server-task.h','server-task.cpp')
    subprocess.run(['scp',*[f'{board}:{source}/tools/server/{n}' for n in names],str(original)],check=True,timeout=90)
    generator=load('generator',HERE/'make-adaptive-mtp.py')
    generator.generate(original,root/'adaptive-mtp.patch')
    for name in ('build-adaptive-mtp.py','test-spine-mtp-policy.cpp'):shutil.copyfile(HERE/name,root/name)
    build={'board':board,'remote_root':target,'baseline_source':str(source)}
    if reuse_build:build['reuse_build_root']=str(reuse_build)
    (root/'build-run.json').write_text(json.dumps(build,indent=2)+'\n')
    (root/'.gitignore').write_text('collector.log\nprofile-artifacts.tar.gz\n*.download\n')
    profile.launch.remote(board,['mkdir',target])
    subprocess.run(['scp',*[str(root/n) for n in ('build-run.json','adaptive-mtp.patch','build-adaptive-mtp.py','test-spine-mtp-policy.cpp')],
        f'{board}:{target}/'],check=True,timeout=90)
    invocation=shlex.join(['python3',target+'/build-adaptive-mtp.py',target])+' > '+shlex.quote(target+'/build.log')+' 2>&1'
    profile.launch.remote(board,['tmux','new-session','-d','-s','adaptive_build_'+root.name,invocation])

def collect(root,key_file):
    try:
        profile.collect(root)
        scorer=load('scorer',root/'score-adaptive-mtp.py')
        result=scorer.score(root,key_file)
        (root/'collector-exit-status').write_text(('0' if result['candidate_qualified'] else '2')+'\n')
    except BaseException as error:
        (root/'collector-exit-status').write_text('1\n')
        (root/'scoring-phase').write_text('failed: '+type(error).__name__+'\n');raise

def start(root,evidence,key_file,reuse_build=None,infrastructure=False):
    if not key_file.is_file():raise FileNotFoundError('judge key missing')
    prepare_build(root,evidence,reuse_build)
    build=json.loads((root/'build-run.json').read_text());board=build['board'];target=build['remote_root']
    if (root/'run.json').exists():raise ValueError('already dispatched; use collection-only recovery')
    files={n:HERE/n for n in FILES}
    files.update({'cached-document-chat.py':HERE.parent/'serve/cached-document-chat.py',
        'expected-provenance.json':evidence/'expected-provenance.json',
        'validation-provenance.json':evidence/'provenance.json','validation-run.json':evidence/'run.json'})
    for name,path in files.items():shutil.copyfile(path,root/name)
    staged=list(files)+['adaptive-mtp.patch','build-adaptive-mtp.py','test-spine-mtp-policy.cpp','build-run.json']
    manifest={'board':board,'remote_root':target,'evidence':str(evidence),
        'screen':'infrastructure' if infrastructure else 'quality',
        'board_session':'adaptive_test_'+root.name,'collector_session':'adaptive_collect_'+root.name,
        'judge':{'base_url':'https://api.xiaomimimo.com/v1','model':'mimo-v2.6-flash','orders':2},
        'code_sha256':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in staged}}
    (root/'run.json').write_text(json.dumps(manifest,indent=2)+'\n')
    subprocess.run(['scp',*[str(root/n) for n in files],str(root/'run.json'),f'{board}:{target}/'],check=True,timeout=90)
    invocation=shlex.join([sys.executable,str(Path(__file__).resolve()),'--collect-only','--run-dir',str(root),'--key-file',str(key_file)])
    invocation+=' >> '+shlex.quote(str(root/'collector.log'))+' 2>&1'
    subprocess.run(['tmux','new-session','-d','-s',manifest['collector_session'],invocation],check=True)
    try:
        profile.launch.remote(board,['tmux','new-session','-d','-s',manifest['board_session'],
            shlex.join(['bash',target+'/run-adaptive-mtp-board.sh',target])])
    except BaseException:
        subprocess.run(['tmux','kill-session','-t',manifest['collector_session']],check=False);raise
    print(json.dumps({k:v for k,v in manifest.items() if k!='code_sha256'},indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-dir',type=Path,required=True)
    p.add_argument('--evidence',type=Path,default=HERE.parent/'reports/raw/k1-validation-20261003-124720')
    p.add_argument('--key-file',type=Path,default=Path.home()/'.secret_ai_key');p.add_argument('--collect-only',action='store_true')
    p.add_argument('--reuse-build',type=Path,help='board run root with identical patch/sources and compiled server objects')
    p.add_argument('--infrastructure',action='store_true',help='bounded timing screen; retain quality failures and exclude capped answers from grading')
    args=p.parse_args()
    if args.collect_only:collect(args.run_dir.resolve(),args.key_file.resolve())
    else:start(args.run_dir.resolve(),args.evidence.resolve(),args.key_file.resolve(),args.reuse_build,args.infrastructure)
