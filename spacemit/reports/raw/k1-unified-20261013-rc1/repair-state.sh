#!/usr/bin/env bash
set -euo pipefail
rc_root=$HOME/Projects/riscv-accl-bench-2026-09-27/k1-unified-20261013-rc1
cd "$rc_root"
mkdir attempt1-build-receipt
cp build/build-receipt.json attempt1-build-receipt/
cp build/bin/test-state attempt1-build-receipt/
mv validation validation-attempt1
mv validation-driver.log validation-attempt1-driver.log
mv validation-exit-status validation-attempt1-exit-status
rc_cxx=$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/g++-14
rc_cc=$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/gcc-14
rc_spert=$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2
rc_tcm=$HOME/Projects/llm-bench/.toolchain/spine-tcm
export LD_LIBRARY_PATH="$rc_root/build/bin:$rc_tcm:$rc_spert/lib"
"$rc_cxx" -O3 -std=c++17 -DSPINE_K1_BOARD -march=rv64gcv_zfh_zvfh_zicbop_zihintpause_zba -mabi=lp64d -Isource/include -Isource/ggml/include -Isource/ggml/src -Isource/ggml/src/ggml-cpu -Isource/ggml/src/ggml-cpu/spacemit -Isource/src/models package/tests/test-state.cpp -Lbuild/bin '-Wl,-rpath,$ORIGIN' -lllama -lggml -lggml-cpu -lggml-base -pthread -o build/bin/test-state
python3 package/record-build.py source build "$rc_cc" "$rc_cxx" "$rc_spert" "$rc_tcm" > repair-state-build.log
set +e
python3 package/validate.py --source source --build build --reference "$HOME/Projects/riscv-accl-bench-2026-09-27/k1-release-check-20261007-125712/build/bin" --models "$HOME/Projects/spacemit-llama/models" --output validation > validation-driver.log 2>&1
printf '%s\n' "$?" > validation-exit-status
