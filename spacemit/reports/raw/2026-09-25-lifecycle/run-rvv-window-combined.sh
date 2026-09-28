#!/bin/bash
set -euo pipefail
while [ -d /proc/244243 ] && ! grep -q '^State:.*Z' /proc/244243/status; do sleep 20; done
ROOT="$HOME/Projects/spacemit-llama-integrated"
MODELS="$HOME/Projects/spacemit-llama/models"
PATCH=/tmp/windowed-mtp-package-check.patch
OUTPUT=/tmp/lifecycle-rvv-window-combined.jsonl
if [ -e "$OUTPUT" ]; then echo "existing $OUTPUT" >&2; exit 1; fi
cd "$ROOT"
git apply --check "$PATCH"
git apply "$PATCH"
installed=0
cleanup() {
  if [ "$installed" -eq 0 ]; then
    git apply -R "$PATCH"
    cmake --build build --target llama-server -j 4
  fi
}
trap cleanup EXIT
cmake --build build --target llama-server -j 4
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$ROOT/build/bin"
export SPINE_FA_WIDE_TILE=1
for size in 2B 4B; do
  for arm in full window; do
    if [ "$arm" = window ]; then export SPINE_MTP_WINDOW=2048; else unset SPINE_MTP_WINDOW; fi
    label="${size}-rvv-mtp-${arm}-combined"
    echo "START $label"
    log="/tmp/lifecycle-${label}.log"
    python3 /tmp/bench-lifecycle-telemetry.py --server "$ROOT/build/bin/llama-server" \
      --model "$MODELS/Qwen3.5-${size}-MTP-Q4_0-embQ4_0-dv64k.gguf" \
      --label "$label" --mode mtp --contexts 128 12288 --n-predict 128 \
      --ctx-size 16384 --timeout 14400 --output "$OUTPUT" --log "$log"
    grep -q 'SPINE_FA_WIDE_TILE: RVV tiled attention enabled for 256-dim heads' "$log"
    if [ "$arm" = window ]; then grep -q 'draft MTP window = 2048' "$log"; fi
  done
done
python3 /tmp/audit-lifecycle.py "$OUTPUT" \
  --require-identical --require-token-ids --min-runs-per-group 2
installed=1
