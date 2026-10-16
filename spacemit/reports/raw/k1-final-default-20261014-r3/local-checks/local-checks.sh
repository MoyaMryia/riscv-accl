#!/usr/bin/env bash
set -u
cd /home/moyamryia/Projects/riscv-accl
python3 spacemit/bench/final-default/test_selection.py > lab/final-default-20261013/local-checks.log 2>&1
printf '%s\n' "$?" > lab/final-default-20261013/local-checks-exit-status
python3 -m py_compile spacemit/bench/final-default/*.py >> lab/final-default-20261013/local-checks.log 2>&1
printf '%s\n' "$?" > lab/final-default-20261013/syntax-exit-status
