#!/usr/bin/env bash
set -euo pipefail
cd /home/moyamryia/Projects/riscv-accl
rc_work=lab/final-default-20261013
[[ $(cat "$rc_work/collect-search-exit-status") == 0 ]]
scp -r musepipro:/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1/tools-r2 "$rc_work/board/"
python3 spacemit/bench/final-default/verify_search.py --board "$rc_work/board" \
 --policy "$rc_work/delivery/package/default-policy.json" --output "$rc_work/search-verification.json"
