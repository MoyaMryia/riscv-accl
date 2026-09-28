#!/bin/bash
set -euo pipefail
while [ -d /proc/243048 ] && ! grep -q '^State:.*Z' /proc/243048/status; do sleep 20; done
ROOT="$HOME/Projects/spacemit-llama-integrated"
MODELS="$HOME/Projects/spacemit-llama/models"
OUTPUT=/tmp/lifecycle-integrated-rvv-12k.jsonl
if [ -e "$OUTPUT" ]; then echo "existing $OUTPUT" >&2; exit 1; fi
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$ROOT/build/bin"
for size in 2B 4B; do
  for enabled in 0 1; do
    export SPINE_FA_WIDE_TILE="$enabled"
    label="${size}-rvv32-integrated-12k-${enabled}"
    echo "START $label"
    python3 /tmp/bench-lifecycle.py --server "$ROOT/build/bin/llama-server" \
      --model "$MODELS/Qwen3.5-${size}-MTP-Q4_0-embQ4_0-dv64k.gguf" \
      --label "$label" --mode plain --contexts 12288 --n-predict 32 \
      --ctx-size 16384 --timeout 14400 --output "$OUTPUT" \
      --log "/tmp/lifecycle-${label}.log"
    if [ "$enabled" -eq 1 ]; then
      grep -q 'SPINE_FA_WIDE_TILE: RVV tiled attention enabled for 256-dim heads' \
        "/tmp/lifecycle-${label}.log"
    fi
  done
done
python3 /tmp/audit-lifecycle.py "$OUTPUT" \
  --require-identical --require-token-ids --min-runs-per-group 2
