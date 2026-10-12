#!/usr/bin/env bash
set -euo pipefail
SSM_QUALITY_ROOT=$1
exec >> "$SSM_QUALITY_ROOT/driver.log" 2>&1
trap 'ssm_quality_status=$?; printf "%s\n" "$ssm_quality_status" > "$SSM_QUALITY_ROOT/exit-status"' EXIT
printf 'waiting for board benchmark lock\n' > "$SSM_QUALITY_ROOT/phase"
exec 9> "$HOME/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock"
flock -w 43200 9
if pgrep -x llama-server >/dev/null; then exit 1; fi
for ssm_quality_env in ${!SPINE_@} ${!SPACEMIT_@}; do unset "$ssm_quality_env"; done
timeout --signal=TERM --kill-after=30s 28800s python3 "$SSM_QUALITY_ROOT/k1-ssm-quality.py" "$SSM_QUALITY_ROOT"
