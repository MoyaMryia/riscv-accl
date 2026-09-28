#!/bin/bash
set -euo pipefail
while [ -d /proc/147968 ] && ! grep -q '^State:.*Z' /proc/147968/status; do sleep 20; done
BASE="$HOME/Projects/spacemit-llama-integrated"
WORKTREE="$HOME/Projects/spacemit-llama-window"
MODELS="$HOME/Projects/spacemit-llama/models"
if [ -e "$WORKTREE" ]; then
  echo "worktree path already exists: $WORKTREE" >&2
  exit 1
fi
git -C "$BASE" worktree add --detach "$WORKTREE" a990751
git -C "$WORKTREE" apply /tmp/windowed-mtp.patch
cmake -S "$WORKTREE" -B "$WORKTREE/build" -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER="$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/gcc-14" \
  -DCMAKE_CXX_COMPILER="$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/g++-14" \
  -DGGML_CPU_RISCV64_SPACEMIT=ON \
  -DSPERT_DIR="$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2" \
  -DGGML_OPENMP=OFF -DGGML_RV_ZBA=ON -DGGML_NATIVE=OFF \
  -DGGML_CPU_REPACK=OFF -DLLAMA_BUILD_TESTS=OFF \
  -DLLAMA_OPENSSL=OFF -DLLAMA_CURL=OFF \
  -DLLAMA_BUILD_UI=OFF -DLLAMA_USE_PREBUILT_UI=OFF
cmake --build "$WORKTREE/build" --target llama-server -j4
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$WORKTREE/build/bin"
for size in 2B 4B; do
  model="$MODELS/Qwen3.5-${size}-MTP-Q4_0-embQ4_0-dv64k.gguf"
  unset SPINE_MTP_WINDOW
  python3 /tmp/bench-lifecycle.py --server "$WORKTREE/build/bin/llama-server" --model "$model" \
    --label "${size}-full-mtp-short" --mode mtp --contexts 128 --n-predict 128 \
    --ctx-size 16384 --output /tmp/lifecycle-windowed.jsonl --log "/tmp/lifecycle-${size}-full-short.log"
  export SPINE_MTP_WINDOW=2048
  python3 /tmp/bench-lifecycle.py --server "$WORKTREE/build/bin/llama-server" --model "$model" \
    --label "${size}-window2k-short" --mode mtp --contexts 128 --n-predict 128 \
    --ctx-size 16384 --output /tmp/lifecycle-windowed.jsonl --log "/tmp/lifecycle-${size}-window-short.log"
  python3 /tmp/bench-lifecycle.py --server "$WORKTREE/build/bin/llama-server" --model "$model" \
    --label "${size}-window2k-12k" --mode mtp --contexts 12288 --n-predict 128 \
    --ctx-size 16384 --output /tmp/lifecycle-windowed.jsonl --log "/tmp/lifecycle-${size}-window-12k.log"
done
