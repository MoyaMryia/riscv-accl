#!/usr/bin/env bash
set -euo pipefail
RUN_ROOT=$1
BUILD_RUN=$2
MODE=$3
exec >> "$RUN_ROOT/driver.log" 2>&1
trap 'status=$?; printf "%s\n" "$status" > "$RUN_ROOT/exit-status"' EXIT
printf 'waiting for board benchmark lock\n' > "$RUN_ROOT/phase"
exec 9> "$HOME/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock"
flock -w 43200 9
if pgrep -x llama-server >/dev/null; then
  echo 'another server is active; stopping' >&2
  exit 1
fi
SPERT_DIR="$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2"
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$SPERT_DIR/lib:$BUILD_RUN/source/build/bin"
export SPINE_FA_WIDE_TILE=1
unset SPINE_FA_K1_LAYOUT SPINE_MTP_WINDOW SPINE_SPEC_RS SPINE_KV_PAGE_GATHER
unset SPINE_SPEC_LOWACC SPINE_SPEC_MAX_CONTEXT SPINE_GDN_RVV
python3 "$RUN_ROOT/k1-fast-test.py" "$RUN_ROOT" "$BUILD_RUN" --mode "$MODE"
