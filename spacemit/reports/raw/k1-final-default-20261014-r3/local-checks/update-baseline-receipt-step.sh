#!/usr/bin/env bash
set -euo pipefail
cd /home/moyamryia/Projects/riscv-accl
rc_remote=/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1
ssh musepipro "cd '$rc_remote' && test ! -e baseline-load-build-exit-status && test ! -e search-r2 && test ! -e search-driver-r2.log"
scp spacemit/bench/final-default/record_baseline.py lab/final-default-20261013/search-driver-r2.sh "musepipro:$rc_remote/"
