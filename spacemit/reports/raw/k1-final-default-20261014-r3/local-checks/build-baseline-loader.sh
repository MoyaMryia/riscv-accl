#!/usr/bin/env bash
set -euo pipefail
rc_root=$HOME/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1
cd "$rc_root"
[[ -n ${TMUX:-} && ${K1_PACKAGE_LOCK_FD:-} == 9 ]] || exit 2
[[ ! -e baseline-load-source && ! -e baseline-load-build ]] || exit 2
python3 prepare-baseline-loader.py
rc_cc=$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/gcc-14
rc_cxx=$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/g++-14
rc_spert=$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2
rc_tcm=$HOME/Projects/llm-bench/.toolchain/spine-tcm
export LD_LIBRARY_PATH="$rc_tcm:$rc_spert/lib"
unset LD_PRELOAD LD_AUDIT
cmake -S baseline-load-source -B baseline-load-build -G Ninja -DCMAKE_BUILD_TYPE=Release \
 -DCMAKE_C_COMPILER="$rc_cc" -DCMAKE_CXX_COMPILER="$rc_cxx" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
 -DCMAKE_BUILD_RPATH_USE_ORIGIN=ON '-DCMAKE_INSTALL_RPATH=$ORIGIN' \
 -DGGML_CPU_RISCV64_SPACEMIT=ON -DSPERT_DIR="$rc_spert" -DGGML_OPENMP=OFF \
 -DGGML_RV_ZBA=ON -DGGML_NATIVE=OFF -DGGML_CPU_REPACK=OFF -DLLAMA_BUILD_TESTS=OFF \
 -DLLAMA_OPENSSL=OFF -DLLAMA_CURL=OFF -DLLAMA_BUILD_UI=OFF -DLLAMA_USE_PREBUILT_UI=OFF
timeout --signal=TERM --kill-after=30s 14400s cmake --build baseline-load-build --target llama-server llama-bench -j4
