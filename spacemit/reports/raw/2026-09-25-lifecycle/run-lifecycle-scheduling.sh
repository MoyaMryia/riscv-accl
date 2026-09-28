#!/bin/bash
set -uo pipefail
while [ -d /proc/147889 ] && ! grep -q '^State:.*Z' /proc/147889/status; do sleep 20; done
ROOT="$HOME/Projects/spacemit-llama-integrated"
MODELS="$HOME/Projects/spacemit-llama/models"
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$ROOT/build/bin"
run() {
  echo "START $*"
  python3 /tmp/bench-lifecycle.py "$@" --server "$ROOT/build/bin/llama-server" --output /tmp/lifecycle-scheduling.jsonl --log "/tmp/lifecycle-${label}.log" || echo "FAILED $label"
}
for size in 2B 4B; do
  label="${size}-prefix-reuse"
  run --model "$MODELS/Qwen3.5-${size}-MTP-Q4_0-embQ4_0-dv64k.gguf" --label "$label" --mode plain --contexts 2048 --n-predict 32 --ctx-size 4096 --repeats 2 --cache-prompt
  for mode in plain mtp; do
    label="${size}-${mode}-unified-c8"
    run --model "$MODELS/Qwen3.5-${size}-MTP-Q4_0-embQ4_0-dv64k.gguf" --label "$label" --mode "$mode" --contexts 128 --n-predict 128 --ctx-size 16384 --parallel 8 --concurrency 8 --kv-unified
  done
done
