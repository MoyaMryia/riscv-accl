#!/usr/bin/env bash
set -euo pipefail
rc_root=$HOME/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1
cd "$rc_root"
[[ $(cat baseline-k1-build-exit-status) == 0 ]]
python3 native-check.py > native-driver.log 2>&1
python3 tools/experiment.py --stage search --output search \
 --baseline baseline-k1-build \
 --candidate "$HOME/Projects/riscv-accl-bench-2026-09-27/k1-unified-20261013-rc1/build" \
 --models "$HOME/Projects/spacemit-llama/models" \
 --spert "$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2" \
 --tcm "$HOME/Projects/llm-bench/.toolchain/spine-tcm"
