#!/bin/bash
set -uo pipefail
while [ -d /proc/185376 ] && ! grep -q '^State:.*Z' /proc/185376/status; do sleep 20; done
ROOT="$HOME/Projects/spacemit-llama-integrated"
MODEL="$HOME/Projects/spacemit-llama/models/Qwen3.5-4B-MTP-Q4_0-embQ4_0-dv64k.gguf"
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$ROOT/build/bin"
pass=0
for cache in f16 q4_0 q4_0 f16; do
  pass=$((pass + 1))
  label="4B-kv-${cache}-pass${pass}"
  echo "START $label"
  python3 /tmp/bench-lifecycle.py \
    --server "$ROOT/build/bin/llama-server" --model "$MODEL" \
    --label "$label" --mode plain --contexts 128 2048 --n-predict 32 \
    --ctx-size 16384 --cache-type-k "$cache" --cache-type-v "$cache" \
    --output /tmp/lifecycle-4b-kv-abba.jsonl \
    --log "/tmp/lifecycle-${label}.log" || echo "FAILED $label"
done
