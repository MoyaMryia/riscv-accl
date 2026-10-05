#!/usr/bin/env bash
set -euo pipefail
ADAPTIVE_MTP_ROOT=$1
exec >> "$ADAPTIVE_MTP_ROOT/driver.log" 2>&1
trap 'adaptive_status=$?; printf "%s\n" "$adaptive_status" > "$ADAPTIVE_MTP_ROOT/exit-status"' EXIT
exec 9> "$HOME/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock"
flock -w 3600 9
if pgrep -x llama-server >/dev/null; then exit 1; fi
for adaptive_env_name in ${!SPINE_@} ${!SPACEMIT_@}; do unset "$adaptive_env_name"; done
timeout --signal=TERM --kill-after=30s 21600s python3 "$ADAPTIVE_MTP_ROOT/adaptive-mtp-test.py" "$ADAPTIVE_MTP_ROOT"
