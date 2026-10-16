#!/usr/bin/env bash
# 从统一源码构建服务器、基准工具与数值检查工具。
set -euo pipefail
[[ $# == 2 ]] || { echo 'usage: build.sh SOURCE BUILD_DIR' >&2; exit 2; }
[[ -n ${TMUX:-} && ${K1_PACKAGE_LOCK_FD:-} == 9 && -e /proc/$$/fd/9 ]] || { echo 'Use with-lock.sh in tmux.' >&2; exit 2; }
pkg_here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
pkg_source=$(realpath "$1")
pkg_build=$(realpath -m "$2")
[[ ! -e "$pkg_build" ]] || { echo 'Build directory exists.' >&2; exit 2; }
python3 "$pkg_here/package.py" verify "$pkg_source"
pkg_cc=${K1_CC:-$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/gcc-14}
pkg_cxx=${K1_CXX:-$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/g++-14}
pkg_spert=${K1_SPERT_DIR:-$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2}
pkg_tcm=${K1_TCM_DIR:-$HOME/Projects/llm-bench/.toolchain/spine-tcm}
export LD_LIBRARY_PATH="$pkg_tcm:$pkg_spert/lib"
unset LD_PRELOAD LD_AUDIT
cmake -S "$pkg_source" -B "$pkg_build" -G Ninja -DCMAKE_BUILD_TYPE=Release \
 -DCMAKE_C_COMPILER="$pkg_cc" -DCMAKE_CXX_COMPILER="$pkg_cxx" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
 -DCMAKE_BUILD_RPATH_USE_ORIGIN=ON '-DCMAKE_INSTALL_RPATH=$ORIGIN' \
 -DGGML_CPU_RISCV64_SPACEMIT=ON -DSPERT_DIR="$pkg_spert" -DGGML_OPENMP=OFF \
 -DGGML_RV_ZBA=ON -DGGML_NATIVE=OFF -DGGML_CPU_REPACK=OFF -DLLAMA_BUILD_TESTS=OFF \
 -DLLAMA_OPENSSL=OFF -DLLAMA_CURL=OFF -DLLAMA_BUILD_UI=OFF -DLLAMA_USE_PREBUILT_UI=OFF
timeout --signal=TERM --kill-after=30s 14400s cmake --build "$pkg_build" --target llama-server llama-bench -j4
export LD_LIBRARY_PATH="$pkg_build/bin:$pkg_tcm:$pkg_spert/lib"
for pkg_probe in attention ssm gdn state route default-state; do
 "$pkg_cxx" -O3 -std=c++17 -DSPINE_K1_BOARD -march=rv64gcv_zfh_zvfh_zicbop_zihintpause_zba -mabi=lp64d \
  "-I$pkg_source/include" "-I$pkg_source/ggml/include" "-I$pkg_source/ggml/src" \
  "-I$pkg_source/ggml/src/ggml-cpu" "-I$pkg_source/ggml/src/ggml-cpu/spacemit" "-I$pkg_source/src/models" \
  "$pkg_here/tests/test-$pkg_probe.cpp" "-L$pkg_build/bin" '-Wl,-rpath,$ORIGIN' \
  -lllama -lggml -lggml-cpu -lggml-base -pthread -o "$pkg_build/bin/test-$pkg_probe"
done
python3 "$pkg_here/record-build.py" "$pkg_source" "$pkg_build" "$pkg_cc" "$pkg_cxx" "$pkg_spert" "$pkg_tcm"
