#!/usr/bin/env python3
"""Launch request-only K1 profiling and collection in board/workstation tmux."""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
FILES = ('profile-k1-prefill.py', 'run-k1-prefill-profile-board.sh', 'bench-lifecycle.py', 'k1-fast-test.py')
spec = importlib.util.spec_from_file_location('launch', HERE / 'start-k1-fast-test.py')
launch = importlib.util.module_from_spec(spec); spec.loader.exec_module(launch)


def collect(root):
    run = json.loads((root / 'run.json').read_text())
    board, target = run['board'], run['remote_root']
    deadline = time.monotonic() + 86400
    while time.monotonic() < deadline:
        try:
            status = launch.remote(board, ['cat', target + '/exit-status']); break
        except (subprocess.SubprocessError, OSError):
            time.sleep(60)
    else:
        raise TimeoutError('collector deadline exceeded')
    names = json.loads(launch.remote(board, ['python3', '-c',
        'import json,sys; from pathlib import Path; print(json.dumps([p.name for p in Path(sys.argv[1]).iterdir() '
        'if p.is_file() and (p.suffix in (".json", ".log", ".md", ".txt", ".err", ".data") '
        'or p.name in ("phase", "exit-status"))]))', target]))
    for name in names:
        if Path(name).name != name:
            raise ValueError('invalid artifact name')
        subprocess.run(['scp', f'{board}:{target}/{name}', str(root)], check=True, timeout=180)
    (root / 'exit-status').write_text(status + '\n')
    print(f'Profile exit {status}; results {root}', flush=True)


def start(root, evidence):
    root.mkdir(parents=True, exist_ok=False)
    if (evidence / 'exit-status').read_text().strip() != '0':
        raise ValueError('requires completed fast-test provenance')
    old = json.loads((evidence / 'run.json').read_text())
    expected = json.loads((evidence / 'provenance.json').read_text())
    board = old['board']
    home = launch.remote(board, ['python3', '-c', 'from pathlib import Path; print(Path.home())'])
    target = home + '/Projects/riscv-accl-bench-2026-09-27/' + root.name
    (root / 'expected-provenance.json').write_text(json.dumps(expected, indent=2) + '\n')
    launch.remote(board, ['mkdir', target])
    subprocess.run(['scp', *[str(HERE / n) for n in FILES], str(root / 'expected-provenance.json'),
                    f'{board}:{target}/'], check=True, timeout=90)
    run = {'board': board, 'remote_root': target, 'evidence': str(evidence),
           'board_session': 'k1_profile_' + root.name, 'tokens': 2048,
           'code_sha256': {n: hashlib.sha256((HERE / n).read_bytes()).hexdigest() for n in FILES}}
    (root / 'run.json').write_text(json.dumps(run, indent=2) + '\n')
    launch.remote(board, ['tmux', 'new-session', '-d', '-s', run['board_session'],
                         shlex.join(['bash', target + '/run-k1-prefill-profile-board.sh', target])])
    session = 'k1_profile_collect_' + root.name
    invocation = shlex.join([sys.executable, str(Path(__file__).resolve()), '--collect-only', '--run-dir', str(root)])
    invocation += ' >> ' + shlex.quote(str(root / 'collector.log')) + ' 2>&1'
    subprocess.run(['tmux', 'new-session', '-d', '-s', session, invocation], check=True)
    print(f'Board tmux {run["board_session"]}; collector {session}; results {root}', flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-dir', type=Path, default=HERE.parent / 'reports/raw' /
                   ('k1-profile-' + datetime.datetime.now(ZoneInfo('Asia/Singapore')).strftime('%Y%m%d-%H%M%S')))
    p.add_argument('--evidence', type=Path, default=HERE.parent / 'reports/raw/k1-fast-20261001-224957')
    p.add_argument('--collect-only', action='store_true')
    args = p.parse_args()
    if args.collect_only:
        collect(args.run_dir.resolve())
    else:
        start(args.run_dir.resolve(), args.evidence.resolve())
