#!/usr/bin/env bash
set -euo pipefail
cd /home/moyamryia/Projects/riscv-accl
rc_remote=/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1
ssh musepipro "test ! -e '$rc_remote/search' && test ! -e '$rc_remote/native-check'"
scp spacemit/bench/final-default/experiment.py "musepipro:$rc_remote/tools/experiment.py"
