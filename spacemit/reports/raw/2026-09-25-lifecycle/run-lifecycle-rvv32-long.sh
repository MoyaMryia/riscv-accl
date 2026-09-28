#!/bin/bash
set -uo pipefail
while [ -d /proc/204226 ] && ! grep -q '^State:.*Z' /proc/204226/status; do sleep 20; done
ROOT="$HOME/Projects/spacemit-llama-rvv32"
MODELS="$HOME/Projects/spacemit-llama/models"
if [ ! -x "$ROOT/build/bin/llama-server" ]; then
  echo "RVV32 server build unavailable; skipping 8k extension" >&2
  exit 1
fi
mapfile -t sizes < <(python3 /tmp/select-rvv32-long.py /tmp/lifecycle-rvv32.jsonl)
if [ "${#sizes[@]}" -eq 0 ]; then
  echo "No RVV32 model passed the short-context exact-output and activation gates" >&2
  exit 0
fi
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$ROOT/build/bin"
for size in "${sizes[@]}"; do
  pass=0
  for enabled in 0 1 1 0; do
    pass=$((pass + 1))
    export SPINE_FA_WIDE_TILE="$enabled"
    label="8k-${size}-rvv32-${enabled}-pass${pass}"
    echo "START $label"
    python3 /tmp/bench-lifecycle.py --server "$ROOT/build/bin/llama-server" \
      --model "$MODELS/Qwen3.5-${size}-MTP-Q4_0-embQ4_0-dv64k.gguf" \
      --label "$label" --mode plain --contexts 8192 --n-predict 32 \
      --ctx-size 16384 --output /tmp/lifecycle-rvv32-long.jsonl \
      --log "/tmp/lifecycle-${label}.log" || exit 1
  done
done
python3 /tmp/audit-lifecycle.py /tmp/lifecycle-rvv32-long.jsonl \
  --require-identical --require-token-ids --min-runs-per-group 4
