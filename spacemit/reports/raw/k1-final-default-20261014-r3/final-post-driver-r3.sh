#!/usr/bin/env bash
set -euo pipefail
cd "$HOME/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1"
[[ $(cat final-r3-build-exit-status) == 0 ]]
rc_reference=$HOME/Projects/riscv-accl-bench-2026-09-27/k1-unified-20261013-rc1/build
rc_models=$HOME/Projects/spacemit-llama/models
rc_spert=$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2
rc_tcm=$HOME/Projects/llm-bench/.toolchain/spine-tcm
python3 comparison-tools-r3/validate_delivery.py --source final-r3/source --package final-r3/package \
 --build final-r3/build --reference "$rc_reference" --models "$rc_models" \
 --output final-validation-r3 --spert "$rc_spert" --tcm "$rc_tcm"
python3 comparison-tools-r3/experiment.py --stage compare --output comparison-r3 \
 --baseline baseline-load-build --candidate "$rc_reference" --final final-r3/build \
 --policy final-r3/package/default-policy.json --models "$rc_models" --spert "$rc_spert" --tcm "$rc_tcm"
