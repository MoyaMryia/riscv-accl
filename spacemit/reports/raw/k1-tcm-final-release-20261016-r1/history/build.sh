#!/usr/bin/env bash
# Build llama.cpp for the SpacemiT K1-x / X60 (MUSE-Pi-Pro running Bianbu).
#
# Why this script exists:
#   * The system GCC 13.2 does NOT provide the RISC-V FP16 vector intrinsics
#     (vfloat16m1_t/vfloat16m2_t/...) that the SpaceMiT kernels require, so it
#     cannot compile GGML_CPU_RISCV64_SPACEMIT. GCC 14 is required.
#   * We have no root, so GCC 14 is fetched from the Bianbu apt repo and
#     extracted into ./.toolchain/gcc14 (no dpkg install needed).
#   * OpenMP is disabled: the extracted toolchain has no usable PIC libgomp.
#   * The prebuilt web-UI download is disabled: this box cannot reach
#     huggingface.co (hf-mirror does not proxy HF "buckets").
#
# Usage:  ./build.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
LLAMA="$ROOT/llama.cpp"
TOOLCHAIN="$ROOT/.toolchain/gcc14"
GCC_PKGS="cpp-14 cpp-14-riscv64-linux-gnu libitm1 liblsan0 libtsan2 \
libgcc-14-dev gcc-14-riscv64-linux-gnu libstdc++-14-dev \
g++-14-riscv64-linux-gnu gcc-14 g++-14"

# --- 1. local GCC 14 (skip if already present) -------------------------------
if [ ! -x "$TOOLCHAIN/usr/bin/gcc-14" ]; then
    echo ">> fetching GCC 14 from the Bianbu apt repo into $TOOLCHAIN"
    mkdir -p "$TOOLCHAIN" "$ROOT/.deb-cache"
    ( cd "$ROOT/.deb-cache" && apt-get download -q $GCC_PKGS )
    for d in "$ROOT"/.deb-cache/*.deb; do dpkg-deb -x "$d" "$TOOLCHAIN"; done
fi
export PATH="$TOOLCHAIN/usr/bin:$PATH"
gcc-14 --version | head -1

# --- 2. configure ------------------------------------------------------------
rm -rf "$LLAMA/build"
cmake -B "$LLAMA/build" -S "$LLAMA" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_C_COMPILER=gcc-14 -DCMAKE_CXX_COMPILER=g++-14 \
    -DGGML_NATIVE=OFF \
    -DGGML_CPU_RISCV64_SPACEMIT=ON \
    -DGGML_CPU_REPACK=OFF \
    -DGGML_OPENMP=OFF \
    -DGGML_RVV=ON -DGGML_RV_ZVFH=ON -DGGML_RV_ZFH=ON \
    -DGGML_RV_ZICBOP=ON -DGGML_RV_ZIHINTPAUSE=ON -DGGML_RV_ZBA=ON \
    -DLLAMA_CURL=OFF -DLLAMA_OPENSSL=OFF \
    -DLLAMA_USE_PREBUILT_UI=OFF \
    -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=ON \
    -DCMAKE_INSTALL_PREFIX="$LLAMA/build/installed"

# --- 3. build ----------------------------------------------------------------
# (llama-bench lives under examples/, so LLAMA_BUILD_EXAMPLES must be ON; only
#  the named targets are actually compiled.)
cmake --build "$LLAMA/build" -j"$(nproc)" --target llama-cli llama-server llama-bench
echo ">> done: $LLAMA/build/bin/{llama-cli,llama-server,llama-bench}"
