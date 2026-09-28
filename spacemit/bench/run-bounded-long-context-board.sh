#!/usr/bin/env bash
# One bounded, real long-prompt request on the MUSE-Pi-Pro board.
set -euo pipefail

BENCH_ROOT=${BENCH_ROOT:-"$HOME/Projects/riscv-accl-bench-2026-09-27"}
SERVER_ROOT=${SERVER_ROOT:-"$HOME/Projects/spacemit-llama-integrated"}
MODEL_SIZE=${MODEL_SIZE:-2B}
PROMPT_TOKENS=${PROMPT_TOKENS:-32768}
TIME_LIMIT_S=${TIME_LIMIT_S:-10800}

case "$MODEL_SIZE" in 2B|4B) ;; *) echo 'MODEL_SIZE must be 2B or 4B' >&2; exit 2;; esac
case "$PROMPT_TOKENS" in 32768|65536) ;; *) echo 'PROMPT_TOKENS must be 32768 or 65536' >&2; exit 2;; esac

label="${MODEL_SIZE}-q4w-f16kv-${PROMPT_TOKENS}-rvv1-bounded"
output="$BENCH_ROOT/$label.jsonl"
log="$BENCH_ROOT/$label.log"
if [ -e "$output" ]; then echo "existing output: $output" >&2; exit 1; fi
if pgrep -x llama-server >/dev/null; then echo 'another server is running' >&2; exit 1; fi
if [ "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -lt 10485760 ]; then
  echo 'less than 10 GiB MemAvailable' >&2; exit 1
fi

export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$SERVER_ROOT/build/bin"
export SPINE_FA_WIDE_TILE=1
unset SPINE_MTP_WINDOW SPINE_SPEC_RS
model="$HOME/Projects/spacemit-llama/models/Qwen3.5-${MODEL_SIZE}-MTP-Q4_0-embQ4_0-dv64k.gguf"
ctx_size=$((PROMPT_TOKENS + 4096))
echo "START $label $(date -Is)"
(
  ulimit -v 12582912
  timeout --signal=TERM --kill-after=10s "${TIME_LIMIT_S}s" python3 "$BENCH_ROOT/bench-lifecycle.py" \
    --server "$SERVER_ROOT/build/bin/llama-server" --model "$model" --label "$label" \
    --mode plain --contexts "$PROMPT_TOKENS" --ctx-size "$ctx_size" --n-predict 32 \
    --threads 4 --batch-size 32 --ubatch-size 32 \
    --cache-type-k f16 --cache-type-v f16 --timeout "$TIME_LIMIT_S" \
    --output "$output" --log "$log"
)
grep -q 'SPINE_FA_WIDE_TILE: RVV tiled attention enabled for 256-dim heads' "$log"
python3 "$BENCH_ROOT/audit-lifecycle.py" "$output" --require-token-ids
