#!/usr/bin/env bash
# From the local checkout: stage code, run against board-local public docs, and archive.
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
BENCH_DIR="$REPO_ROOT/spacemit/bench"
ARCHIVE="$REPO_ROOT/spacemit/reports/raw/2026-09-25-lifecycle"
BOARD=${BOARD:-musepipro-wg}
REMOTE_ROOT='~/Projects/riscv-accl-bench-2026-09-27'
mkdir -p "$ARCHIVE"
scp "$BENCH_DIR/bench-lifecycle.py" "$BENCH_DIR/bench-shared-document-cache.py" \
    "$BENCH_DIR/audit-shared-document-cache.py" "$BENCH_DIR/run-shared-document-cache-board.sh" \
    "$BOARD:$REMOTE_ROOT/"
set +e
ssh "$BOARD" "cd $REMOTE_ROOT && timeout --signal=TERM --kill-after=30s 50000s bash ./run-shared-document-cache-board.sh > shared-document-driver.log 2>&1; rc=\$?; tail -n 25 shared-document-driver.log; exit \"\$rc\""
status=$?
set -e
scp "$BOARD:$REMOTE_ROOT/*-shared-document-*-rvv1.jsonl" \
    "$BOARD:$REMOTE_ROOT/*-shared-document-*-rvv1.log" \
    "$BOARD:$REMOTE_ROOT/shared-document-driver.log" \
    "$BOARD:$REMOTE_ROOT/shared-document-public-llamacpp.txt" "$ARCHIVE/" || true
exit "$status"
