#!/usr/bin/env bash
set -euo pipefail
cd /home/moyamryia/Projects/riscv-accl
rc_local=lab/final-default-20261013
rc_remote=/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1
[[ $(cat "$rc_local/preflight-r3-exit-status") == 0 ]]
ssh musepipro "cd '$rc_remote' && test ! -e final-r3 && test ! -e comparison-tools-r3"
mkdir "$rc_local/comparison-tools-r3"
cp spacemit/bench/final-default/*.py "$rc_local/comparison-tools-r3/"
cp "$rc_local"/lifecycle.py "$rc_local"/chat.py "$rc_local"/quality.py \
 "$rc_local"/2B-answer.json "$rc_local"/4B-answer.json "$rc_local"/PROTOCOL.md "$rc_local/comparison-tools-r3/"
scp -r "$rc_local/delivery-r3" "musepipro:$rc_remote/final-r3"
scp -r "$rc_local/comparison-tools-r3" "musepipro:$rc_remote/"
scp "$rc_local/build-final-r3.sh" "$rc_local/smoke-parser-r3.py" \
 "$rc_local/final-post-driver-r3.sh" "$rc_local/final-post-wrapper-r3.sh" "musepipro:$rc_remote/"
ssh musepipro "cd '$rc_remote' && tmux new-session -d -s k1_final_delivery_r3_build 'bash with-lock.sh bash build-final-r3.sh > final-r3-build.log 2>&1; printf \"%s\\n\" \"\$?\" > final-r3-build-exit-status'"
ssh musepipro "cd '$rc_remote' && tmux new-session -d -s k1_final_delivery_r3_post 'bash final-post-wrapper-r3.sh'"
