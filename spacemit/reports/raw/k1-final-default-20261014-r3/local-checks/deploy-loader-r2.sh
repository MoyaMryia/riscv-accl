#!/usr/bin/env bash
set -euo pipefail
cd /home/moyamryia/Projects/riscv-accl
rc_remote=/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1
scp lab/final-default-20261013/prepare-baseline-loader.py lab/final-default-20261013/build-baseline-loader.sh \
 lab/final-default-20261013/search-driver-r2.sh lab/final-default-20261013/search-wrapper-r2.sh "musepipro:$rc_remote/"
ssh musepipro "cd '$rc_remote' && test ! -e tools-r2 && cp -a tools tools-r2"
scp spacemit/bench/final-default/experiment.py spacemit/bench/final-default/effective.py \
 lab/final-default-20261013/PROTOCOL.md "musepipro:$rc_remote/tools-r2/"
ssh musepipro "cd '$rc_remote' && tmux new-session -d -s k1_final_baseline_loader 'bash with-lock.sh bash build-baseline-loader.sh > baseline-load-build.log 2>&1; printf \"%s\\n\" \"\$?\" > baseline-load-build-exit-status'"
ssh musepipro "cd '$rc_remote' && tmux new-session -d -s k1_final_search_r2 'bash search-wrapper-r2.sh'"
