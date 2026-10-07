#!/usr/bin/env bash
set -u
cd /home/moyamryia/Projects/riscv-accl
timeout --signal=TERM --kill-after=30s 86400 python3 -u /home/moyamryia/Projects/riscv-accl/spacemit/reports/raw/local-reference-quality-20261006-194015/local-reference-quality.py /home/moyamryia/Projects/riscv-accl/spacemit/reports/raw/local-reference-quality-20261006-194015 > /home/moyamryia/Projects/riscv-accl/spacemit/reports/raw/local-reference-quality-20261006-194015/runner.log 2>&1
code=$?
printf "%s\n" "$code" > /home/moyamryia/Projects/riscv-accl/spacemit/reports/raw/local-reference-quality-20261006-194015/exit-status
exit "$code"
