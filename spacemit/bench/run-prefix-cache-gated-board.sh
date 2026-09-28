#!/usr/bin/env bash
# Same-process 2B prefix reuse, with 32k attempted only after 8k and 16k pass.
set -euo pipefail

BENCH_ROOT=${BENCH_ROOT:-"$HOME/Projects/riscv-accl-bench-2026-09-27"}
SERVER_ROOT=${SERVER_ROOT:-"$HOME/Projects/spacemit-llama-integrated"}
model="$HOME/Projects/spacemit-llama/models/Qwen3.5-2B-MTP-Q4_0-embQ4_0-dv64k.gguf"

if pgrep -x llama-server >/dev/null; then echo 'another server is running' >&2; exit 1; fi
if [ "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -lt 10485760 ]; then
  echo 'less than 10 GiB MemAvailable' >&2; exit 1
fi
for context in 8192 16384 32768; do
  if [ -e "$BENCH_ROOT/2B-prefix-cache-${context}-rvv1.jsonl" ]; then
    echo "existing output for $context" >&2; exit 1
  fi
done

export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$SERVER_ROOT/build/bin"
export SPINE_FA_WIDE_TILE=1
unset SPINE_MTP_WINDOW SPINE_SPEC_RS

for context in 8192 16384 32768; do
  label="2B-prefix-cache-${context}-rvv1"
  output="$BENCH_ROOT/$label.jsonl"
  log="$BENCH_ROOT/$label.log"
  case "$context" in
    8192) limit=7200 ;;
    16384) limit=10800 ;;
    32768) limit=18000 ;;
  esac
  echo "START $label $(date -Is)"
  (
    ulimit -v 12582912
    timeout --signal=TERM --kill-after=10s "${limit}s" python3 "$BENCH_ROOT/bench-lifecycle.py" \
      --server "$SERVER_ROOT/build/bin/llama-server" --model "$model" --label "$label" \
      --mode plain --contexts "$context" --ctx-size "$((context + 4096))" \
      --n-predict 32 --repeats 3 --cache-prompt --capture-token-ids \
      --threads 4 --batch-size 32 --ubatch-size 32 \
      --cache-type-k f16 --cache-type-v f16 --timeout "$limit" \
      --output "$output" --log "$log" >/dev/null
  )
  grep -q 'SPINE_FA_WIDE_TILE: RVV tiled attention enabled for 256-dim heads' "$log"
  python3 "$BENCH_ROOT/check-prefix-cache.py" "$output" "$context"
done
