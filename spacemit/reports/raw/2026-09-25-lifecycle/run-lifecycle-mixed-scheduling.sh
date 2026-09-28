#!/bin/bash
set -uo pipefail
while [ -d /proc/149571 ] && ! grep -q '^State:.*Z' /proc/149571/status; do sleep 20; done
ROOT="$HOME/Projects/spacemit-llama-integrated"
MODELS="$HOME/Projects/spacemit-llama/models"
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$ROOT/build/bin"
for size in 2B 4B; do
  arm=0
  for variant in partition unified unified partition; do
    arm=$((arm + 1))
    label="${size}-${variant}-mixed-${arm}"
    flags=()
    if [ "$variant" = unified ]; then flags+=(--kv-unified); fi
    echo "START $label"
    python3 /tmp/bench-lifecycle.py --server "$ROOT/build/bin/llama-server" \
      --model "$MODELS/Qwen3.5-${size}-MTP-Q4_0-embQ4_0-dv64k.gguf" \
      --label "$label" --mode plain --contexts 128 \
      --slot-contexts 128 512 1024 2048 --n-predict 128 \
      --parallel 4 --concurrency 4 --ctx-size 16384 \
      --output /tmp/lifecycle-mixed-scheduling.jsonl --log "/tmp/lifecycle-${label}.log" \
      "${flags[@]}" || echo "FAILED $label"
  done
done
