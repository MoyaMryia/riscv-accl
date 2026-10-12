#!/usr/bin/env bash
# Run on MUSE-Pi-Pro after staging bench-lifecycle.py in BENCH_ROOT.
set -euo pipefail

BENCH_ROOT=${BENCH_ROOT:-"$HOME/Projects/riscv-accl-bench-2026-09-27"}
SERVER_ROOT=${SERVER_ROOT:-"$HOME/Projects/spacemit-llama-integrated"}
MODEL_ROOT=${MODEL_ROOT:-"$HOME/Projects/spacemit-llama/models"}
RUNNER="$BENCH_ROOT/bench-lifecycle.py"
SERVER="$SERVER_ROOT/build/bin/llama-server"

if [ ! -f "$RUNNER" ] || [ ! -x "$SERVER" ]; then
  echo 'missing benchmark runner or server binary' >&2
  exit 1
fi
if pgrep -x llama-server >/dev/null; then
  echo 'another llama-server is running; keep board measurements serialized' >&2
  exit 1
fi
if [ "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -lt 10485760 ]; then
  echo 'less than 10 GiB MemAvailable; skipping long-context run' >&2
  exit 1
fi

export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$SERVER_ROOT/build/bin"
unset SPINE_MTP_WINDOW SPINE_SPEC_RS

# 12 GiB address-space limit and three-hour per-arm wall limit on a 15 GiB board.
# The 20,480-token allocation fits a real 16,384-token prompt plus 32 outputs.
for size in 2B 4B; do
  model="$MODEL_ROOT/Qwen3.5-${size}-MTP-Q4_0-embQ4_0-dv64k.gguf"
  for rvv in 1 0; do
    label="${size}-q4w-f16kv-16k-rvv${rvv}"
    output="$BENCH_ROOT/${label}.jsonl"
    log="$BENCH_ROOT/${label}.log"
    if [ -e "$output" ]; then
      echo "existing result: $output" >&2
      exit 1
    fi
    echo "START $label $(date -Is)"
    (
      ulimit -v 12582912
      export SPINE_FA_WIDE_TILE="$rvv"
      timeout --signal=TERM --kill-after=10s 10800s python3 "$RUNNER" \
        --server "$SERVER" --model "$model" --label "$label" \
        --mode plain --contexts 16384 --ctx-size 20480 --n-predict 32 \
        --batch-size 32 --ubatch-size 32 --threads 4 \
        --cache-type-k f16 --cache-type-v f16 --timeout 10800 \
        --output "$output" --log "$log"
    )
    if [ "$rvv" -eq 1 ]; then
      grep -q 'SPINE_FA_WIDE_TILE: RVV tiled attention enabled for 256-dim heads' "$log"
    fi
  done
  python3 "$BENCH_ROOT/audit-lifecycle.py" \
    "$BENCH_ROOT/${size}-q4w-f16kv-16k-rvv0.jsonl" \
    "$BENCH_ROOT/${size}-q4w-f16kv-16k-rvv1.jsonl" \
    --require-identical --require-token-ids --min-runs-per-group 2
done
