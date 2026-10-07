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
import tarfile
import time
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
FILES = ('profile-k1-prefill.py', 'run-k1-prefill-profile-board.sh', 'bench-lifecycle.py', 'k1-fast-test.py')
spec = importlib.util.spec_from_file_location('launch', HERE / 'start-k1-fast-test.py')
launch = importlib.util.module_from_spec(spec); spec.loader.exec_module(launch)


def unpack_artifacts(archive, root, receipt):
    expected = receipt['files_sha256']
    with tarfile.open(archive, 'r:gz') as bundle:
        members = bundle.getmembers()
        names = [m.name for m in members]
        if len(set(names)) != len(names) or set(names) != set(expected):
            raise ValueError('archive file list differs from receipt')
        if any(not m.isfile() or Path(m.name).name != m.name or m.size > 512 * 1024 * 1024 for m in members):
            raise ValueError('unsafe artifact archive member')
        if sum(m.size for m in members) > 1024 * 1024 * 1024:
            raise ValueError('artifact archive too large')
        for member in members:
            temporary = root / (member.name + '.download')
            h = hashlib.sha256()
            with bundle.extractfile(member) as source, temporary.open('wb') as output:
                for chunk in iter(lambda: source.read(4 * 1024 * 1024), b''):
                    output.write(chunk); h.update(chunk)
            if h.hexdigest() != expected[member.name]:
                temporary.unlink(); raise ValueError('artifact checksum mismatch')
            temporary.replace(root / member.name)


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
    # Compress repeated stack text before transferring it over the board link.
    code = ('import hashlib,json,sys,tarfile; from pathlib import Path; '
            'p=Path(sys.argv[1]); files=[f for f in p.iterdir() if f.is_file() and '
            '(f.suffix in (".json", ".jsonl", ".log", ".md", ".txt", ".err", ".data", ".cpp", ".patch") '
            'or f.name in ("phase", "exit-status"))]; '
            'out=p/"profile-artifacts.tar.gz"; temp=p/"profile-artifacts.tar.gz.tmp"; '
            't=tarfile.open(temp,"w:gz",compresslevel=1); '
            '[t.add(f,arcname=f.name,recursive=False) for f in files]; t.close(); temp.replace(out); '
            'print(json.dumps({"archive_sha256":hashlib.sha256(out.read_bytes()).hexdigest(), '
            '"archive_bytes":out.stat().st_size,"files_sha256":'
            '{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in files}}))')
    receipt = json.loads(launch.remote(board, ['python3', '-c', code, target]))
    archive = root / 'profile-artifacts.tar.gz'
    temporary = root / 'profile-artifacts.tar.gz.download'
    subprocess.run(['scp', f'{board}:{target}/{archive.name}', str(temporary)], check=True, timeout=900)
    if hashlib.sha256(temporary.read_bytes()).hexdigest() != receipt['archive_sha256']:
        raise ValueError('archive checksum mismatch')
    temporary.replace(archive)
    unpack_artifacts(archive, root, receipt)
    (root / 'collection-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    (root / 'exit-status').write_text(status + '\n')
    print(f'Profile exit {status}; results {root}', flush=True)


def start(root, evidence, files=FILES, board_script='run-k1-prefill-profile-board.sh', session_prefix='k1_profile_'):
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
    subprocess.run(['scp', *[str(HERE / n) for n in files], str(root / 'expected-provenance.json'),
                    f'{board}:{target}/'], check=True, timeout=90)
    run = {'board': board, 'remote_root': target, 'evidence': str(evidence),
           'board_session': session_prefix + root.name,
           'code_sha256': {n: hashlib.sha256((HERE / n).read_bytes()).hexdigest() for n in files}}
    (root / 'run.json').write_text(json.dumps(run, indent=2) + '\n')
    launch.remote(board, ['tmux', 'new-session', '-d', '-s', run['board_session'],
                         shlex.join(['bash', target + '/' + board_script, target])])
    session = session_prefix + 'collect_' + root.name
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
