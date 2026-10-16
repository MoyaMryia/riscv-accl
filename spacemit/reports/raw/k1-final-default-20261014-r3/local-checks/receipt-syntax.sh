#!/usr/bin/env bash
set -u
cd /home/moyamryia/Projects/riscv-accl
python3 -m py_compile spacemit/bench/final-default/record_baseline.py > lab/final-default-20261013/receipt-syntax.log 2>&1
printf '%s\n' "$?" > lab/final-default-20261013/receipt-syntax-exit-status
bash -n lab/final-default-20261013/search-driver-r2.sh lab/final-default-20261013/update-baseline-receipt-step.sh >> lab/final-default-20261013/receipt-syntax.log 2>&1
printf '%s\n' "$?" > lab/final-default-20261013/receipt-shell-syntax-exit-status
