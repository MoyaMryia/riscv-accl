#!/usr/bin/env bash
set -euo pipefail
VALIDATION_ROOT=$1
exec >> "$VALIDATION_ROOT/driver.log" 2>&1
trap 'validation_status=$?; printf "%s\n" "$validation_status" > "$VALIDATION_ROOT/exit-status"' EXIT
printf 'waiting for board benchmark lock\n' > "$VALIDATION_ROOT/phase"
exec 9> "$HOME/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock"
flock -w 43200 9
if pgrep -x llama-server >/dev/null; then
    printf 'unmanaged llama-server is running\n' > "$VALIDATION_ROOT/phase"
    exit 1
fi
for validation_env_name in ${!SPINE_@} ${!SPACEMIT_@}; do unset "$validation_env_name"; done
timeout --signal=TERM --kill-after=30s 43200s python3 "$VALIDATION_ROOT/k1-validation.py" "$VALIDATION_ROOT"
