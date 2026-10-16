#!/usr/bin/env bash
set -euo pipefail
cd /home/moyamryia/Projects/riscv-accl
rc_board=lab/final-default-20261013/board
[[ ! -e "$rc_board/final-validation" && ! -e "$rc_board/comparison-tools" ]]
ssh musepipro 'cd /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1 && tar --exclude=final-validation/relocated-build --exclude="*/__pycache__" -cf - final-validation final-post.log final-post-exit-status final-build.log final-build-exit-status comparison-tools final/build/build-receipt.json final/build/CMakeCache.txt final/build/compile_commands.json' | tar -xf - -C "$rc_board"
python3 - <<'PY'
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,'spacemit/bench/final-default')
from verify_search import receipts
root=Path('lab/final-default-20261013')
board=root/'board'
count=receipts(board/'final-validation')
summary=json.loads((board/'final-validation/summary.json').read_text())
assert summary['status']=='failed'
assert summary['stages']['native']['status']=='pass'
assert summary['stages']['state']['records']==64
log=(board/'final-validation/relocated-2B.server.log').read_text()
assert 'GGML_ASSERT(params.n_gpu_layers < 0) failed' in log
identity=json.loads((board/'final-validation/identity.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(board/'comparison-tools/validate_delivery.py')==identity['tool_sha256']
assert sha(board/'comparison-tools/effective.py')==identity['effective_tool_sha256']
assert sha(root/'delivery/package/unified.patch')==identity['source']['patch_sha256']
result=dict(status='failure-evidence-verified',files=count,native='pass',state_records=64,
    failed_stage='argument parser before model load',source_patch_sha256=identity['source']['patch_sha256'])
(root/'r1-failure-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
PY
