#!/usr/bin/env python3
"""Stage a fast K1 test in board tmux and collect it in workstation tmux."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import time
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
SOURCES = ('k1-fast-test.py', 'run-k1-fast-test-board.sh',
           'test-k1-attention-layout.cpp', 'bench-lifecycle.py')
PATHS = ('ggml/src/ggml-cpu/ggml-cpu.c', 'ggml/src/ggml-cpu/spacemit/ime.cpp',
         'ggml/src/ggml-cpu/spacemit/rvv_kernels.cpp')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def remote(board, argv):
    return subprocess.check_output(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
                                    '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=2',
                                    board, shlex.join(list(map(str, argv)))], text=True, timeout=60).strip()


def collect(root):
    manifest = json.loads((root / 'run.json').read_text())
    board, target = manifest['board'], manifest['remote_root']
    deadline = time.monotonic() + 86400
    while time.monotonic() < deadline:
        try:
            status = remote(board, ['cat', target + '/exit-status'])
            break
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            time.sleep(60)
    else:
        raise TimeoutError('collector deadline exceeded')
    listing = remote(board, ['python3', '-c',
                     'from pathlib import Path; import json,sys; '
                     'print(json.dumps([p.name for p in Path(sys.argv[1]).iterdir() '
                     'if p.is_file() and (p.suffix in (".log", ".json", ".jsonl", ".md") '
                     'or p.name in ("phase", "exit-status"))]))', target])
    for name in json.loads(listing):
        if Path(name).name != name:
            raise ValueError('invalid artifact name')
        subprocess.run(['scp', f'{board}:{target}/{name}', str(root)], check=True, timeout=90)
    (root / 'exit-status').write_text(status + '\n')
    print(f'Fast test exit {status}; results {root}', flush=True)


def start(args):
    root = args.run_dir.resolve()
    if args.resume:
        manifest = json.loads((root / 'run.json').read_text())
        if manifest['code_sha256'] != {n: sha(HERE / n) for n in SOURCES}:
            raise ValueError('code changed; start a new run instead of resuming old stages')
        board, target, build_run = manifest['board'], manifest['remote_root'], manifest['build_run']
        if manifest['mode'] != args.mode:
            summary = json.loads((root / 'summary.json').read_text())
            if not (manifest['mode'] == 'screen' and args.mode == 'confirm-long'
                    and summary['status'] == 'screen eligible'):
                raise ValueError('only an eligible screen can advance to confirm-long')
        active = subprocess.run(['ssh', board, shlex.join(['tmux', 'has-session', '-t', manifest['board_session']])],
                                capture_output=True, timeout=45)
        if active.returncode == 0:
            raise ValueError('board job still active; use --collect-only to recover collection')
        if active.returncode == 255:
            raise RuntimeError('could not check board job state')
        remote(board, ['rm', '-f', target + '/exit-status'])
        manifest['mode'] = args.mode
        (root / 'run.json').write_text(json.dumps(manifest, indent=2) + '\n')
        (root / 'exit-status').unlink(missing_ok=True)
    else:
        root.mkdir(parents=True, exist_ok=False)
        reuse = args.reuse_run.resolve()
        old = json.loads((reuse / 'run.json').read_text())
        board = args.board
        if old['board'] != board:
            raise ValueError('reuse board differs from requested board')
        patch = HERE.parent / 'experiments/2026-09-30-k1-attention-layout.patch'
        if sha(patch) != old['patch_sha256']:
            raise ValueError('reuse requires the exact same layout patch')
        audit = json.loads((reuse / 'source-manifest.json').read_text())
        expected = {}
        with tempfile.TemporaryDirectory(prefix='k1-fast-source-') as temporary:
            tmp = Path(temporary)
            for name in PATHS:
                src = reuse / 'baseline' / Path(name).name
                if sha(src) != audit['source_sha256'][name]:
                    raise ValueError('local baseline hash mismatch')
                dst = tmp / name
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(src.read_bytes())
            subprocess.run(['git', 'apply', '--check', str(patch)], cwd=tmp, check=True)
            subprocess.run(['git', 'apply', str(patch)], cwd=tmp, check=True)
            expected = {name: sha(tmp / name) for name in PATHS}
        (root / 'expected-source.json').write_text(json.dumps(expected, indent=2) + '\n')
        home = remote(board, ['python3', '-c', 'from pathlib import Path; print(Path.home())'])
        target = home + '/Projects/riscv-accl-bench-2026-09-27/' + root.name
        build_run = old['remote_root']
        remote(board, ['mkdir', target])
        subprocess.run(['scp', *[str(HERE / n) for n in SOURCES], str(root / 'expected-source.json'),
                        f'{board}:{target}/'], check=True, timeout=90)
        manifest = {'board': board, 'remote_root': target, 'build_run': build_run, 'mode': args.mode,
                    'board_session': 'k1_fast_' + root.name,
                    'code_sha256': {n: sha(HERE / n) for n in SOURCES},
                    'reuse_source': str(reuse), 'planned_cases_per_layout': 241}
        (root / 'run.json').write_text(json.dumps(manifest, indent=2) + '\n')
    invocation = shlex.join(['bash', target + '/run-k1-fast-test-board.sh', target, build_run, args.mode])
    remote(board, ['tmux', 'new-session', '-d', '-s', manifest['board_session'], invocation])
    session = 'k1_fast_collect_' + root.name
    invocation = shlex.join([sys.executable, str(Path(__file__).resolve()), '--collect-only', '--run-dir', str(root)])
    invocation += ' >> ' + shlex.quote(str(root / 'collector.log')) + ' 2>&1'
    subprocess.run(['tmux', 'new-session', '-d', '-s', session, invocation], check=True)
    print(f'Board tmux {manifest["board_session"]}; local collector {session}; results {root}', flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--board', default='musepipro-wg')
    p.add_argument('--reuse-run', type=Path, default=HERE.parent / 'reports/raw/k1-layout-20260930-153134')
    p.add_argument('--run-dir', type=Path, default=HERE.parent / 'reports/raw' /
                   ('k1-fast-' + datetime.datetime.now(ZoneInfo('Asia/Singapore')).strftime('%Y%m%d-%H%M%S')))
    p.add_argument('--mode', choices=('smoke', 'screen', 'confirm-long'), default='screen')
    p.add_argument('--collect-only', action='store_true')
    p.add_argument('--resume', action='store_true')
    args = p.parse_args()
    if args.collect_only:
        collect(args.run_dir.resolve())
    else:
        start(args)


if __name__ == '__main__':
    main()
