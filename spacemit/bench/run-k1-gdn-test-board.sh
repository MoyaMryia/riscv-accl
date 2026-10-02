#!/usr/bin/env bash
set -euo pipefail
GDN_ROOT=$1
exec >> "$GDN_ROOT/driver.log" 2>&1
trap 'gdn_status=$?; printf "%s\n" "$gdn_status" > "$GDN_ROOT/exit-status"' EXIT
printf 'waiting for board benchmark lock\n' > "$GDN_ROOT/phase"
exec 9> "$HOME/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock"
flock -w 43200 9
if pgrep -x llama-server >/dev/null; then
  echo 'another server is active; stopping' >&2
  exit 1
fi
for gdn_env_name in ${!SPINE_@}; do unset "$gdn_env_name"; done
timeout --signal=TERM --kill-after=20s 2700s python3 "$GDN_ROOT/k1-gdn-test.py" "$GDN_ROOT"
