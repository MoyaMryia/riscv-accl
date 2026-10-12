#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"
exec 9>/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock
if ! flock -n 9; then
    echo busy > launch-status
    exit 75
fi
if pgrep -x llama-bench >/dev/null || pgrep -x llama-server >/dev/null; then
    echo task-present > launch-status
    exit 75
fi
printf 'locked\n' > launch-status
python3 collect.py >driver.log 2>&1
result=$?
printf '%s\n' "$result" > exit-status
exit "$result"
