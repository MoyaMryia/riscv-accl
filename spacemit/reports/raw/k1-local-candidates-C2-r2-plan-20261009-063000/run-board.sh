#!/usr/bin/env bash
set -uo pipefail
cd /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-local-candidates-C2-r2-20261009-063000
trap 'result=$?; printf "%s\n" "$result" > exit-status' EXIT
sha256sum -c payload-sha256.txt > payload-check.log 2>&1 || exit 1
timeout --signal=TERM --kill-after=30s 86400s python3 -u tool/spacemit/bench/local-candidates/board-c2-r2.py /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-local-candidates-C2-r2-20261009-063000 C > driver.log 2>&1
