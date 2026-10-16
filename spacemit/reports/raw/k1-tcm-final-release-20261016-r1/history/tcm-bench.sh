#!/usr/bin/env bash
# TCM staging availability probe + A/B benchmark on the SpacemiT X60 (IME1).
# Results and the activation story: OPTIMIZATION-REPORT.md §8.
#
# Prereqs:
#   * libspine_tcm.so in .toolchain/spine-tcm/ (extracted from spacemit-com/
#     spine-runtime release 0.6.0, asset spacemit-tcm_3.0.1_riscv64.deb)
#   * /dev/tcm accessible: kernel CONFIG_SPACEMIT_TCM probed
#     (/sys/bus/platform/drivers/tcm) and chmod 666 /dev/tcm (root; resets
#     on reboot — persist with a udev rule if desired)
set -euo pipefail
cd "$(dirname "$0")"
BB=./llama.cpp/build/bin/llama-bench
TCM=$PWD/.toolchain/spine-tcm
M=${1:-models/Qwen3.5-2B-Q4_0-embQ4_0.gguf}

echo "== /dev/tcm:"; ls -l /dev/tcm
echo "== TCM availability probe (16-token bench):"
LD_LIBRARY_PATH=$TCM:$PWD/llama.cpp/build/bin $BB -m "$M" -t 4 -p 0 -n 16 2>&1 \
    | grep -iE "tcm is available" || echo "TCM NOT active (check chmod /dev/tcm and LD_LIBRARY_PATH)"
echo "== baseline (no TCM lib):"
LD_LIBRARY_PATH=$PWD/llama.cpp/build/bin $BB -m "$M" -t 4 -p 0 -n 128 2>&1 | grep "tg128"
echo "== TCM staged:"
LD_LIBRARY_PATH=$TCM:$PWD/llama.cpp/build/bin $BB -m "$M" -t 4 -p 0 -n 128 2>&1 \
    | grep -E "tg128|tcm is available"
