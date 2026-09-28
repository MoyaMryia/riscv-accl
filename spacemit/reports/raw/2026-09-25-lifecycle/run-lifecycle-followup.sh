#!/bin/bash
set -uo pipefail
while [ -d /proc/147808 ] && ! grep -q '^State:.*Z' /proc/147808/status; do sleep 20; done
ROOT="$HOME/Projects/spacemit-llama-integrated"
MODELS="$HOME/Projects/spacemit-llama/models"
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$ROOT/build/bin"
run() {
  echo "START $*"
  python3 /tmp/bench-lifecycle.py "$@" --server "$ROOT/build/bin/llama-server" --output /tmp/lifecycle-followup.jsonl --log "/tmp/lifecycle-${label}.log" || echo "FAILED $label"
}
for mode in plain mtp; do
  for conc in 1 2 4 8; do
    label="4B-${mode}-c${conc}"
    run --model "$MODELS/Qwen3.5-4B-MTP-Q4_0-embQ4_0-dv64k.gguf" --label "$label" --mode "$mode" --contexts 128 --n-predict 128 --ctx-size 16384 --parallel 8 --concurrency "$conc"
  done
done
for size in 2B 4B; do
  for mode in plain mtp; do
    label="${size}-${mode}-long"
    run --model "$MODELS/Qwen3.5-${size}-MTP-Q4_0-embQ4_0-dv64k.gguf" --label "$label" --mode "$mode" --contexts 128 --n-predict 2048 --ctx-size 4096 --ignore-eos
  done
done
for size in 2B 4B; do
  for cache in q8_0 q4_0; do
    label="${size}-${cache}-kv"
    run --model "$MODELS/Qwen3.5-${size}-MTP-Q4_0-embQ4_0-dv64k.gguf" --label "$label" --mode plain --contexts 128 2048 --n-predict 32 --ctx-size 16384 --cache-type-k "$cache" --cache-type-v "$cache"
  done
done
for size in 2B 4B; do
  for ub in 32 48; do
    label="${size}-ub${ub}-prefill"
    run --model "$MODELS/Qwen3.5-${size}-MTP-Q4_0-embQ4_0-dv64k.gguf" --label "$label" --mode plain --contexts 128 2048 --n-predict 1 --ctx-size 4096 --batch-size 128 --ubatch-size "$ub" --repeats 2
  done
done
