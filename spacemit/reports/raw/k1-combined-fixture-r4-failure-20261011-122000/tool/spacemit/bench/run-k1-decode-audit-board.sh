#!/usr/bin/env bash
set -euo pipefail
AUDIT_ROOT=$1
exec >> "$AUDIT_ROOT/driver.log" 2>&1
trap 'audit_status=$?; printf "%s\n" "$audit_status" > "$AUDIT_ROOT/exit-status"' EXIT
printf 'waiting for board benchmark lock\n' > "$AUDIT_ROOT/phase"
exec 9> "$HOME/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock"
flock -w 43200 9
if pgrep -x llama-server >/dev/null; then
  echo 'another server is active; stopping' >&2
  exit 1
fi
for audit_env_name in ${!SPINE_@}; do unset "$audit_env_name"; done
export LD_LIBRARY_PATH
LD_LIBRARY_PATH=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["runtime"]["LD_LIBRARY_PATH"])' "$AUDIT_ROOT/expected-provenance.json")
timeout --signal=TERM --kill-after=30s 14400s python3 "$AUDIT_ROOT/k1-decode-audit.py" "$AUDIT_ROOT"
