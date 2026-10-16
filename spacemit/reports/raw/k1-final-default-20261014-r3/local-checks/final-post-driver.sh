#!/usr/bin/env bash
set -euo pipefail
cd "$HOME/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1"
[[ $(cat final-build-exit-status) == 0 ]]
rc_reference=$HOME/Projects/riscv-accl-bench-2026-09-27/k1-unified-20261013-rc1/build
rc_models=$HOME/Projects/spacemit-llama/models
rc_spert=$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2
rc_tcm=$HOME/Projects/llm-bench/.toolchain/spine-tcm
python3 comparison-tools/validate_delivery.py --source final/source --package final/package \
 --build final/build --reference "$rc_reference" --models "$rc_models" \
 --output final-validation --spert "$rc_spert" --tcm "$rc_tcm"
python3 comparison-tools/experiment.py --stage compare --output comparison \
 --baseline baseline-load-build --candidate "$rc_reference" --final final/build \
 --policy final/package/default-policy.json --models "$rc_models" --spert "$rc_spert" --tcm "$rc_tcm"
