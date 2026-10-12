#!/usr/bin/env bash
# 在新目录串行执行固定组合协议。
set -euo pipefail
root=$(realpath "$1")
test ! -e "$root/driver.log"
exec >"$root/driver.log" 2>&1
trap 'result=$?; date -Is >"$root/end-clock.log"; printf "%s\n" "$result" >"$root/exit-status"' EXIT
date -Is >"$root/start-clock.log"
cd "$root"
timeout --signal=TERM --kill-after=30s 86400s python3 -u \
    tool/spacemit/bench/local-candidates/board-combined.py "$root" C
