#!/usr/bin/env bash
set -euo pipefail
cd "$HOME/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1"
[[ $(cat search-r2-exit-status) == 0 ]]
python3 - <<'PY'
import hashlib,json
from pathlib import Path
original=Path('search-r2/selected-default.json')
selected=json.loads(original.read_text())
current=json.loads(Path('final-r2/package/default-policy.json').read_text())
assert current['selection_policy_sha256']==hashlib.sha256(original.read_bytes()).hexdigest()
assert all(current[n]==v for n,v in selected.items() if n!='version')
assert current['version']=='k1-final-20261013-r2'
PY
bash final-r2/package/build.sh final-r2/source final-r2/build
python3 smoke-parser.py
