#!/usr/bin/env python3
"""Offload fixed K32 M1 testing and verified collection using direct board SSH."""
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

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('launcher', HERE/'start-k1-prefill-profile.py')
launcher = importlib.util.module_from_spec(spec); spec.loader.exec_module(launcher)
FILES = ('k1-ime-m1-k32.py', 'make-k1-ime-m1-k32.py', 'k1-gemm-routing.py',
         'make-k1-gemm-routing.py', 'k1-ime-test.py', 'make-k1-ime-candidate.py',
         'k1-fast-test.py', 'bench-lifecycle.py', 'test-k1-ime-m1.cpp',
         'test-k1-ime-m1-graph.cpp', 'test-k1-ime-m1-state.cpp', 'run-k1-ime-m1-k32-board.sh')
COLLECTOR_FILES = ('start-k1-ime-m1-k32.py', 'start-k1-prefill-profile.py', 'start-k1-fast-test.py')


def collect(root):
    run = json.loads((root/'run.json').read_text())
    # Copy back staged code independently: the profile archive contains result
    # extensions and C++ sources, but deliberately omits Python/shell files.
    launcher.collect(root)
    code = 'import hashlib,json,sys; from pathlib import Path; p=Path(sys.argv[1]); names=json.loads(sys.argv[2]); print(json.dumps({n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in names}))'
    hashes = json.loads(launcher.launch.remote(run['board'], ['python3', '-c', code, run['remote_root'], json.dumps(list(run['code_sha256']))]))
    if hashes != run['code_sha256']:
        raise ValueError('remote staged code hashes changed')
    for name, expected in run['code_sha256'].items():
        if launcher.hashlib.sha256((root/name).read_bytes()).hexdigest() != expected:
            raise ValueError('local staged code hashes changed: '+name)
    for name, expected in run['collector_code_sha256'].items():
        if launcher.hashlib.sha256((root/name).read_bytes()).hexdigest() != expected:
            raise ValueError('frozen collector code changed')
    (root/'collection-verification.json').write_text(json.dumps(dict(board_exit_status=(root/'exit-status').read_text().strip(),
        staged_code_verified=True, remote_staged_code_sha256=hashes, collector_code_verified=True), indent=2)+'\n')
    if (root/'exit-status').read_text().strip() != '0':
        raise RuntimeError('board M1 pilot failed; preserved artifacts collected')


def start(root, evidence, routing, board):
    if (evidence/'exit-status').read_text().strip() != '0' or (routing/'exit-status').read_text().strip() != '0':
        raise ValueError('requires successful frozen baseline evidence')
    root.mkdir(parents=True, exist_ok=False)
    remote = launcher.launch.remote
    home = remote(board, ['python3', '-c', 'from pathlib import Path; print(Path.home())'])
    target = home+'/Projects/riscv-accl-bench-2026-09-27/'+root.name
    run = dict(board=board, remote_root=target, evidence=str(evidence), routing_evidence=str(routing),
               board_session='k1_m1_'+root.name, collector_session='k1_m1_collect_'+root.name,
               dispatch_time=datetime.datetime.now(ZoneInfo('Asia/Singapore')).isoformat(),
               code_sha256={n: launcher.hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in FILES},
               collector_code_sha256={n: launcher.hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in COLLECTOR_FILES})
    (root/'run.json').write_text(json.dumps(run, indent=2)+'\n')
    shutil.copyfile(evidence/'provenance.json', root/'expected-provenance.json')
    shutil.copyfile(routing/'provenance.json', root/'routing-provenance.json')
    for n in (*FILES, *COLLECTOR_FILES):
        shutil.copyfile(HERE/n, root/n)
    remote(board, ['mkdir', target])
    subprocess.run(['scp', *[str(root/n) for n in (*FILES, 'run.json', 'expected-provenance.json', 'routing-provenance.json')],
                    f'{board}:{target}/'], check=True, timeout=120)
    remote(board, ['tmux', 'new-session', '-d', '-s', run['board_session'],
                  shlex.join(['bash', target+'/run-k1-ime-m1-k32-board.sh', target])])
    invocation = shlex.join([sys.executable, str(root/'start-k1-ime-m1-k32.py'), '--collect-only', '--run-dir', str(root)])
    command = invocation+' >> '+shlex.quote(str(root/'collector.log'))+' 2>&1; m1_collect_status=$?; printf "%s\\n" "$m1_collect_status" > '+shlex.quote(str(root/'collector-exit-status'))
    subprocess.run(['tmux', 'new-session', '-d', '-s', run['collector_session'], command], check=True)
    print(json.dumps(run), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, default=HERE.parent/'reports/raw'/('k1-ime-m1-k32-'+datetime.datetime.now(ZoneInfo('Asia/Singapore')).strftime('%Y%m%d-%H%M%S')))
    parser.add_argument('--evidence', type=Path, default=HERE.parent/'reports/raw/k1-fast-20261001-224957')
    parser.add_argument('--routing-evidence', type=Path, default=HERE.parent/'reports/raw/k1-gemm-routing-20261003-005740')
    parser.add_argument('--board', default='musepipro')
    parser.add_argument('--collect-only', action='store_true')
    args = parser.parse_args()
    if args.collect_only:
        collect(args.run_dir.resolve())
    else:
        start(args.run_dir.resolve(), args.evidence.resolve(), args.routing_evidence.resolve(), args.board)
