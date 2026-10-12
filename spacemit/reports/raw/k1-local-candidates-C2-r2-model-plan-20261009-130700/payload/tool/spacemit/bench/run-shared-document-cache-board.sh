#!/usr/bin/env bash
# Gated changed-question cache test, one server at a time on MUSE-Pi-Pro.
set -euo pipefail

BENCH_ROOT=${BENCH_ROOT:-"$HOME/Projects/riscv-accl-bench-2026-09-27"}
SERVER_ROOT=${SERVER_ROOT:-"$HOME/Projects/spacemit-llama-integrated"}
DOCUMENT=${DOCUMENT:-"$BENCH_ROOT/shared-document-public-llamacpp.txt"}
INCLUDE_4B_32K=${INCLUDE_4B_32K:-0}
case "$INCLUDE_4B_32K" in 0|1) ;; *) echo 'INCLUDE_4B_32K must be 0 or 1' >&2; exit 2;; esac

if pgrep -x llama-server >/dev/null; then echo 'another server is running' >&2; exit 1; fi
if [ ! -e "$DOCUMENT" ]; then
  # Assemble public documentation already present in the board's llama.cpp fork.
  docs=("$SERVER_ROOT/README.md")
  for path in "$SERVER_ROOT"/docs/*.md; do docs+=("$path"); done
  for path in "${docs[@]}"; do
    if [ ! -s "$path" ]; then echo "missing source document: $path" >&2; exit 1; fi
  done
  for path in "${docs[@]}"; do
    printf '\n\n===== %s =====\n\n' "${path#"$SERVER_ROOT"/}"
    cat "$path"
    printf '\n'
  done > "$DOCUMENT"
fi
if [ ! -s "$DOCUMENT" ]; then echo "missing document: $DOCUMENT" >&2; exit 1; fi
if [ "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -lt 10485760 ]; then
  echo 'less than 10 GiB MemAvailable' >&2; exit 1
fi

export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$SERVER_ROOT/build/bin"
export SPINE_FA_WIDE_TILE=1
unset SPINE_MTP_WINDOW SPINE_SPEC_RS

run_one() {
  local model_size=$1 context=$2 timeout_s label output log total_s model
  case "$model_size:$context" in
    2B:8192) timeout_s=3600 ;;
    2B:16384) timeout_s=5400 ;;
    2B:32768) timeout_s=9000 ;;
    4B:8192) timeout_s=5400 ;;
    4B:16384) timeout_s=9000 ;;
    4B:32768) timeout_s=18000 ;;
    *) echo 'unsupported model/context' >&2; exit 2 ;;
  esac
  total_s=$((2 * timeout_s + 900))
  label="${model_size}-shared-document-${context}-rvv1"
  output="$BENCH_ROOT/$label.jsonl"
  log="$BENCH_ROOT/$label.log"
  model="$HOME/Projects/spacemit-llama/models/Qwen3.5-${model_size}-MTP-Q4_0-embQ4_0-dv64k.gguf"
  if [ -e "$output" ] || [ -e "$log" ]; then
    if [ -s "$output" ] && [ -s "$log" ]; then
      echo "AUDIT existing $label"
      grep -q 'SPINE_FA_WIDE_TILE: RVV tiled attention enabled for 256-dim heads' "$log" || return 1
      python3 "$BENCH_ROOT/audit-shared-document-cache.py" "$output" "$context" "$model_size"
      return $?
    fi
    echo "incomplete existing artifact for $label; refusing to overwrite" >&2
    return 1
  fi
  if pgrep -x llama-server >/dev/null; then echo 'another server is running' >&2; return 1; fi
  if [ "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -lt 10485760 ]; then
    echo 'less than 10 GiB MemAvailable' >&2; return 1
  fi
  echo "START $label $(date -Is)"
  (
    ulimit -v 12582912
    timeout --signal=TERM --kill-after=20s "${total_s}s" python3 "$BENCH_ROOT/bench-shared-document-cache.py" \
      --server "$SERVER_ROOT/build/bin/llama-server" --model "$model" \
      --model-size "$model_size" --document "$DOCUMENT" \
      --context "$context" --ctx-size "$((context + 4096))" \
      --timeout "$timeout_s" --output "$output" --log "$log"
  ) || return 1
  grep -q 'SPINE_FA_WIDE_TILE: RVV tiled attention enabled for 256-dim heads' "$log" || return 1
  python3 "$BENCH_ROOT/audit-shared-document-cache.py" "$output" "$context" "$model_size"
}

failed=0
for context in 8192 16384 32768; do
  if ! run_one 2B "$context"; then failed=1; echo "STOP 2B after failed $context gate"; break; fi
done
for context in 8192 16384; do
  if ! run_one 4B "$context"; then failed=1; echo "STOP 4B after failed $context gate"; break; fi
done
if [ "$INCLUDE_4B_32K" = 1 ] && [ "$failed" = 0 ]; then
  if ! run_one 4B 32768; then failed=1; fi
fi
exit "$failed"
