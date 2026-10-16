#!/usr/bin/env bash
set -u
cd /home/moyamryia/Projects/riscv-accl
python3 spacemit/bench/final-default/test_delivery.py > lab/final-default-20261013/delivery-preflight.log 2>&1
printf '%s\n' "$?" > lab/final-default-20261013/delivery-preflight-exit-status
