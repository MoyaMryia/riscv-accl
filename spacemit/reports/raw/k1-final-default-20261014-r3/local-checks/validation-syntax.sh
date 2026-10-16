#!/usr/bin/env bash
set -u
cd /home/moyamryia/Projects/riscv-accl
python3 -m py_compile spacemit/bench/final-default/validate_delivery.py > lab/final-default-20261013/validation-syntax.log 2>&1
printf '%s\n' "$?" > lab/final-default-20261013/validation-syntax-exit-status
