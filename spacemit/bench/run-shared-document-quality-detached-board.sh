#!/usr/bin/env bash
set -uo pipefail
BENCH_ROOT=${BENCH_ROOT:-"$HOME/Projects/riscv-accl-bench-2026-09-27"}
cd "$BENCH_ROOT" || exit 1
bash ./run-shared-document-quality-board.sh > quality256-driver.log 2>&1
status=$?
printf '%s\n' "$status" > quality256-exit-status
exit "$status"
