#!/usr/bin/env bash
set -euo pipefail
RELEASE_ROOT=$1
exec >> "$RELEASE_ROOT/driver.log" 2>&1
trap 'release_status=$?; printf "%s\n" "$release_status" > "$RELEASE_ROOT/exit-status"' EXIT
printf 'waiting for board benchmark lock\n' > "$RELEASE_ROOT/phase"
exec 9> "$HOME/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock"
flock -w 43200 9
if pgrep -x llama-server >/dev/null; then
  echo 'another server is active; stopping' >&2
  exit 1
fi
for release_env_name in ${!SPINE_@}; do unset "$release_env_name"; done
export LD_LIBRARY_PATH
LD_LIBRARY_PATH=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["runtime"]["LD_LIBRARY_PATH"])' "$RELEASE_ROOT/expected-provenance.json")
timeout --signal=TERM --kill-after=30s 21600s python3 "$RELEASE_ROOT/k1-release-check.py" "$RELEASE_ROOT"
