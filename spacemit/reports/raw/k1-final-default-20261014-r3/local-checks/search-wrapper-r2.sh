#!/usr/bin/env bash
set -u
cd "$HOME/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1"
for rc_wait in $(seq 1 1500); do
 [[ ! -f baseline-load-build-exit-status ]] || break
 sleep 10
done
bash with-lock.sh bash search-driver-r2.sh > search-driver-r2.log 2>&1
printf '%s\n' "$?" > search-r2-exit-status
