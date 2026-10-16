#!/usr/bin/env bash
set -euo pipefail
cd /home/moyamryia/Projects/riscv-accl
python3 lab/final-default-20261013/stage-final-evidence.py
python3 lab/final-default-20261013/delivery-r3/package/pack.py \
 --source lab/final-default-20261013/delivery-r3/source \
 --build lab/final-default-20261013/board/final-r3/build \
 --evidence lab/final-default-20261013/release-evidence --requirements Requirements.md \
 --report spacemit/reports/2026-10-14-final-default-comparison.md \
 --materials lab/integrated-20261013/model-materials \
 --reference lab/integrated-20261013/release/k1-unified-20261013-rc1/reference-release \
 --output lab/final-default-20261013/release
