#!/usr/bin/env python3
"""Offload hybrid SSM full-answer testing; collect and judge locally in tmux."""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
from zoneinfo import ZoneInfo

HERE=Path(__file__).resolve().parent
def module(name,folder=HERE):
    spec=importlib.util.spec_from_file_location(name,folder/(name+'.py'))
    result=importlib.util.module_from_spec(spec); spec.loader.exec_module(result); return result
profile=module('start-k1-prefill-profile'); base=module('start-k1-ssm-conv')
FILES=tuple(dict.fromkeys((*base.FILES,'k1-ssm-quality.py','score-k1-ssm-quality.py',
    'run-k1-ssm-quality-board.sh','mtp-quality.py','mtp-quality-checks.py',
    'score-mtp-quality.py','document_quality_suite.py','judge-shared-document-cache.py')))

def collect(root,key_file,score_only=False):
    try:
        if not score_only:
            profile.collect(root)
            (root/'collection-exit-status').write_text('0\n')
        run=json.loads((root/'run.json').read_text())
        for name,digest in run['code_sha256'].items():
            if hashlib.sha256((root/name).read_bytes()).hexdigest() != digest:
                raise ValueError('staged source changed: '+name)
        if (root/'exit-status').read_text().strip() != '0':
            raise RuntimeError('board qualification/generation failed; artifacts collected')
        module('score-k1-ssm-quality',root).score(root,key_file)
        (root/'collector-exit-status').write_text('0\n')
    except BaseException as error:
        (root/'collector-exit-status').write_text('1\n')
        (root/'scoring-phase').write_text('failed: '+type(error).__name__+': '+str(error)[:200]+'\n')
        raise

def start(root,evidence,key_file,base_url,judge_model):
    if not key_file.is_file(): raise FileNotFoundError('local judge key file missing')
    if (evidence/'exit-status').read_text().strip() != '0': raise ValueError('baseline evidence is incomplete')
    subprocess.run(['tmux','-V'],check=True,capture_output=True)
    root.mkdir(parents=True,exist_ok=False)
    files={name:HERE/name for name in FILES}
    files['cached-document-chat.py']=HERE.parent/'serve/cached-document-chat.py'
    files['expected-provenance.json']=evidence/'provenance.json'
    for name,path in files.items(): shutil.copyfile(path,root/name)
    (root/'.gitignore').write_text('profile-artifacts.tar.gz\n*.download\n')
    board=json.loads((evidence/'run.json').read_text())['board']
    home=profile.launch.remote(board,['python3','-c','from pathlib import Path; print(Path.home())'])
    target=home+'/Projects/riscv-accl-bench-2026-09-27/'+root.name
    run={'board':board,'remote_root':target,'evidence':str(evidence),'board_session':'ssm_quality_'+root.name,
         'collector_session':'ssm_quality_collect_'+root.name,
         'dispatch_time':datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
         'judge':{'base_url':base_url,'model':judge_model,'orders':2},
         'code_sha256':{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files}}
    (root/'run.json').write_text(json.dumps(run,indent=2)+'\n')
    profile.launch.remote(board,['mkdir',target])
    # Only source and public benchmark evidence cross to the board. The key
    # is read by the workstation scorer and is never staged or serialized.
    subprocess.run(['scp',*[str(root/name) for name in (*files,'run.json')],f'{board}:{target}/'],check=True,timeout=120)
    invocation=shlex.join([sys.executable,str(Path(__file__).resolve()),'--collect-only','--run-dir',str(root),'--key-file',str(key_file)])
    subprocess.run(['tmux','new-session','-d','-s',run['collector_session'],
                    invocation+' >> '+shlex.quote(str(root/'collector.log'))+' 2>&1'],check=True)
    try:
        profile.launch.remote(board,['tmux','new-session','-d','-s',run['board_session'],
            shlex.join(['bash',target+'/run-k1-ssm-quality-board.sh',target])])
    except BaseException:
        subprocess.run(['tmux','kill-session','-t',run['collector_session']],check=False); raise
    print(json.dumps({k:v for k,v in run.items() if k != 'code_sha256'},indent=2),flush=True)

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir',type=Path,default=HERE.parent/'reports/raw'/
        ('k1-ssm-quality-'+datetime.datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y%m%d-%H%M%S')))
    parser.add_argument('--evidence',type=Path,default=HERE.parent/'reports/raw/k1-fast-20261001-224957')
    parser.add_argument('--key-file',type=Path,default=Path.home()/'.secret_ai_key')
    parser.add_argument('--base-url',default='https://api.xiaomimimo.com/v1')
    parser.add_argument('--judge-model',default='mimo-v2.6-flash')
    parser.add_argument('--collect-only',action='store_true'); parser.add_argument('--score-only',action='store_true')
    args=parser.parse_args()
    if args.collect_only or args.score_only: collect(args.run_dir.resolve(),args.key_file.resolve(),args.score_only)
    else: start(args.run_dir.resolve(),args.evidence.resolve(),args.key_file.resolve(),args.base_url,args.judge_model)
