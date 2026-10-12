#!/usr/bin/env python3
"""Offload channels-major SSM convolution tests and verified collection to tmux."""
import argparse
import datetime
import importlib.util
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
from zoneinfo import ZoneInfo

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('launcher',HERE/'start-k1-prefill-profile.py')
launcher=importlib.util.module_from_spec(spec); spec.loader.exec_module(launcher)
FILES=('k1-ssm-conv.py','make-k1-ssm-conv.py','spine-k1-ssm-conv.h','spine-k1-ssm-kernel.h',
       'test-k1-ssm-conv.cpp','test-k1-ssm-state.cpp','run-k1-ssm-conv-board.sh',
       'k1-ime-test.py','make-k1-ime-candidate.py','make-k1-gemm-routing.py','bench-lifecycle.py','k1-fast-test.py')

def collect(root):
    launcher.collect(root)
    run=json.loads((root/'run.json').read_text())
    for name in FILES:
        expected=run['code_sha256'][name]
        if launcher.hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('staged code changed: '+name)
    if (root/'exit-status').read_text().strip()!='0':
        raise RuntimeError('board convolution run failed; inspect summary and logs')

def start(root,evidence):
    if (evidence/'exit-status').read_text().strip()!='0':
        raise ValueError('requires successful frozen-runtime evidence')
    root.mkdir(parents=True,exist_ok=False)
    old=json.loads((evidence/'run.json').read_text())
    board=old['board']; remote=launcher.launch.remote
    home=remote(board,['python3','-c','from pathlib import Path; print(Path.home())'])
    target=home+'/Projects/riscv-accl-bench-2026-09-27/'+root.name
    session='k1_ssm_collect_verified_'+root.name
    run={'board':board,'remote_root':target,'evidence':str(evidence),
         'board_session':'k1_ssm_'+root.name,'collector_session':session,
         'dispatch_time':datetime.datetime.now(ZoneInfo('Asia/Singapore')).isoformat(),
         'code_sha256':{name:launcher.hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in FILES}}
    (root/'run.json').write_text(json.dumps(run,indent=2)+'\n')
    shutil.copyfile(evidence/'provenance.json',root/'expected-provenance.json')
    for name in FILES: shutil.copyfile(HERE/name,root/name)
    remote(board,['mkdir',target])
    subprocess.run(['scp',*[str(root/name) for name in (*FILES,'run.json','expected-provenance.json')],
                    f'{board}:{target}/'],check=True,timeout=120)
    remote(board,['tmux','new-session','-d','-s',run['board_session'],
                  shlex.join(['bash',target+'/run-k1-ssm-conv-board.sh',target])])
    invocation=shlex.join([sys.executable,str(Path(__file__).resolve()),'--collect-only','--run-dir',str(root)])
    command=invocation+' >> '+shlex.quote(str(root/'collector.log'))+' 2>&1; ssm_collect_status=$?; printf "%s\\n" "$ssm_collect_status" > '+shlex.quote(str(root/'collector-exit-status'))
    subprocess.run(['tmux','new-session','-d','-s',session,command],check=True)
    print(f'Board tmux {run["board_session"]}; verified collector {session}; results {root}',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-dir',type=Path,default=HERE.parent/'reports/raw'/
        ('k1-ssm-conv-'+datetime.datetime.now(ZoneInfo('Asia/Singapore')).strftime('%Y%m%d-%H%M%S')))
    p.add_argument('--evidence',type=Path,default=HERE.parent/'reports/raw/k1-fast-20261001-224957')
    p.add_argument('--collect-only',action='store_true'); args=p.parse_args()
    if args.collect_only: collect(args.run_dir.resolve())
    else: start(args.run_dir.resolve(),args.evidence.resolve())
