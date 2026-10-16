#!/usr/bin/env bash
set -euo pipefail
cd /home/moyamryia/Projects/riscv-accl
rc_remote=/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1
scp lab/final-default-20261013/build-baseline-compatible.sh "musepipro:$rc_remote/"
ssh musepipro "cd '$rc_remote' && tmux new-session -d -s k1_final_baseline_compat 'bash with-lock.sh bash build-baseline-compatible.sh > baseline-k1-build.log 2>&1'"
