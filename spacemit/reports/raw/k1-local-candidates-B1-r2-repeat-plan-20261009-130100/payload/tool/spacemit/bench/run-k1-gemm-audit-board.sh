#!/usr/bin/env bash
set -euo pipefail
GEMM_ROOT=$1
exec >> "$GEMM_ROOT/driver.log" 2>&1
trap 'gemm_status=$?; printf "%s\n" "$gemm_status" > "$GEMM_ROOT/exit-status"' EXIT
printf 'waiting for board benchmark lock\n' > "$GEMM_ROOT/phase"
exec 9> "$HOME/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock"
flock -w 43200 9
if pgrep -x llama-server >/dev/null; then exit 1; fi
for gemm_env_name in ${!SPINE_@} ${!SPACEMIT_@}; do unset "$gemm_env_name"; done
timeout --signal=TERM --kill-after=20s 1800s python3 "$GEMM_ROOT/k1-gemm-audit.py" "$GEMM_ROOT"
