#!/usr/bin/env bash
set -euo pipefail
cd "$HOME/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1"
[[ $(cat final-r2-build-exit-status) == 0 ]]
rc_reference=$HOME/Projects/riscv-accl-bench-2026-09-27/k1-unified-20261013-rc1/build
rc_models=$HOME/Projects/spacemit-llama/models
rc_spert=$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2
rc_tcm=$HOME/Projects/llm-bench/.toolchain/spine-tcm
python3 comparison-tools-r2/validate_delivery.py --source final-r2/source --package final-r2/package \
 --build final-r2/build --reference "$rc_reference" --models "$rc_models" \
 --output final-validation-r2 --spert "$rc_spert" --tcm "$rc_tcm"
python3 comparison-tools-r2/experiment.py --stage compare --output comparison-r2 \
 --baseline baseline-load-build --candidate "$rc_reference" --final final-r2/build \
 --policy final-r2/package/default-policy.json --models "$rc_models" --spert "$rc_spert" --tcm "$rc_tcm"
