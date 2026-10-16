#!/usr/bin/env bash
set -euo pipefail
cd /home/moyamryia/Projects/riscv-accl
[[ -n ${TMUX:-} ]]
rc_board=lab/final-default-20261013/board
[[ ! -e "$rc_board/final-validation-r2" && ! -e "$rc_board/comparison-tools-r2" ]]
ssh musepipro 'cd /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1 && tar --exclude=final-validation-r2/relocated-build --exclude="*/__pycache__" -cf - final-validation-r2 final-post-r2.log final-post-r2-exit-status final-r2-build.log final-r2-build-exit-status comparison-tools-r2 parser-r2 final-r2/build/build-receipt.json final-r2/build/CMakeCache.txt final-r2/build/compile_commands.json' | tar -xf - -C "$rc_board"
python3 - <<'PY'
import json, sys
from pathlib import Path
sys.path.insert(0, 'spacemit/bench/final-default')
from verify_search import receipts, sha
root = Path('lab/final-default-20261013')
board = root / 'board'
validation = board / 'final-validation-r2'
count = receipts(validation)
summary = json.loads((validation / 'summary.json').read_text())
assert summary['status'] == 'failed'
assert summary['stages']['native']['status'] == 'pass'
assert summary['stages']['state']['records'] == 64
assert "'slots': '4'" in summary['error']
assert (board / 'parser-r2/exit-status').read_text().strip() == '0'
identity = json.loads((validation / 'identity.json').read_text())
assert sha(board / 'comparison-tools-r2/validate_delivery.py') == identity['tool_sha256']
assert sha(board / 'comparison-tools-r2/effective.py') == identity['effective_tool_sha256']
assert sha(root / 'delivery-r2/package/unified.patch') == identity['source']['patch_sha256']
result = dict(status='failure-evidence-verified', files=count, native='pass', state_records=64,
    failed_stage='effective slot count', expected_slots=1, actual_slots=4,
    source_patch_sha256=identity['source']['patch_sha256'])
output = root / 'r2-failure-verification.json'
assert not output.exists()
output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
PY
