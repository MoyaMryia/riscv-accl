#!/bin/bash
set -uo pipefail
while [ -d /proc/153564 ] && ! grep -q '^State:.*Z' /proc/153564/status; do sleep 20; done
ROOT="$HOME/Projects/spacemit-llama-integrated"
MODELS="$HOME/Projects/spacemit-llama/models"
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$ROOT/build/bin"
for size in 2B 4B; do
  pass=0
  for threads in 4 6 8 2 4; do
    pass=$((pass + 1))
    label="${size}-t${threads}-prefill-pass${pass}"
    echo "START $label"
    python3 /tmp/bench-lifecycle.py \
      --server "$ROOT/build/bin/llama-server" \
      --model "$MODELS/Qwen3.5-${size}-MTP-Q4_0-embQ4_0-dv64k.gguf" \
      --label "$label" --mode plain --contexts 128 2048 \
      --n-predict 1 --ignore-eos --repeats 2 --ctx-size 4096 \
      --threads "$threads" \
      --output /tmp/lifecycle-threads.jsonl \
      --log "/tmp/lifecycle-${label}.log" || echo "FAILED $label"
  done
done
