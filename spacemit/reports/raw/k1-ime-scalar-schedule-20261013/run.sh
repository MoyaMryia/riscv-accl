#!/usr/bin/env bash
set -euo pipefail
SCALAR_ROOT=$1
exec >> "$SCALAR_ROOT/run.log" 2>&1
trap 'scalar_status=$?; printf "%s\n" "$scalar_status" > "$SCALAR_ROOT/exit-status"' EXIT
timeout --signal=TERM --kill-after=20s 1200s python3 "$SCALAR_ROOT/board.py" "$SCALAR_ROOT"
