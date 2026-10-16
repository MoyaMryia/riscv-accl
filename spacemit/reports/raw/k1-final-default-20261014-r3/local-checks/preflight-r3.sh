#!/usr/bin/env bash
set -euo pipefail
cd /home/moyamryia/Projects/riscv-accl
python3 spacemit/bench/final-default/test_delivery.py
bash lab/final-default-20261013/generate-final-r3.sh
python3 - <<'CHECK'
import hashlib,json
from pathlib import Path
root=Path('lab/final-default-20261013')
def pins(folder):
 return {str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}
before=pins(root/'delivery-r2/source');after=pins(root/'delivery-r3/source')
assert set(before)==set(after)
changed=sorted(n for n in before if before[n]!=after[n])
assert changed==['common/arg.cpp']
old=(root/'delivery-r2/source/common/arg.cpp').read_text()
new=(root/'delivery-r3/source/common/arg.cpp').read_text()
assert old.replace('        params.n_parallel = -1;     // auto by default','        params.n_parallel = 1;      // Fixed K1 server slot count.')==new
(root/'r3-change-receipt.json').write_text(json.dumps(dict(status='pass',changed_files=changed,source_files=len(after),prior_sha256=before[changed[0]],current_sha256=after[changed[0]]),indent=2)+'\n')
CHECK
bash -n lab/final-default-20261013/deploy-final-r3.sh lab/final-default-20261013/build-final-r3.sh lab/final-default-20261013/final-post-driver-r3.sh lab/final-default-20261013/final-post-wrapper-r3.sh
python3 -m py_compile lab/final-default-20261013/smoke-parser-r3.py
