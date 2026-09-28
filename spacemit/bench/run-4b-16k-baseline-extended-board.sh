#!/usr/bin/env bash
# Complete the RVV-off 4B real-16k arm with a bound informed by the 12k result.
set -euo pipefail

BENCH_ROOT=${BENCH_ROOT:-"$HOME/Projects/riscv-accl-bench-2026-09-27"}
SERVER_ROOT=${SERVER_ROOT:-"$HOME/Projects/spacemit-llama-integrated"}
MODEL="$HOME/Projects/spacemit-llama/models/Qwen3.5-4B-MTP-Q4_0-embQ4_0-dv64k.gguf"
LABEL=4B-q4w-f16kv-16k-rvv0-extended
OUTPUT="$BENCH_ROOT/$LABEL.jsonl"
LOG="$BENCH_ROOT/$LABEL.log"

if [ -e "$OUTPUT" ]; then echo "existing output: $OUTPUT" >&2; exit 1; fi
if pgrep -x llama-server >/dev/null; then echo 'another server is running' >&2; exit 1; fi
if [ "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -lt 10485760 ]; then
  echo 'less than 10 GiB MemAvailable' >&2; exit 1
fi

export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$SERVER_ROOT/build/bin"
export SPINE_FA_WIDE_TILE=0
unset SPINE_MTP_WINDOW SPINE_SPEC_RS
echo "START $LABEL $(date -Is)"
(
  ulimit -v 12582912
  timeout --signal=TERM --kill-after=10s 18000s python3 "$BENCH_ROOT/bench-lifecycle.py" \
    --server "$SERVER_ROOT/build/bin/llama-server" --model "$MODEL" --label "$LABEL" \
    --mode plain --contexts 16384 --ctx-size 20480 --n-predict 32 \
    --threads 4 --batch-size 32 --ubatch-size 32 \
    --cache-type-k f16 --cache-type-v f16 --timeout 18000 \
    --output "$OUTPUT" --log "$LOG"
)
python3 "$BENCH_ROOT/audit-lifecycle.py" "$OUTPUT" --require-token-ids
