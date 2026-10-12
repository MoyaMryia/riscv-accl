#!/usr/bin/env bash
# Matched Q4_0/Q8_0 weight comparison on MUSE-Pi-Pro, with F16 K/V fixed.
set -euo pipefail

BENCH_ROOT=${BENCH_ROOT:-"$HOME/Projects/riscv-accl-bench-2026-09-27"}
SERVER_ROOT=${SERVER_ROOT:-"$HOME/Projects/spacemit-llama-integrated"}
SERVER="$SERVER_ROOT/build/bin/llama-server"
OUT="$BENCH_ROOT/lifecycle-weight-compare-2k.jsonl"

if [ -e "$OUT" ]; then echo "existing output: $OUT" >&2; exit 1; fi
if pgrep -x llama-server >/dev/null; then echo 'another server is running' >&2; exit 1; fi
if [ "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -lt 10485760 ]; then
  echo 'less than 10 GiB MemAvailable' >&2; exit 1
fi
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$SERVER_ROOT/build/bin"
export SPINE_FA_WIDE_TILE=1
unset SPINE_MTP_WINDOW SPINE_SPEC_RS

for size in 2B 4B; do
  pass=0
  for weight in Q4_0 Q8_0 Q8_0 Q4_0; do
    pass=$((pass+1))
    if [ "$weight" = Q4_0 ]; then
      model="$HOME/Projects/spacemit-llama/models/Qwen3.5-${size}-Q4_0-embQ4_0.gguf"
    else
      if [ "$size" = 2B ]; then
        model="$HOME/Projects/llm-bench/models/Qwen3.5-2B-Q8_0.gguf"
      else
        model="$HOME/Projects/spacemit-llama/models/Qwen3.5-4B-Q8_0.gguf"
      fi
    fi
    label="${size}-${weight}-f16kv-rvv-2k-pass${pass}"
    log="$BENCH_ROOT/${label}.log"
    echo "START $label $(date -Is)"
    (
      ulimit -v 12582912
      timeout --signal=TERM --kill-after=10s 2400s python3 "$BENCH_ROOT/bench-lifecycle.py" \
        --server "$SERVER" --model "$model" --label "$label" \
        --mode plain --contexts 2048 --ctx-size 4096 --n-predict 32 \
        --threads 4 --batch-size 32 --ubatch-size 32 \
        --cache-type-k f16 --cache-type-v f16 --timeout 2400 \
        --output "$OUT" --log "$log"
    )
    grep -q 'SPINE_FA_WIDE_TILE: RVV tiled attention enabled for 256-dim heads' "$log"
  done
done
python3 "$BENCH_ROOT/audit-lifecycle.py" "$OUT" \
  --require-identical --require-token-ids --min-runs-per-group 2
