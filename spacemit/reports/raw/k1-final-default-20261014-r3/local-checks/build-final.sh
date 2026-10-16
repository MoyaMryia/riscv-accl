#!/usr/bin/env bash
set -euo pipefail
cd "$HOME/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1"
[[ $(cat search-r2-exit-status) == 0 ]]
cmp search-r2/selected-default.json final/package/default-policy.json
bash final/package/build.sh final/source final/build
