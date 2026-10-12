#!/usr/bin/env bash
set -euo pipefail
ATTENTION_ROOT=$1
exec >> "$ATTENTION_ROOT/driver.log" 2>&1
trap 'attention_status=$?; printf "%s\n" "$attention_status" > "$ATTENTION_ROOT/exit-status"' EXIT
printf 'waiting for board benchmark lock\n' > "$ATTENTION_ROOT/phase"
exec 9> "$HOME/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock"
flock -w 43200 9
if pgrep -x llama-server >/dev/null; then
  echo 'another server is active; stopping' >&2
  exit 1
fi
for attention_env_name in ${!SPINE_@} ${!SPACEMIT_@}; do unset "$attention_env_name"; done
timeout --signal=TERM --kill-after=20s 7200s python3 "$ATTENTION_ROOT/k1-attention-infra.py" "$ATTENTION_ROOT"
