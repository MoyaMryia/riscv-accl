#!/usr/bin/env bash
set -uo pipefail
cd /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-local-candidates-C2-repeat-20261008-215300
timeout --signal=TERM --kill-after=30s 86400s python3 -u tool/spacemit/bench/local-candidates/repeat-c.py /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-local-candidates-C2-repeat-20261008-215300 /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-local-candidates-20261008-184350 /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-local-candidates-C-repair2-20261008-190930 C2 > driver.log 2>&1
result=$?
printf '%s\n' "$result" > exit-status
exit "$result"
