#!/usr/bin/env bash
set -uo pipefail
cd /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-local-candidates-C1-repeat-20261008-202900
timeout --signal=TERM --kill-after=30s 43200s python3 -u tool/spacemit/bench/local-candidates/repeat-c1.py /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-local-candidates-C1-repeat-20261008-202900 /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-local-candidates-20261008-184350 /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-local-candidates-C-repair2-20261008-190930 > driver.log 2>&1
result=$?
printf '%s\n' "$result" > exit-status
exit "$result"
