#!/usr/bin/env bash
set -euo pipefail
work=/tmp/k1-combined-repair-work
exec >"$work/failure-sync-collector.log" 2>&1
trap 'result=$?; printf "%s\n" "$result" >"$work/failure-sync-exit-status"' EXIT
deadline=$((SECONDS+7200))
while fuser -s "$work/failed-full-deduplicated.tar.gz"; do
    test "$SECONDS" -lt "$deadline"
    sleep 30
done
gzip -t "$work/failed-full-deduplicated.tar.gz"
python3 "$work/finish_failure_sync.py"
