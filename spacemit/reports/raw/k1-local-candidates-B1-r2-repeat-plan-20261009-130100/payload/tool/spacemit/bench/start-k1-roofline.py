#!/usr/bin/env python3
"""Launch measured K1 roofline work and collection in separate tmux sessions."""
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
FILES = ('k1-roofline.py', 'k1-memory-read.cpp', 'run-k1-roofline-board.sh',
         'profile-k1-prefill.py', 'bench-lifecycle.py', 'k1-fast-test.py')
spec = importlib.util.spec_from_file_location('profile_launcher', HERE / 'start-k1-prefill-profile.py')
profile = importlib.util.module_from_spec(spec); spec.loader.exec_module(profile)


def collect(root):
    try:
        profile.collect(root)
        status = (root / 'exit-status').read_text().strip()
        (root / 'collector-exit-status').write_text(status + '\n')
    except BaseException:
        (root / 'collector-exit-status').write_text('1\n'); raise


def start(args):
    root = args.run_dir.resolve()
    root.mkdir(parents=True, exist_ok=False)
    evidence, routing = args.evidence.resolve(), args.routing_evidence.resolve()
    if any((p / 'exit-status').read_text().strip() != '0' for p in (evidence, routing)):
        raise ValueError('requires completed runtime and routing provenance')
    old = json.loads((routing / 'run.json').read_text())
    expected = json.loads((evidence / 'provenance.json').read_text())
    candidate = json.loads((routing / 'provenance.json').read_text())
    board = old['board']
    target = str(Path(old['remote_root']).parent / root.name)
    for name in FILES:
        shutil.copyfile(HERE / name, root / name)
    profile.launch.remote(board, ['mkdir', target])
    for name, data in [('expected-provenance.json', expected), ('routing-provenance.json', candidate)]:
        (root / name).write_text(json.dumps(data, indent=2) + '\n')
    run = {'board': board, 'remote_root': target, 'runtime_evidence': str(evidence),
           'routing_evidence': str(routing), 'board_session': 'k1_roofline_' + root.name,
           'collector_session': 'k1_roofline_collect_' + root.name,
           'dispatched_at': datetime.datetime.now(ZoneInfo('Asia/Singapore')).isoformat(),
           'code_sha256': {name: profile.launch.sha(root / name) for name in FILES}}
    (root / 'run.json').write_text(json.dumps(run, indent=2) + '\n')
    staged = list(FILES) + ['expected-provenance.json', 'routing-provenance.json', 'run.json']
    subprocess.run(['scp', *[str(root / name) for name in staged], f'{board}:{target}/'], check=True, timeout=90)
    invocation = shlex.join([sys.executable, str(Path(__file__).resolve()), '--collect-only', '--run-dir', str(root)])
    invocation += ' >> ' + shlex.quote(str(root / 'collector.log')) + ' 2>&1'
    subprocess.run(['tmux', 'new-session', '-d', '-s', run['collector_session'], invocation], check=True)
    try:
        profile.launch.remote(board, ['tmux', 'new-session', '-d', '-s', run['board_session'],
                                     shlex.join(['bash', target + '/run-k1-roofline-board.sh', target])])
    except BaseException:
        subprocess.run(['tmux', 'kill-session', '-t', run['collector_session']], check=False)
        raise
    print(json.dumps(run, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, default=HERE.parent / 'reports/raw' /
                        ('k1-roofline-' + datetime.datetime.now(ZoneInfo('Asia/Singapore')).strftime('%Y%m%d-%H%M%S')))
    parser.add_argument('--evidence', type=Path, default=HERE.parent / 'reports/raw/k1-fast-20261001-224957')
    parser.add_argument('--routing-evidence', type=Path, default=HERE.parent / 'reports/raw/k1-gemm-routing-20261003-005740')
    parser.add_argument('--collect-only', action='store_true')
    args = parser.parse_args()
    if args.collect_only:
        collect(args.run_dir.resolve())
    else:
        start(args)
