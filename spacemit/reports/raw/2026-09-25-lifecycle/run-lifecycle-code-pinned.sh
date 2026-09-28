#!/bin/bash
set -uo pipefail
while [ -d /proc/205591 ] && ! grep -q '^State:.*Z' /proc/205591/status; do sleep 20; done
ROOT="$HOME/Projects/spacemit-llama-integrated"
MODELS="$HOME/Projects/spacemit-llama/models"
OUTPUT=/tmp/lifecycle-code-pinned.jsonl
if [ ! -s /tmp/lifecycle-code-prompt.cpp ] || [ -e "$OUTPUT" ]; then
  echo 'Missing fixed C++ prompt or existing output path; refusing to reuse campaign file' >&2
  exit 1
fi
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$ROOT/build/bin"
for concurrency in 4 8; do
  slots=()
  for ((i=0; i<concurrency; i++)); do slots+=(128); done
  arm=0
  for mode in plain mtp mtp plain; do
    arm=$((arm + 1))
    label="4B-${mode}-code-pinned-c${concurrency}-pass${arm}"
    echo "START $label"
    python3 /tmp/bench-lifecycle.py \
      --server "$ROOT/build/bin/llama-server" \
      --model "$MODELS/Qwen3.5-4B-MTP-Q4_0-embQ4_0-dv64k.gguf" \
      --label "$label" --mode "$mode" --contexts 128 \
      --slot-contexts "${slots[@]}" --prompt-file /tmp/lifecycle-code-prompt.cpp \
      --ignore-eos --n-predict 128 --ctx-size 16384 --parallel 8 \
      --concurrency "$concurrency" --output "$OUTPUT" \
      --log "/tmp/lifecycle-${label}.log" || echo "FAILED $label" >&2
  done
done
python3 /tmp/audit-lifecycle.py "$OUTPUT" --require-token-ids
python3 /tmp/audit-concurrency-slots.py "$OUTPUT"
