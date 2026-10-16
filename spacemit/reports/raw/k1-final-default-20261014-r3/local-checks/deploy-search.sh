#!/usr/bin/env bash
set -euo pipefail
cd /home/moyamryia/Projects/riscv-accl
rc_local=lab/final-default-20261013
rc_remote=/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1
mkdir -p "$rc_local/tools"
cp spacemit/bench/final-default/*.py "$rc_local/tools/"
cp "$rc_local"/lifecycle.py "$rc_local"/chat.py "$rc_local"/quality.py "$rc_local"/2B-answer.json "$rc_local"/4B-answer.json "$rc_local"/test-state-all-masks.cpp "$rc_local"/PROTOCOL.md "$rc_local/tools/"
scp -r "$rc_local/tools" "musepipro:$rc_remote/"
scp "$rc_local/native-check.py" "$rc_local/search-driver.sh" "$rc_local/search-wrapper.sh" "musepipro:$rc_remote/"
ssh musepipro "cd '$rc_remote' && tmux new-session -d -s k1_final_search 'bash search-wrapper.sh'"
