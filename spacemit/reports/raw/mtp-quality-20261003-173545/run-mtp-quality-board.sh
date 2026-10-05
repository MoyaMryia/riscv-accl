#!/usr/bin/env bash
set -euo pipefail
MTP_QUALITY_ROOT=$1
exec >> "$MTP_QUALITY_ROOT/driver.log" 2>&1
trap 'quality_status=$?; printf "%s\n" "$quality_status" > "$MTP_QUALITY_ROOT/exit-status"' EXIT
printf 'waiting for shared benchmark lock\n' > "$MTP_QUALITY_ROOT/phase"
exec 9> "$HOME/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock"
flock -w 3600 9
if pgrep -x llama-server >/dev/null; then exit 1; fi
for quality_env_name in ${!SPINE_@} ${!SPACEMIT_@}; do unset "$quality_env_name"; done
timeout --signal=TERM --kill-after=30s 21600s python3 "$MTP_QUALITY_ROOT/mtp-quality.py" "$MTP_QUALITY_ROOT"
