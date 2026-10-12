#!/usr/bin/env bash
set -uo pipefail
cd /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-local-candidates-C-models-20261008-185800
timeout --signal=TERM --kill-after=30s 21600s python3 -u tool/spacemit/bench/local-candidates/model-c.py /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-local-candidates-C-models-20261008-185800 /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-local-candidates-20261008-184350 > driver.log 2>&1
result=$?
printf '%s\n' "$result" > exit-status
exit "$result"
