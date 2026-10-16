#!/usr/bin/env bash
set -euo pipefail
cd /home/moyamryia/Projects/riscv-accl
[[ -n ${TMUX:-} ]]
rc_status=pending
for rc_wait in $(seq 1 120); do
 rc_status=$(ssh musepipro 'cd /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1 && if test -f final-post-r3-exit-status; then cat final-post-r3-exit-status; else printf pending; fi')
 [[ "$rc_status" == pending ]] || break
 sleep 30
done
[[ "$rc_status" == 0 ]] || { printf 'Final task status: %s\n' "$rc_status"; exit 1; }
bash lab/final-default-20261013/collect-final-r3.sh
python3 spacemit/bench/final-default/verify_final.py \
 --board lab/final-default-20261013/board \
 --delivery lab/final-default-20261013/delivery-r3 --version r3 \
 --output lab/final-default-20261013/final-verification.json
