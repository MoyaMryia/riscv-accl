#!/bin/bash
set -uo pipefail
while [ -d /proc/152917 ] && ! grep -q '^State:.*Z' /proc/152917/status; do sleep 20; done
ROOT="$HOME/Projects/spacemit-llama-wide-fa"
MODELS="$HOME/Projects/spacemit-llama/models"
if [ ! -x "$ROOT/build/bin/llama-server" ]; then
  echo "wide-RVV server build unavailable; skipping 8k extension" >&2
  exit 1
fi
mapfile -t sizes < <(python3 /tmp/select-wide-fa-long.py /tmp/lifecycle-wide-fa.jsonl)
if [ "${#sizes[@]}" -eq 0 ]; then
  echo "No model passed the short-context exact-output gate" >&2
  exit 0
fi
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$ROOT/build/bin"
for size in "${sizes[@]}"; do
  pass=0
  for enabled in 0 1 1 0; do
    pass=$((pass + 1))
    export SPINE_FA_WIDE_TILE="$enabled"
    label="8k-${size}-widefa${enabled}-pass${pass}"
    echo "START $label"
    python3 /tmp/bench-lifecycle.py \
      --server "$ROOT/build/bin/llama-server" \
      --model "$MODELS/Qwen3.5-${size}-MTP-Q4_0-embQ4_0-dv64k.gguf" \
      --label "$label" --mode plain --contexts 8192 --n-predict 32 \
      --ctx-size 16384 --output /tmp/lifecycle-wide-fa-long.jsonl \
      --log "/tmp/lifecycle-${label}.log" || echo "FAILED $label"
  done
done
