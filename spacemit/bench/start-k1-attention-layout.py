#!/usr/bin/env python3
"""Queue an isolated K1 layout experiment and collect its results using tmux."""

import argparse
import datetime
import hashlib
import json
import shlex
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def command(argv, **kwargs):
    return subprocess.run(argv, text=True, check=True, **kwargs)


def remote(board, argv):
    return command(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', board,
                    shlex.join(argv)], capture_output=True, timeout=45).stdout.strip()


def collect(root):
    manifest = json.loads((root/'run.json').read_text())
    board, target = manifest['board'], manifest['remote_root']
    deadline = time.monotonic() + 86400
    while time.monotonic() < deadline:
        try:
            status = remote(board, ['cat', target+'/exit-status'])
            break
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            time.sleep(60)
    else:
        raise TimeoutError('collector deadline exceeded')
    names = ['phase', 'driver.log', 'configure.log', 'build.log', 'test-build.log',
             'numeric-status', 'audit.log', 'results.jsonl', 'summary.json', 'summary.md']
    names += [f'numeric-{rows}.log' for rows in (0, 16, 32)]
    names += [f'{model}-layout-{rows}-pass{i}.log' for model in ('2B', '4B')
              for i, rows in enumerate((0, 16, 32, 32, 16, 0), 1)]
    for name in names:
        try:
            command(['scp', f'{board}:{target}/{name}', str(root)],
                    capture_output=True, timeout=60)
        except subprocess.CalledProcessError:
            print(f'Artifact unavailable: {name}', flush=True)
    (root/'exit-status').write_text(status+'\n')
    print(f'Experiment exit {status}; results {root}', flush=True)


def start(args):
    root = args.run_dir.resolve()
    root.mkdir(parents=True, exist_ok=False)
    provenance = HERE.parent/'reports/raw/2026-09-30-code-audit/source-manifest.json'
    audit = json.loads(provenance.read_text())
    home = remote(args.board, ['python3', '-c', 'from pathlib import Path; print(Path.home())'])
    base = home+'/Projects/spacemit-llama-integrated'
    if not remote(args.board, ['git', '-C', base, 'rev-parse', 'HEAD']).startswith(audit['head_short']):
        raise ValueError('board baseline commit differs from the audited source')
    baseline = root/'baseline'
    baseline.mkdir()
    for path in audit['modified_paths']:
        command(['scp', f'{args.board}:{base}/{path}', str(baseline)], capture_output=True, timeout=60)
        copied = baseline/Path(path).name
        if hashlib.sha256(copied.read_bytes()).hexdigest() != audit['source_sha256'][path]:
            raise ValueError(f'board baseline changed: {path}')
    (root/'source-manifest.json').write_text(provenance.read_text())
    target = home+'/Projects/riscv-accl-bench-2026-09-27/'+root.name
    remote(args.board, ['mkdir', '-p', target+'/baseline'])
    command(['scp', *map(str, baseline.iterdir()), f'{args.board}:{target}/baseline/'], timeout=60)
    sources = [HERE/name for name in ('run-k1-attention-layout-board.sh', 'test-k1-attention-layout.cpp',
                                     'bench-lifecycle.py', 'audit-lifecycle.py', 'summarize-k1-attention-layout.py')]
    command(['scp', *map(str, sources), str(root/'source-manifest.json'), f'{args.board}:{target}/'], timeout=60)
    patch = HERE.parent/'experiments/2026-09-30-k1-attention-layout.patch'
    command(['scp', str(patch), f'{args.board}:{target}/layout.patch'], timeout=60)
    board_session = 'k1_layout_'+root.name
    invocation = shlex.join(['bash', target+'/run-k1-attention-layout-board.sh', target])
    (root/'run.json').write_text(json.dumps({'board': args.board, 'remote_root': target,
                                           'board_session': board_session,
                                           'patch_sha256': hashlib.sha256(patch.read_bytes()).hexdigest(),
                                           'planned_layouts': [0, 16, 32], 'numeric_cases_per_layout': 235}, indent=2)+'\n')
    remote(args.board, ['tmux', 'new-session', '-d', '-s', board_session, invocation])
    local_session = 'k1_layout_collect_'+root.name
    local_command = shlex.join([sys.executable, str(Path(__file__).resolve()), '--collect-only',
                                '--run-dir', str(root)])
    local_command += ' > '+shlex.quote(str(root/'collector.log'))+' 2>&1'
    command(['tmux', 'new-session', '-d', '-s', local_session, local_command])
    print(f'Queued board tmux {board_session}; collector {local_session}; results {root}', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', default='musepipro-wg')
    parser.add_argument('--run-dir', type=Path,
                        default=HERE.parent/'reports/raw'/('k1-layout-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')))
    parser.add_argument('--collect-only', action='store_true')
    args = parser.parse_args()
    if args.collect_only:
        collect(args.run_dir.resolve())
    else:
        start(args)


if __name__ == '__main__':
    main()
