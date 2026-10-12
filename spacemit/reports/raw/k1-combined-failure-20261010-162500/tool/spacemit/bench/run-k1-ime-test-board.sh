#!/usr/bin/env bash
set -euo pipefail
IME_ROOT=$1
exec >> "$IME_ROOT/driver.log" 2>&1
trap 'ime_status=$?; printf "%s\n" "$ime_status" > "$IME_ROOT/exit-status"' EXIT
printf 'waiting for board benchmark lock\n' > "$IME_ROOT/phase"
exec 9> "$HOME/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock"
flock -w 43200 9
if pgrep -x llama-server >/dev/null; then
  echo 'another server is active; stopping' >&2
  exit 1
fi
for ime_env_name in ${!SPINE_@}; do unset "$ime_env_name"; done
timeout --signal=TERM --kill-after=20s 2700s python3 "$IME_ROOT/k1-ime-test.py" "$IME_ROOT"
