#!/usr/bin/env bash
set -uo pipefail
cd /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-local-candidates-C2-r2-model-20261009-130700
trap 'result=$?; printf "%s\n" "$result" > exit-status' EXIT
sha256sum -c payload-sha256.txt > payload-check.log 2>&1 || exit 1
timeout --signal=TERM --kill-after=30s 86400s python3 -u tool/spacemit/bench/local-candidates/model-c2-r2.py /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-local-candidates-C2-r2-model-20261009-130700 /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-local-candidates-C2-r2-20261009-063000 > driver.log 2>&1
