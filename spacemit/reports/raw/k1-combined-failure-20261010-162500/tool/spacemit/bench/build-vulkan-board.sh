#!/usr/bin/env bash
# Build an isolated Vulkan-enabled SpacemiT llama.cpp server on MUSE-Pi-Pro.
set -euo pipefail

BASE="$HOME/Projects/spacemit-llama-integrated"
WORKTREE="$HOME/Projects/spacemit-llama-vulkan"
TOOLCHAIN="$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin"
SPERT="$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2"

if [ -e "$WORKTREE" ]; then
  echo "existing worktree: $WORKTREE" >&2
  exit 1
fi
if pgrep -x llama-server >/dev/null; then
  echo 'another llama-server is running' >&2
  exit 1
fi
command -v glslc >/dev/null
test -f /usr/include/vulkan/vulkan.h
git -C "$BASE" worktree add --detach "$WORKTREE" a990751

cmake -S "$WORKTREE" -B "$WORKTREE/build" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER="$TOOLCHAIN/gcc-14" \
  -DCMAKE_CXX_COMPILER="$TOOLCHAIN/g++-14" \
  -DGGML_CPU_RISCV64_SPACEMIT=ON -DSPERT_DIR="$SPERT" \
  -DGGML_VULKAN=ON -DGGML_OPENMP=OFF -DGGML_RV_ZBA=ON \
  -DGGML_NATIVE=OFF -DGGML_CPU_REPACK=OFF -DLLAMA_BUILD_TESTS=OFF \
  -DLLAMA_OPENSSL=OFF -DLLAMA_CURL=OFF \
  -DLLAMA_BUILD_UI=OFF -DLLAMA_USE_PREBUILT_UI=OFF
timeout --signal=TERM --kill-after=20s 7200s \
  cmake --build "$WORKTREE/build" --target llama-server -j4
test -x "$WORKTREE/build/bin/llama-server"
echo "PASS: isolated Vulkan server built at $WORKTREE/build/bin/llama-server"
