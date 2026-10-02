#!/usr/bin/env bash
set -euo pipefail
PROFILE_ROOT=$1
exec >> "$PROFILE_ROOT/driver.log" 2>&1
trap 'profile_status=$?; printf "%s\n" "$profile_status" > "$PROFILE_ROOT/exit-status"' EXIT
printf 'waiting for board benchmark lock\n' > "$PROFILE_ROOT/phase"
exec 9> "$HOME/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock"
flock -w 43200 9
if pgrep -x llama-server >/dev/null; then
  echo 'another server is active; stopping' >&2
  exit 1
fi
for profile_env_name in ${!SPINE_@}; do unset "$profile_env_name"; done
export LD_LIBRARY_PATH
LD_LIBRARY_PATH=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["runtime"]["LD_LIBRARY_PATH"])' "$PROFILE_ROOT/expected-provenance.json")
timeout --signal=TERM --kill-after=20s 1800s python3 "$PROFILE_ROOT/profile-k1-prefill.py" "$PROFILE_ROOT"
