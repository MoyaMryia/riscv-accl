#!/usr/bin/env bash
set -euo pipefail
ROOFLINE_ROOT=$1
exec >> "$ROOFLINE_ROOT/driver.log" 2>&1
trap 'roofline_status=$?; printf "%s\n" "$roofline_status" > "$ROOFLINE_ROOT/exit-status"' EXIT
printf 'waiting for board benchmark lock\n' > "$ROOFLINE_ROOT/phase"
exec 9> "$HOME/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock"
flock -w 43200 9
if pgrep -x llama-server >/dev/null || pgrep -x llama-bench >/dev/null; then
  echo 'another inference process is active; stopping' >&2
  exit 1
fi
timeout --signal=TERM --kill-after=30s 14400s python3 "$ROOFLINE_ROOT/k1-roofline.py" "$ROOFLINE_ROOT"
