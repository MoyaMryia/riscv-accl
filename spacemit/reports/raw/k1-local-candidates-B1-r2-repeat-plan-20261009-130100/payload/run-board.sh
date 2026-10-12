#!/usr/bin/env bash
set -uo pipefail
cd /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-local-candidates-B1-r2-repeat-20261009-130100
trap 'result=$?; printf "%s\n" "$result" > exit-status' EXIT
sha256sum -c payload-sha256.txt > payload-check.log 2>&1 || exit 1
timeout --signal=TERM --kill-after=30s 86400s python3 -u tool/spacemit/bench/local-candidates/repeat-b1.py /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-local-candidates-B1-r2-repeat-20261009-130100 /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-local-candidates-B1-r2-model-20261009-051000 /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-local-candidates-B1-r2-20261008-231500 > driver.log 2>&1
