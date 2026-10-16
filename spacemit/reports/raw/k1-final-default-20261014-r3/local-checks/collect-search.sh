#!/usr/bin/env bash
set -euo pipefail
cd /home/moyamryia/Projects/riscv-accl
rc_remote=/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1
rc_board=lab/final-default-20261013/board
mkdir -p "$rc_board"
scp -r "musepipro:$rc_remote/search-r2" "musepipro:$rc_remote/native-check" "$rc_board/"
scp "musepipro:$rc_remote/baseline-source-receipt.json" \
 "musepipro:$rc_remote/baseline-k1-source-receipt.json" \
 "musepipro:$rc_remote/baseline-load-source-receipt.json" \
 "musepipro:$rc_remote/baseline-k1-build-only.patch" \
 "musepipro:$rc_remote/baseline-load-compatibility.patch" \
 "musepipro:$rc_remote/baseline-build.log" \
 "musepipro:$rc_remote/baseline-build-exit-status" \
 "musepipro:$rc_remote/baseline-k1-build.log" \
 "musepipro:$rc_remote/baseline-k1-build-exit-status" \
 "musepipro:$rc_remote/baseline-load-build.log" \
 "musepipro:$rc_remote/baseline-load-build-exit-status" \
 "musepipro:$rc_remote/search-driver.log" \
 "musepipro:$rc_remote/search-exit-status" \
 "musepipro:$rc_remote/search-driver-r2.log" \
 "musepipro:$rc_remote/search-r2-exit-status" "$rc_board/"
mkdir -p "$rc_board/baseline-load-build"
scp "musepipro:$rc_remote/baseline-load-build/build-receipt.json" \
 "musepipro:$rc_remote/baseline-load-build/CMakeCache.txt" \
 "musepipro:$rc_remote/baseline-load-build/compile_commands.json" "$rc_board/baseline-load-build/"
