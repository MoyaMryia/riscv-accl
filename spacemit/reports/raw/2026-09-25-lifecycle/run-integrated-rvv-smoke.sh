#!/bin/bash
set -euo pipefail
ROOT="$HOME/Projects/spacemit-llama-integrated"
MODELS="$HOME/Projects/spacemit-llama/models"
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$ROOT/build/bin"
export SPINE_FA_WIDE_TILE=1
for size in 2B 4B; do
  label="${size}-rvv32-integrated-smoke"
  python3 /tmp/bench-lifecycle.py --server "$ROOT/build/bin/llama-server" \
    --model "$MODELS/Qwen3.5-${size}-MTP-Q4_0-embQ4_0-dv64k.gguf" \
    --label "$label" --mode plain --contexts 128 --n-predict 32 \
    --ctx-size 4096 --output /tmp/lifecycle-integrated-rvv-smoke.jsonl \
    --log "/tmp/lifecycle-${label}.log"
  grep -q 'SPINE_FA_WIDE_TILE: RVV tiled attention enabled for 256-dim heads' \
    "/tmp/lifecycle-${label}.log"
done
python3 /tmp/audit-lifecycle.py /tmp/lifecycle-rvv32.jsonl \
  /tmp/lifecycle-integrated-rvv-smoke.jsonl \
  --require-identical --require-token-ids --min-runs-per-group 3
