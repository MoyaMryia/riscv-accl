#!/bin/bash
set -uo pipefail
while [ -d /proc/154698 ] && ! grep -q '^State:.*Z' /proc/154698/status; do sleep 20; done
ROOT="$HOME/Projects/spacemit-llama-window"
MODELS="$HOME/Projects/spacemit-llama/models"
if [ ! -x "$ROOT/build/bin/llama-server" ]; then
  echo "windowed MTP build unavailable" >&2
  exit 1
fi
mapfile -t sizes < <(python3 /tmp/select-windowed-control.py /tmp/lifecycle-windowed.jsonl)
if [ "${#sizes[@]}" -eq 0 ]; then
  echo "No completed windowed long run needs a control" >&2
  exit 0
fi
unset SPINE_MTP_WINDOW
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$ROOT/build/bin"
for size in "${sizes[@]}"; do
  label="${size}-full-mtp-12k-samebuild"
  echo "START $label"
  python3 /tmp/bench-lifecycle.py \
    --server "$ROOT/build/bin/llama-server" \
    --model "$MODELS/Qwen3.5-${size}-MTP-Q4_0-embQ4_0-dv64k.gguf" \
    --label "$label" --mode mtp --contexts 12288 --n-predict 128 \
    --ctx-size 16384 --output /tmp/lifecycle-windowed-control.jsonl \
    --log "/tmp/lifecycle-${label}.log" || echo "FAILED $label"
done
