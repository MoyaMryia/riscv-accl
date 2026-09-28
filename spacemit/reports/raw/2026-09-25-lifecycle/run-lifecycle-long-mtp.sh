#!/bin/bash
set -uo pipefail
while [ -d /proc/147914 ] && ! grep -q '^State:.*Z' /proc/147914/status; do sleep 20; done
ROOT="$HOME/Projects/spacemit-llama-integrated"
MODELS="$HOME/Projects/spacemit-llama/models"
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$ROOT/build/bin"
run() {
  echo "START $*"
  python3 /tmp/bench-lifecycle.py "$@" --server "$ROOT/build/bin/llama-server" --output /tmp/lifecycle-long-mtp.jsonl --log "/tmp/lifecycle-${label}.log" || echo "FAILED $label"
}
for size in 2B 4B; do
  for ctx in 8192 16384; do
    label="${size}-ctx${ctx}-footprint"
    run --model "$MODELS/Qwen3.5-${size}-MTP-Q4_0-embQ4_0-dv64k.gguf" --label "$label" --mode plain --contexts 128 --n-predict 1 --ctx-size "$ctx"
  done
  label="${size}-mtp-12k"
  run --model "$MODELS/Qwen3.5-${size}-MTP-Q4_0-embQ4_0-dv64k.gguf" --label "$label" --mode mtp --contexts 12288 --n-predict 128 --ctx-size 16384
 done
