#!/usr/bin/env bash
set -euo pipefail
cd /home/moyamryia/Projects/riscv-accl
rc_remote=/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1
ssh musepipro "test ! -e '$rc_remote' && mkdir '$rc_remote'"
scp lab/final-default-20261013/prepare-baseline.sh spacemit/release-candidate/with-lock.sh "musepipro:$rc_remote/"
ssh musepipro "cd '$rc_remote' && tmux new-session -d -s k1_final_baseline 'bash with-lock.sh bash prepare-baseline.sh > baseline-build.log 2>&1'"
