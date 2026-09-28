#!/bin/bash
set -uo pipefail
while [ -d /proc/149650 ] && ! grep -q '^State:.*Z' /proc/149650/status; do sleep 20; done
ROOT="$HOME/Projects/spacemit-llama-integrated"
MODELS="$HOME/Projects/spacemit-llama/models"
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$ROOT/build/bin"
pass=0
for mode in plain mtp mtp plain; do
  pass=$((pass + 1))
  for conc in 1 4 8; do
    label="4B-${mode}-code-c${conc}-pass${pass}"
    echo "START $label"
    python3 /tmp/bench-lifecycle.py \
      --server "$ROOT/build/bin/llama-server" \
      --model "$MODELS/Qwen3.5-4B-MTP-Q4_0-embQ4_0-dv64k.gguf" \
      --label "$label" --mode "$mode" --contexts 128 --n-predict 128 \
      --prompt-file /tmp/lifecycle-code-prompt.cpp --ignore-eos \
      --ctx-size 16384 --parallel 8 --concurrency "$conc" \
      --output /tmp/lifecycle-code-concurrency.jsonl \
      --log "/tmp/lifecycle-${label}.log" || echo "FAILED $label"
  done
done
