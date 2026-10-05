#!/usr/bin/env python3
"""Start checkpoint-MTP answer testing in board tmux; collect and judge locally."""
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
spec=importlib.util.spec_from_file_location('profile',HERE/'start-k1-prefill-profile.py')
profile=importlib.util.module_from_spec(spec); spec.loader.exec_module(profile)
FILES=('mtp-quality.py','mtp-quality-checks.py','score-mtp-quality.py','run-mtp-quality-board.sh',
       'k1-fast-test.py','bench-lifecycle.py','document_quality_suite.py','judge-shared-document-cache.py')


def collect(root,key_file,base_url,model):
    try:
        profile.collect(root)
        spec=importlib.util.spec_from_file_location('score',root/'score-mtp-quality.py')
        scorer=importlib.util.module_from_spec(spec); spec.loader.exec_module(scorer)
        summary=scorer.score(root,key_file,base_url,model)
        status=0 if summary['candidate_useful_in_pilot'] else 2
        (root/'collector-exit-status').write_text(str(status)+'\n')
    except BaseException as error:
        (root/'collector-exit-status').write_text('1\n')
        (root/'scoring-phase').write_text('failed: '+type(error).__name__+': '+str(error)[:200]+'\n')
        raise


def start(root,evidence,key_file,base_url,model):
    if not key_file.is_file(): raise FileNotFoundError('judge key file missing')
    if (evidence/'exit-status').read_text().strip()!='0': raise ValueError('requires completed validation provenance')
    prior=json.loads((evidence/'run.json').read_text()); board=prior['board']
    # Ensure tmux exists before dispatch; the foreground invocation only stages code.
    subprocess.run(['tmux','-V'],check=True,capture_output=True)
    root.mkdir(parents=True,exist_ok=False)
    files={n:HERE/n for n in FILES}
    files.update({'cached-document-chat.py':HERE.parent/'serve/cached-document-chat.py',
        'expected-provenance.json':evidence/'expected-provenance.json',
        'validation-provenance.json':evidence/'provenance.json','validation-run.json':evidence/'run.json'})
    for name,path in files.items(): shutil.copyfile(path,root/name)
    (root/'.gitignore').write_text('collector.log\nprofile-artifacts.tar.gz\n*.download\n')
    home=profile.launch.remote(board,['python3','-c','from pathlib import Path; print(Path.home())'])
    target=home+'/Projects/riscv-accl-bench-2026-09-27/'+root.name
    profile.launch.remote(board,['mkdir',target])
    subprocess.run(['scp',*[str(root/n) for n in files],f'{board}:{target}/'],check=True,timeout=90)
    manifest={'board':board,'remote_root':target,'evidence':str(evidence),
        'board_session':'mtp_quality_'+root.name,'collector_session':'mtp_quality_collect_'+root.name,
        'judge':{'base_url':base_url,'model':model,'orders':2},
        'code_sha256':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in files}}
    (root/'run.json').write_text(json.dumps(manifest,indent=2)+'\n')
    subprocess.run(['scp',str(root/'run.json'),f'{board}:{target}/'],check=True,timeout=30)
    invocation=shlex.join([sys.executable,str(Path(__file__).resolve()),'--collect-only','--run-dir',str(root),
        '--key-file',str(key_file),'--base-url',base_url,'--judge-model',model])
    invocation+=' >> '+shlex.quote(str(root/'collector.log'))+' 2>&1'
    subprocess.run(['tmux','new-session','-d','-s',manifest['collector_session'],invocation],check=True)
    try:
        profile.launch.remote(board,['tmux','new-session','-d','-s',manifest['board_session'],
            shlex.join(['bash',target+'/run-mtp-quality-board.sh',target])])
    except BaseException:
        subprocess.run(['tmux','kill-session','-t',manifest['collector_session']],check=False); raise
    print(json.dumps({k:v for k,v in manifest.items() if k!='code_sha256'},indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir',type=Path,default=HERE.parent/'reports/raw'/
        ('mtp-quality-'+datetime.datetime.now(ZoneInfo('Asia/Singapore')).strftime('%Y%m%d-%H%M%S')))
    parser.add_argument('--evidence',type=Path,default=HERE.parent/'reports/raw/k1-validation-20261003-124720')
    parser.add_argument('--key-file',type=Path,default=Path.home()/'.secret_ai_key')
    parser.add_argument('--base-url',default='https://api.xiaomimimo.com/v1'); parser.add_argument('--judge-model',default='mimo-v2.6-flash')
    parser.add_argument('--collect-only',action='store_true'); args=parser.parse_args()
    if args.collect_only: collect(args.run_dir.resolve(),args.key_file.resolve(),args.base_url,args.judge_model)
    else: start(args.run_dir.resolve(),args.evidence.resolve(),args.key_file.resolve(),args.base_url,args.judge_model)
