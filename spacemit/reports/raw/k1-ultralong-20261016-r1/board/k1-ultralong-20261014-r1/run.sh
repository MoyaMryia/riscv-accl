#!/usr/bin/env bash
set -euo pipefail
cd "$HOME/Projects/riscv-accl-bench-2026-09-27/k1-ultralong-20261014-r1"
python3 tools/long_context.py \
 --original "$HOME/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1" \
 --output results --models "$HOME/Projects/spacemit-llama/models" \
 --spert "$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2" \
 --tcm "$HOME/Projects/llm-bench/.toolchain/spine-tcm"
