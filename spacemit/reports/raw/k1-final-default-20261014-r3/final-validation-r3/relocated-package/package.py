#!/usr/bin/env python3
"""核验统一源码，并从固定厂商源码生成独立目录。"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def manifest():
    return json.loads((HERE/'manifest.json').read_text())


def expected(clean=False):
    m = manifest()
    if sha(HERE/'vendor-source.json') != m['vendor_manifest_sha256']:
        raise ValueError('vendor receipt differs')
    if sha(HERE/'unified.patch') != m['patch_sha256']:
        raise ValueError('unified patch differs')
    pins = json.loads((HERE/'vendor-source.json').read_text())['files_sha256']
    if not clean:
        pins.update(m['files_sha256'])
    return pins


def verify(root, clean=False):
    pins = expected(clean)
    for name, value in pins.items():
        path = root/name
        if not path.is_file() or path.is_symlink() or sha(path) != value:
            raise ValueError('source differs: '+name)
    extras = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts} - set(pins)
    if extras:
        raise ValueError('extra source files: '+str(sorted(extras)[:8]))
    return {'files': len(pins), 'source_commit': manifest()['source_commit'], 'patch_sha256': manifest()['patch_sha256']}


def prepare(source, output):
    verify(source, True)
    if output.exists():
        raise ValueError('output exists')
    output.mkdir(parents=True)
    for name in expected(True):
        dest = output/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source/name, dest)
    subprocess.run(['git', 'apply', '--check', str(HERE/'unified.patch')], cwd=output, check=True)
    subprocess.run(['git', 'apply', str(HERE/'unified.patch')], cwd=output, check=True)
    return verify(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    p = sub.add_parser('prepare')
    p.add_argument('vendor_source', type=Path)
    p.add_argument('output', type=Path)
    p = sub.add_parser('verify')
    p.add_argument('source', type=Path)
    args = parser.parse_args()
    result = prepare(args.vendor_source.resolve(), args.output.resolve()) if args.action == 'prepare' else verify(args.source.resolve())
    print(json.dumps(result, indent=2))
