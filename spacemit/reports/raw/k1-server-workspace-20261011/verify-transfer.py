#!/usr/bin/env python3
"""核验已传输文件、符号链接与权限。"""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
here = Path(__file__).resolve().parent
manifest = json.loads((here/'transfer-manifest.json').read_text())
errors = []
for name, expected in manifest['files'].items():
    path = root/name
    if not path.is_file() or path.is_symlink():
        errors.append([name, 'file type differs'])
        continue
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected['sha256']:
        errors.append([name, 'hash differs'])
    if path.stat().st_mode & 0o7777 != expected['mode']:
        errors.append([name, 'mode differs'])
for name, target in manifest['symlinks'].items():
    path = root/name
    if not path.is_symlink() or str(path.readlink()) != target:
        errors.append([name, 'link differs'])
result = {'status': 'failed' if errors else 'passed', 'files': len(manifest['files']),
          'symlinks': len(manifest['symlinks']), 'errors': errors,
          'manifest_sha256': hashlib.sha256((here/'transfer-manifest.json').read_bytes()).hexdigest()}
(here/'transfer-review.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
if errors:
    raise SystemExit(1)
