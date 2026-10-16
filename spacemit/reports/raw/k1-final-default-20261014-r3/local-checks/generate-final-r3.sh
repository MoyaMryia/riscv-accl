#!/usr/bin/env bash
set -euo pipefail
cd /home/moyamryia/Projects/riscv-accl
rc_work=lab/final-default-20261013
python3 "$rc_work/prepare-r3-policy.py"
python3 spacemit/bench/final-default/build_default.py \
 --reference-package spacemit/release-candidate \
 --source lab/integrated-20261013/source --vendor lab/local-reference/source-a990751-clean \
 --policy "$rc_work/selection/selected-default-r3.json" --output "$rc_work/delivery-r3"
python3 "$rc_work/delivery-r3/package/package.py" prepare \
 lab/local-reference/source-a990751-clean "$rc_work/delivery-r3-replay"
g++ -std=c++17 -fsyntax-only -I"$rc_work/delivery-r3/source/include" \
 -I"$rc_work/delivery-r3/source/ggml/include" -I"$rc_work/delivery-r3/source/common" \
 "$rc_work/delivery-r3/source/common/arg.cpp"
sha256sum "$rc_work/delivery-r3/package/unified.patch" "$rc_work/delivery-r3/package/default-policy.json"
