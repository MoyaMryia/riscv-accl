#!/usr/bin/env bash
set -u
cd "$HOME/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1"
for rc_wait in $(seq 1 1500); do
 [[ ! -f final-build-exit-status ]] || break
 sleep 10
done
bash with-lock.sh bash final-post-driver.sh > final-post.log 2>&1
printf '%s\n' "$?" > final-post-exit-status
