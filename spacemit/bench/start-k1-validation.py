#!/usr/bin/env python3
"""Offload staged validation to board tmux and automatically collect its evidence."""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import sys
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('profile', HERE / 'start-k1-prefill-profile.py')
profile = importlib.util.module_from_spec(spec); spec.loader.exec_module(profile)
FILES = ('k1-validation.py', 'test-k1-recurrent-state.cpp', 'test-k1-perfect-draft.cpp',
         'run-k1-validation-board.sh', 'bench-lifecycle.py', 'k1-fast-test.py',
         'document_quality_suite.py', 'k1-gemm-routing.py', 'make-k1-gemm-routing.py',
         'k1-ime-test.py', 'make-k1-ime-candidate.py')


def collect(root):
    profile.collect(root)
    summary_file = root / 'summary.json'
    if not summary_file.exists(): raise RuntimeError('board did not produce a summary; inspect driver.log')
    summary = json.loads(summary_file.read_text())
    spec = importlib.util.spec_from_file_location('verify', HERE / 'verify-k1-validation.py')
    verifier = importlib.util.module_from_spec(spec); spec.loader.exec_module(verifier)
    verification = verifier.verify(root)
    (root / 'verification.json').write_text(json.dumps(verification, indent=2) + '\n')
    summary['collection'] = 'archive, individual file SHA256 and completed acceptance gates verified'
    (root / 'collected-summary.md').write_text('# Collected K1 validation\n\n'
        + json.dumps(summary, indent=2) + '\n')
    print('Collected stage outcomes: ' + json.dumps({k: v['status'] for k, v in summary['stages'].items()}), flush=True)


def start(root, routing):
    if (routing / 'exit-status').read_text().strip() != '0': raise ValueError('routing evidence not complete')
    prior = json.loads((routing / 'run.json').read_text())
    results = json.loads((routing / 'summary.json').read_text())
    if results.get('qualified_modes') != [1, 2]: raise ValueError('requires qualified separate phase policies')
    root.mkdir(parents=True, exist_ok=False)
    board = prior['board']
    home = profile.launch.remote(board, ['python3', '-c', 'from pathlib import Path; print(Path.home())'])
    target = home + '/Projects/riscv-accl-bench-2026-09-27/' + root.name
    expected = Path(prior['evidence']) / 'provenance.json'
    staged = {n: HERE / n for n in FILES}
    staged.update({'cached-document-chat.py': HERE.parent / 'serve/cached-document-chat.py',
        'code-prompt.txt': HERE.parent / 'reports/raw/2026-09-25-lifecycle/lifecycle-code-prompt.cpp',
        'expected-provenance.json': expected, 'routing-provenance.json': routing / 'provenance.json',
        'routing-run.json': routing / 'run.json'})
    import shutil
    for name, source in staged.items(): shutil.copyfile(source, root / name)
    # Refuse the wrong old reproduction fixture before spending board time.
    if hashlib.sha256((root / 'code-prompt.txt').read_bytes()).hexdigest() != '06ed2b6d42854f42b74a2fb940a5b5bf405c619fa0d40f81cf8ca18b566104f7':
        raise ValueError('original code fixture changed')
    profile.launch.remote(board, ['mkdir', target])
    subprocess.run(['scp', *[str(root / n) for n in staged], f'{board}:{target}/'], check=True, timeout=90)
    run = {'board': board, 'remote_root': target, 'routing_evidence': str(routing),
           'board_session': 'k1_validation_' + root.name,
           'collector_session': 'k1_validation_collect_' + root.name,
           'code_sha256': {n: hashlib.sha256((root / n).read_bytes()).hexdigest() for n in staged}}
    (root / 'run.json').write_text(json.dumps(run, indent=2) + '\n')
    subprocess.run(['scp', str(root / 'run.json'), f'{board}:{target}/'], check=True, timeout=30)
    # Start the collector first: if board dispatch fails, the evidence directory
    # remains reviewable and the collector can still recover exit-status.
    invocation = shlex.join([sys.executable, str(Path(__file__).resolve()), '--collect-only', '--run-dir', str(root)])
    invocation += ' >> ' + shlex.quote(str(root / 'collector.log')) + ' 2>&1'
    subprocess.run(['tmux', 'new-session', '-d', '-s', run['collector_session'], invocation], check=True)
    try:
        profile.launch.remote(board, ['tmux', 'new-session', '-d', '-s', run['board_session'],
            shlex.join(['bash', target + '/run-k1-validation-board.sh', target])])
    except BaseException:
        subprocess.run(['tmux', 'kill-session', '-t', run['collector_session']], check=False)
        raise
    print(json.dumps(run, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, default=HERE.parent / 'reports/raw' /
        ('k1-validation-' + datetime.datetime.now(ZoneInfo('Asia/Singapore')).strftime('%Y%m%d-%H%M%S')))
    parser.add_argument('--routing-evidence', type=Path, default=HERE.parent / 'reports/raw/k1-gemm-routing-20261003-005740')
    parser.add_argument('--collect-only', action='store_true')
    args = parser.parse_args()
    if args.collect_only: collect(args.run_dir.resolve())
    else: start(args.run_dir.resolve(), args.routing_evidence.resolve())
