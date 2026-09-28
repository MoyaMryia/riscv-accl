#!/bin/bash
set -uo pipefail
while [ -d /proc/205128 ] && ! grep -q '^State:.*Z' /proc/205128/status; do sleep 20; done
ROOT="$HOME/Projects/spacemit-llama-integrated"
MODELS="$HOME/Projects/spacemit-llama/models"
PROMPT=/tmp/lifecycle-code-prompt.cpp
OUTPUT=/tmp/lifecycle-code-long.jsonl
if [ ! -s "$PROMPT" ] || [ -e "$OUTPUT" ]; then
  echo 'Missing fixed C++ prompt or existing output path; refusing to reuse the campaign file' >&2
  exit 1
fi
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$ROOT/build/bin"
for size in 2B 4B; do
  for mode in plain mtp; do
    label="${size}-${mode}-code-long"
    echo "START $label"
    python3 /tmp/bench-lifecycle.py \
      --server "$ROOT/build/bin/llama-server" \
      --model "$MODELS/Qwen3.5-${size}-MTP-Q4_0-embQ4_0-dv64k.gguf" \
      --label "$label" --mode "$mode" --contexts 128 \
      --prompt-file "$PROMPT" --n-predict 4096 --ctx-size 8192 \
      --ignore-eos --repeats 2 --timeout 14400 \
      --output "$OUTPUT" --log "/tmp/lifecycle-${label}.log" || echo "FAILED $label" >&2
  done
done
python3 /tmp/audit-lifecycle.py "$OUTPUT" \
  --label-regex '^[24]B-(plain|mtp)-code-long$' \
  --require-identical --require-token-ids --min-runs-per-group 4
