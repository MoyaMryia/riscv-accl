#!/usr/bin/env bash
set -euo pipefail
cd /home/moyamryia/Projects/riscv-accl
python3 - <<'PY'
import hashlib,json
from pathlib import Path
root=Path('lab/final-default-20261013')
original=root/'delivery/source'
current=root/'delivery-r2/source'
def pins(folder):
    return {str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}
before=pins(original);after=pins(current)
assert set(before)==set(after)
changed=sorted(n for n in before if before[n]!=after[n])
assert changed==['common/arg.cpp']
(root/'r2-change-receipt.json').write_text(json.dumps(dict(status='pass',changed_files=changed,
    prior_sha256=before[changed[0]],current_sha256=after[changed[0]],source_files=len(after)),indent=2)+'\n')
print('PASS: only the argument parser changes from r1 to r2')
PY
bash -n lab/final-default-20261013/build-final-r2.sh lab/final-default-20261013/final-post-driver-r2.sh \
 lab/final-default-20261013/final-post-wrapper-r2.sh lab/final-default-20261013/deploy-final-r2.sh
python3 -m py_compile lab/final-default-20261013/smoke-parser.py
