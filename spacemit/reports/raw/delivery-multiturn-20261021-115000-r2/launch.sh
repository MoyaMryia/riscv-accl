#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
exec >run.log 2>&1
trap 'rc=$?; printf "%s\n" "$rc" > exit-status' EXIT
case "both" in
    both) models=(2B 4B) ;;
    *) models=("both") ;;
esac
python3 - "$PWD" <<'PY'
import json
import sys
from pathlib import Path

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
    'turn_timeout_s': 900,
}
with (Path(sys.argv[1]) / 'runtime.json').open('x') as output:
    output.write(json.dumps(runtime, indent=2) + '\n')
PY
python3 -u multi_turn_batch.py --job "$PWD" --runtime "$PWD/runtime.json" --models "${models[@]}"
