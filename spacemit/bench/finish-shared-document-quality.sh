#!/usr/bin/env bash
# Collect a completed tmux run, build judge input, POST to MiMo, and print marks.
set -euo pipefail
REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
BENCH_DIR="$REPO_ROOT/spacemit/bench"
ARCHIVE="$REPO_ROOT/spacemit/reports/raw/2026-09-25-lifecycle"
BOARD=${BOARD:-musepipro-wg}
REMOTE_ROOT='~/Projects/riscv-accl-bench-2026-09-27'
label=2B-shared-document-16384-quality256-rvv1
if ! ssh "$BOARD" "test -f $REMOTE_ROOT/quality256-exit-status"; then
  echo 'Quality run is still running in tmux; wait and run this again.' >&2
  exit 3
fi
status=$(ssh "$BOARD" "cat $REMOTE_ROOT/quality256-exit-status")
scp "$BOARD:$REMOTE_ROOT/quality256-driver.log" "$ARCHIVE/"
if [ "$status" != 0 ]; then
  echo "Board quality run failed (exit $status); see $ARCHIVE/quality256-driver.log" >&2
  exit 1
fi
scp "$BOARD:$REMOTE_ROOT/$label.jsonl" "$BOARD:$REMOTE_ROOT/$label.log" "$ARCHIVE/"
input="$ARCHIVE/$label-judge-input.json"
output="$ARCHIVE/$label-mimo-v26-judge.jsonl"
if [ ! -e "$input" ]; then
  python3 "$BENCH_DIR/recover-shared-document-answers.py" \
    --record "$ARCHIVE/$label.jsonl" \
    --document "$ARCHIVE/shared-document-public-llamacpp.txt" \
    --output "$input"
fi
if [ -e "$output" ]; then
  echo "Existing judge result: $output"
else
  python3 "$BENCH_DIR/judge-shared-document-cache.py" --input "$input" --output "$output"
fi
