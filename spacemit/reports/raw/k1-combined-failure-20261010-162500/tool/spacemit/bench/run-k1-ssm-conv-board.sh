#!/usr/bin/env bash
set -euo pipefail
SSM_RUN_ROOT=$1
exec >> "$SSM_RUN_ROOT/driver.log" 2>&1
trap 'ssm_status=$?; printf "%s\n" "$ssm_status" > "$SSM_RUN_ROOT/exit-status"' EXIT
printf 'waiting for board benchmark lock\n' > "$SSM_RUN_ROOT/phase"
exec 9> "$HOME/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock"
flock -w 43200 9
if pgrep -x llama-server >/dev/null; then exit 1; fi
for ssm_env_name in ${!SPINE_@} ${!SPACEMIT_@}; do unset "$ssm_env_name"; done
timeout --signal=TERM --kill-after=20s 7200s python3 "$SSM_RUN_ROOT/k1-ssm-conv.py" "$SSM_RUN_ROOT"
