#!/usr/bin/env bash
# Verify real PowerVR Vulkan layer transfer before any GPU speed claim.
set -euo pipefail

BENCH_ROOT=${BENCH_ROOT:-"$HOME/Projects/riscv-accl-bench-2026-09-27"}
SERVER_ROOT="$HOME/Projects/spacemit-llama-vulkan"
SERVER="$SERVER_ROOT/build/bin/llama-server"
MODEL="$HOME/Projects/spacemit-llama/models/Qwen3.5-2B-MTP-Q4_0-embQ4_0-dv64k.gguf"
OUT="$BENCH_ROOT/lifecycle-vulkan-smoke.jsonl"
RUNTIME="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$SERVER_ROOT/build/bin"

if [ ! -x "$SERVER" ] || [ -e "$OUT" ]; then
  echo 'missing Vulkan server or existing result' >&2
  exit 1
fi
if pgrep -x llama-server >/dev/null; then
  echo 'another llama-server is running' >&2
  exit 1
fi

for layers in 0 4; do
  label="2B-vulkan-ngl${layers}-smoke"
  log="$BENCH_ROOT/$label.log"
  echo "START $label $(date -Is)"
  sudo -n setpriv --reuid=1000 --regid=1000 --groups=1000,993 \
    env LD_LIBRARY_PATH="$RUNTIME" \
    timeout --signal=TERM --kill-after=10s 1200s python3 "$BENCH_ROOT/bench-lifecycle.py" \
      --server "$SERVER" --model "$MODEL" --label "$label" \
      --mode plain --contexts 128 --ctx-size 4096 --n-predict 32 \
      --gpu-layers "$layers" --threads 4 --batch-size 32 --ubatch-size 32 \
      --cache-type-k f16 --cache-type-v f16 --timeout 1200 \
      --output "$OUT" --log "$log"
done
python3 "$BENCH_ROOT/audit-lifecycle.py" "$OUT" --require-token-ids --min-runs-per-group 2
grep -E 'Vulkan|offloaded [0-9]+/[0-9]+ layers to GPU' "$BENCH_ROOT/2B-vulkan-ngl4-smoke.log" | tail -20
grep -Eq 'offloaded [1-9][0-9]*/[0-9]+ layers to GPU' "$BENCH_ROOT/2B-vulkan-ngl4-smoke.log"
echo 'PASS: Vulkan server transferred model layers to GPU'
