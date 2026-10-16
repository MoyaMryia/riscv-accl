#!/usr/bin/env bash
set -euo pipefail
cd /home/moyamryia/Projects/riscv-accl
rc_local=lab/final-default-20261013
rc_remote=/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1
[[ $(cat "$rc_local/generate-final-exit-status") == 0 ]]
ssh musepipro "cd '$rc_remote' && test \"\$(cat search-r2-exit-status)\" = 0 && test ! -e final && test ! -e comparison-tools"
mkdir "$rc_local/comparison-tools"
cp spacemit/bench/final-default/*.py "$rc_local/comparison-tools/"
cp "$rc_local"/lifecycle.py "$rc_local"/chat.py "$rc_local"/quality.py \
 "$rc_local"/2B-answer.json "$rc_local"/4B-answer.json "$rc_local"/PROTOCOL.md "$rc_local/comparison-tools/"
scp -r "$rc_local/delivery" "musepipro:$rc_remote/final"
scp -r "$rc_local/comparison-tools" "musepipro:$rc_remote/"
scp "$rc_local/build-final.sh" "$rc_local/final-post-driver.sh" "$rc_local/final-post-wrapper.sh" "musepipro:$rc_remote/"
ssh musepipro "cd '$rc_remote' && tmux new-session -d -s k1_final_delivery_build 'bash with-lock.sh bash build-final.sh > final-build.log 2>&1; printf \"%s\\n\" \"\$?\" > final-build-exit-status'"
ssh musepipro "cd '$rc_remote' && tmux new-session -d -s k1_final_delivery_post 'bash final-post-wrapper.sh'"
