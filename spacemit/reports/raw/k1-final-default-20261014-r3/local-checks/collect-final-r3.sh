#!/usr/bin/env bash
set -euo pipefail
cd /home/moyamryia/Projects/riscv-accl
[[ -n ${TMUX:-} ]]
rc_board=lab/final-default-20261013/board
[[ ! -e "$rc_board/final-validation-r3" && ! -e "$rc_board/comparison-r3" && ! -e "$rc_board/final-r3" ]]
ssh musepipro 'cd /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1 && test "$(cat final-r3-build-exit-status)" = 0 && test "$(cat final-post-r3-exit-status)" = 0 && tar --exclude=final-validation-r3/relocated-build --exclude="*/__pycache__" -cf - final-validation-r3 comparison-r3 comparison-tools-r3 parser-r3 final-r3/package final-r3/build/bin final-r3/build/build-receipt.json final-r3/build/CMakeCache.txt final-r3/build/compile_commands.json final-r3-build.log final-r3-build-exit-status final-post-r3.log final-post-r3-exit-status build-final-r3.sh final-post-driver-r3.sh final-post-wrapper-r3.sh smoke-parser-r3.py' | tar -xf - -C "$rc_board"
python3 - <<'PY'
import json, sys
from pathlib import Path
sys.path.insert(0, 'spacemit/bench/final-default')
from verify_search import receipts, sha
root = Path('lab/final-default-20261013')
board = root / 'board'
validation = board / 'final-validation-r3'
comparison = board / 'comparison-r3'
assert json.loads((validation / 'summary.json').read_text())['status'] == 'verified-limited'
assert json.loads((comparison / 'summary.json').read_text())['status'] == 'pass'
counts = dict(validation=receipts(validation), comparison=receipts(comparison))
record = json.loads((board / 'final-r3/build/build-receipt.json').read_text())
for name, expected in record['binaries'].items():
    assert sha(board / 'final-r3/build/bin' / name) == expected, name
local = root / 'delivery-r3/package'
remote = board / 'final-r3/package'
local_files = {str(p.relative_to(local)): sha(p) for p in local.rglob('*')
    if p.is_file() and '__pycache__' not in p.parts}
remote_files = {str(p.relative_to(remote)): sha(p) for p in remote.rglob('*') if p.is_file()}
assert local_files == remote_files
assert (board / 'parser-r3/exit-status').read_text().strip() == '0'
result = dict(status='pass', receipts=counts, binaries=len(record['binaries']),
    package_files=len(local_files), patch_sha256=sha(local / 'unified.patch'))
output = root / 'final-r3-collection-verification.json'
assert not output.exists()
output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
PY
