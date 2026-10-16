#!/usr/bin/env bash
set -euo pipefail
cd "$HOME/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1"
[[ $(cat baseline-load-build-exit-status) == 0 ]]
python3 record_baseline.py --root .
python3 - <<'PY'
import hashlib,json
from pathlib import Path
root=Path('native-check')
assert json.loads((root/'summary.json').read_text())['status']=='pass'
for name,value in json.loads((root/'receipts.json').read_text()).items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==value
PY
python3 tools-r2/experiment.py --stage search --output search-r2 \
 --baseline baseline-load-build \
 --candidate "$HOME/Projects/riscv-accl-bench-2026-09-27/k1-unified-20261013-rc1/build" \
 --models "$HOME/Projects/spacemit-llama/models" \
 --spert "$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2" \
 --tcm "$HOME/Projects/llm-bench/.toolchain/spine-tcm"
