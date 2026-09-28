#!/bin/bash
set -euo pipefail
while [ -d /proc/243809 ] && ! grep -q '^State:.*Z' /proc/243809/status; do sleep 20; done
ROOT="$HOME/Projects/spacemit-llama-window"
MODELS="$HOME/Projects/spacemit-llama/models"
OUTPUT=/tmp/lifecycle-windowed-abba.jsonl
if [ -e "$OUTPUT" ] || [ ! -x "$ROOT/build/bin/llama-server" ]; then
  echo 'output exists or windowed build missing' >&2
  exit 1
fi
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$ROOT/build/bin"
for size in 2B 4B; do
  for arm in full window window full; do
    if [ "$arm" = window ]; then
      export SPINE_MTP_WINDOW=2048
    else
      unset SPINE_MTP_WINDOW
    fi
    label="${size}-mtp-${arm}-12k-abba"
    echo "START $label"
    python3 /tmp/bench-lifecycle.py --server "$ROOT/build/bin/llama-server" \
      --model "$MODELS/Qwen3.5-${size}-MTP-Q4_0-embQ4_0-dv64k.gguf" \
      --label "$label" --mode mtp --contexts 12288 --n-predict 128 \
      --ctx-size 16384 --timeout 14400 --output "$OUTPUT" \
      --log "/tmp/lifecycle-${label}-$(date +%s).log"
  done
done
python3 /tmp/audit-lifecycle.py "$OUTPUT" \
  --require-identical --require-token-ids --min-runs-per-group 4
