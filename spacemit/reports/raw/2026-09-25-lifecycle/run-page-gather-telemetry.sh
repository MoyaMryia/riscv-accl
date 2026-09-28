#!/bin/bash
set -euo pipefail
while [ -d /proc/243384 ] && ! grep -q '^State:.*Z' /proc/243384/status; do sleep 20; done
ROOT="$HOME/Projects/spacemit-llama-page-gather"
MODEL="$HOME/Projects/spacemit-llama/models/Qwen3.5-2B-MTP-Q4_0-embQ4_0-dv64k.gguf"
OUTPUT=/tmp/lifecycle-page-gather-telemetry.jsonl
LOG=/tmp/lifecycle-2B-page-gather-telemetry.log
if [ -e "$OUTPUT" ]; then echo "existing $OUTPUT" >&2; exit 1; fi
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$ROOT/build/bin"
export SPINE_KV_PAGE_GATHER=1
python3 /tmp/bench-lifecycle-telemetry.py --server "$ROOT/build/bin/llama-server" \
  --model "$MODEL" --label 2B-page-gather-telemetry --mode plain \
  --contexts 128 --slot-contexts 128 256 512 1024 --rotate-slot-contexts \
  --repeats 2 --parallel 4 --concurrency 4 --kv-unified --n-predict 32 \
  --ctx-size 8192 --server-log-verbosity 5 --output "$OUTPUT" --log "$LOG"
grep -m 12 'SPINE_KV_PAGE_GATHER:' "$LOG" | cut -c 1-200
python3 /tmp/audit-lifecycle.py /tmp/lifecycle-page-gather.jsonl "$OUTPUT" \
  --label-regex '^2B-page-gather-' --require-identical --require-token-ids \
  --min-runs-per-group 10
