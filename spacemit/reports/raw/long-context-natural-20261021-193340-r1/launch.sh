#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
exec >run.log 2>&1
trap 'rc=$?; printf "%s\n" "$rc" > exit-status' EXIT
export PYTHONDONTWRITEBYTECODE=1
python3 - "$PWD" <<'RUNTIME'
import json
from pathlib import Path
import sys
home = Path.home()
bench = home / 'Projects/riscv-accl-bench-2026-09-27'
base = bench / 'k1-final-default-20261013-r1/final-r3'
runtime = {
    'server': str(base / 'build/bin/llama-server'),
    'models': str(home / 'Projects/spacemit-llama/models'),
    'spert': str(home / 'Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2'),
    'tcm': str(home / 'Projects/llm-bench/.toolchain/spine-tcm'),
    'manifest': str(base / 'package/manifest.json'),
    'build_receipt': str(base / 'build/build-receipt.json'),
    'lock': str(bench / 'document-quality-suite.lock'),
}
with (Path(sys.argv[1]) / 'runtime.json').open('x') as stream:
    json.dump(runtime, stream, indent=2)
    stream.write('\n')
RUNTIME
python3 -u long_context_batch.py --job "$PWD" --runtime "$PWD/runtime.json" --models 2B 4B
