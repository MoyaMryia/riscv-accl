#!/usr/bin/env bash
# Resume the interrupted integrated 4B 12k RVV off/on pair on MUSE-Pi-Pro.
set -euo pipefail

BENCH_ROOT=${BENCH_ROOT:-"$HOME/Projects/riscv-accl-bench-2026-09-27"}
SERVER_ROOT=${SERVER_ROOT:-"$HOME/Projects/spacemit-llama-integrated"}
SERVER="$SERVER_ROOT/build/bin/llama-server"
MODEL="$HOME/Projects/spacemit-llama/models/Qwen3.5-4B-MTP-Q4_0-embQ4_0-dv64k.gguf"
OUTPUT="$BENCH_ROOT/lifecycle-integrated-4b-rvv-12k-resume.jsonl"

if [ -e "$OUTPUT" ]; then echo "existing output: $OUTPUT" >&2; exit 1; fi
if pgrep -x llama-server >/dev/null; then echo 'another server is running' >&2; exit 1; fi
if [ "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -lt 10485760 ]; then
  echo 'less than 10 GiB MemAvailable' >&2; exit 1
fi
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$SERVER_ROOT/build/bin"
unset SPINE_MTP_WINDOW SPINE_SPEC_RS

# Run the optimized arm first so an interrupted slow baseline still leaves a
# complete actual 12k request. Each arm is limited to four hours and 12 GiB VA.
for rvv in 1 0; do
  export SPINE_FA_WIDE_TILE="$rvv"
  label="4B-rvv32-integrated-12k-resume-$rvv"
  log="$BENCH_ROOT/$label.log"
  echo "START $label $(date -Is)"
  (
    ulimit -v 12582912
    timeout --signal=TERM --kill-after=10s 14400s python3 "$BENCH_ROOT/bench-lifecycle.py" \
      --server "$SERVER" --model "$MODEL" --label "$label" \
      --mode plain --contexts 12288 --ctx-size 16384 --n-predict 32 \
      --threads 4 --batch-size 32 --ubatch-size 32 \
      --cache-type-k f16 --cache-type-v f16 --timeout 14400 \
      --output "$OUTPUT" --log "$log"
  )
  if [ "$rvv" -eq 1 ]; then
    grep -q 'SPINE_FA_WIDE_TILE: RVV tiled attention enabled for 256-dim heads' "$log"
  fi
done
python3 "$BENCH_ROOT/audit-lifecycle.py" "$OUTPUT" \
  --require-identical --require-token-ids --min-runs-per-group 2
