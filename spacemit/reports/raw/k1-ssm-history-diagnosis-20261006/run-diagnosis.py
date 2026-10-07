#!/usr/bin/env python3
"""Bounded native graph diagnosis; never loads or restarts model inference."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parent
saved = json.loads((root / 'diagnosis.json').read_text())
original = root.parent / 'k1-ssm-conv-20261006-073927'
for name, expected in saved['libraries_verified'].items():
    assert hashlib.sha256((original / 'lib' / name).read_bytes()).hexdigest() == expected
argv = [str(root / 'test-k1-ssm-conv-fixed.cpp') if arg == str(root / 'test-k1-ssm-conv.cpp')
        else str(root / 'diagnose-ssm-fixed') if arg == str(root / 'diagnose-ssm') else arg
        for arg in saved['compile']]
subprocess.run(argv, check=True, timeout=60)
env = dict(os.environ, **saved['runtime'])
env.pop('SPINE_SSM_DIAG_LEGACY_COPY', None)
records = []

def run(label, args, legacy=False, expected=0):
    case_env = dict(env)
    if legacy:
        case_env['SPINE_SSM_DIAG_LEGACY_COPY'] = '1'
    command = [str(root / 'diagnose-ssm-fixed'), *map(str, args)]
    result = subprocess.run(command, env=case_env, capture_output=True, text=True, timeout=60)
    (root / (label + '.log')).write_text(result.stdout + result.stderr)
    records.append(dict(label=label, argv=command, legacy_copy=legacy, exit_status=result.returncode))
    print(label, result.returncode, (result.stdout + result.stderr).strip(), flush=True)
    assert result.returncode == expected, label

run('legacy-minimal', ['--case', 1, 7, 3, 1, 1, 0], legacy=True, expected=1)
for mode in (0, 1, 2):
    run('fixed-minimal-' + str(mode), ['--case', mode, 7, 3, 1, 1, 0])
    run('fixed-matrix-' + str(mode), [mode, '--dump', root / ('fixed-' + str(mode) + '.bin')])
hashes = {str(mode): hashlib.sha256((root / ('fixed-' + str(mode) + '.bin')).read_bytes()).hexdigest()
          for mode in (0, 1, 2)}
assert len(set(hashes.values())) == 1, hashes
summary = dict(status='passed', compile=argv, runtime=saved['runtime'],
               libraries_verified=saved['libraries_verified'], cases_per_arm=432,
               executions_per_case=2, checks=records, dump_sha256=hashes,
               source_sha256={name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                              for name in ('test-k1-ssm-conv-fixed.cpp', 'spine-k1-ssm-conv.h', 'run-diagnosis.py')})
(root / 'fixed-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print('PASS: three complete graph arms have identical output and history dumps', flush=True)
