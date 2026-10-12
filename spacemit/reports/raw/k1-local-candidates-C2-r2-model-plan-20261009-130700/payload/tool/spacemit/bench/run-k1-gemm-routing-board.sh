#!/usr/bin/env bash
set -euo pipefail
ROUTE_ROOT=$1
exec >> "$ROUTE_ROOT/driver.log" 2>&1
trap 'route_status=$?; printf "%s\n" "$route_status" > "$ROUTE_ROOT/exit-status"' EXIT
printf 'waiting for board benchmark lock\n' > "$ROUTE_ROOT/phase"
exec 9> "$HOME/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock"
flock -w 43200 9
if pgrep -x llama-server >/dev/null; then exit 1; fi
for route_env_name in ${!SPINE_@} ${!SPACEMIT_@}; do unset "$route_env_name"; done
timeout --signal=TERM --kill-after=20s 3600s python3 "$ROUTE_ROOT/k1-gemm-routing.py" "$ROUTE_ROOT"
