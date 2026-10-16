#!/usr/bin/env bash
set -euo pipefail
cd /home/moyamryia/Projects/riscv-accl
rc_work=lab/final-default-20261013
python3 spacemit/bench/final-default/build_default.py \
 --reference-package spacemit/release-candidate \
 --source lab/integrated-20261013/source \
 --vendor lab/local-reference/source-a990751-clean \
 --policy "$rc_work/selection/selected-default.json" \
 --output "$rc_work/delivery"
python3 "$rc_work/delivery/package/package.py" prepare \
 lab/local-reference/source-a990751-clean "$rc_work/delivery-replay"
g++ -std=c++17 -fsyntax-only \
 -I"$rc_work/delivery/source/include" -I"$rc_work/delivery/source/ggml/include" \
 "$rc_work/delivery/package/tests/test-default-state.cpp"
sha256sum "$rc_work/delivery/package/unified.patch" "$rc_work/delivery/package/default-policy.json"
