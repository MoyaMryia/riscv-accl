#!/usr/bin/env bash
# Detached completion watcher for a benchmark that was already launched over SSH.
set -uo pipefail
BENCH_ROOT=${BENCH_ROOT:-"$HOME/Projects/riscv-accl-bench-2026-09-27"}
bench_pid=${1:?benchmark Python PID required}
result="$BENCH_ROOT/4B-shared-document-16384-rvv1.jsonl"
summary="$BENCH_ROOT/shared-document-detached-audit.log"
echo "WATCH PID $bench_pid $(date -Is)" > "$summary"
while kill -0 "$bench_pid" 2>/dev/null; do sleep 30; done
if [ ! -s "$result" ]; then
  echo 'FAIL: result file missing' >> "$summary"
  exit 1
fi
python3 "$BENCH_ROOT/audit-shared-document-cache.py" "$result" 16384 4B >> "$summary" 2>&1
status=$?
echo "AUDIT_EXIT $status $(date -Is)" >> "$summary"
exit "$status"
