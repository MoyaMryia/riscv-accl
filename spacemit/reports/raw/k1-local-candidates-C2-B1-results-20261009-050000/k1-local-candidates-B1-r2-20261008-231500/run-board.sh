#!/usr/bin/env bash
set -uo pipefail
cd /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-local-candidates-B1-r2-20261008-231500
timeout --signal=TERM --kill-after=30s 86400s python3 -u tool/spacemit/bench/local-candidates/board-b1-r2.py /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-local-candidates-B1-r2-20261008-231500 B1 > driver.log 2>&1
result=$?
printf '%s\n' "$result" > exit-status
exit "$result"
