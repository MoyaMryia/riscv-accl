#!/bin/bash
set -uo pipefail
while [ -d /proc/185452 ] && ! grep -q '^State:.*Z' /proc/185452/status; do sleep 20; done
BASE="$HOME/Projects/spacemit-llama-integrated"
WORKTREE="$HOME/Projects/spacemit-llama-page-gather"
MODELS="$HOME/Projects/spacemit-llama/models"
if [ -e "$WORKTREE" ]; then
  echo "worktree already exists: $WORKTREE" >&2
  exit 1
fi
if ! git -C "$BASE" worktree add --detach "$WORKTREE" a990751; then exit 1; fi
if ! git -C "$WORKTREE" apply /tmp/2026-09-26-page-gather.patch; then exit 1; fi
CC14="$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/gcc-14"
CXX14="$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/g++-14"
if ! cmake -S "$WORKTREE" -B "$WORKTREE/build" -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER="$CC14" -DCMAKE_CXX_COMPILER="$CXX14" \
  -DGGML_CPU_RISCV64_SPACEMIT=ON \
  -DSPERT_DIR="$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2" \
  -DGGML_OPENMP=OFF -DGGML_RV_ZBA=ON -DGGML_NATIVE=OFF \
  -DGGML_CPU_REPACK=OFF -DLLAMA_BUILD_TESTS=OFF \
  -DLLAMA_OPENSSL=OFF -DLLAMA_CURL=OFF \
  -DLLAMA_BUILD_UI=OFF -DLLAMA_USE_PREBUILT_UI=OFF; then exit 1; fi
if ! cmake --build "$WORKTREE/build" --target llama-server -j4; then exit 1; fi
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$WORKTREE/build/bin"
if ! "$CXX14" -std=c++17 -O2 /tmp/2026-09-26-page-gather-test.cpp \
  -I"$WORKTREE/src" -I"$WORKTREE/ggml/include" -L"$WORKTREE/build/bin" \
  -lggml-cpu -lggml-base -lggml -o /tmp/test-page-gather-board; then exit 1; fi
if ! /tmp/test-page-gather-board; then exit 1; fi
for size in 2B 4B; do
  for mode in off on; do
    unset SPINE_KV_PAGE_GATHER
    if [ "$mode" = on ]; then export SPINE_KV_PAGE_GATHER=1; fi
    label="${size}-page-gather-smoke-${mode}"
    python3 /tmp/bench-lifecycle.py --server "$WORKTREE/build/bin/llama-server" \
      --model "$MODELS/Qwen3.5-${size}-MTP-Q4_0-embQ4_0-dv64k.gguf" \
      --label "$label" --mode plain --contexts 128 --n-predict 32 --ctx-size 4096 --kv-unified \
      --output /tmp/lifecycle-page-gather-smoke.jsonl --log "/tmp/lifecycle-${label}.log" || exit 1
  done
done
if ! python3 /tmp/audit-lifecycle.py /tmp/lifecycle-page-gather-smoke.jsonl \
  --require-identical --require-token-ids --min-runs-per-group 2; then exit 1; fi
for size in 2B 4B; do
  arm=0
  for mode in off on on off; do
    arm=$((arm + 1))
    unset SPINE_KV_PAGE_GATHER
    if [ "$mode" = on ]; then export SPINE_KV_PAGE_GATHER=1; fi
    label="${size}-page-gather-${mode}-pass${arm}"
    echo "START $label"
    python3 /tmp/bench-lifecycle.py --server "$WORKTREE/build/bin/llama-server" \
      --model "$MODELS/Qwen3.5-${size}-MTP-Q4_0-embQ4_0-dv64k.gguf" \
      --label "$label" --mode plain --contexts 128 --slot-contexts 128 256 512 1024 \
      --rotate-slot-contexts --repeats 2 --parallel 4 --concurrency 4 --kv-unified \
      --n-predict 32 --ctx-size 8192 --output /tmp/lifecycle-page-gather.jsonl \
      --log "/tmp/lifecycle-${label}.log" || exit 1
  done
done
python3 /tmp/audit-lifecycle.py /tmp/lifecycle-page-gather.jsonl \
  --require-identical --require-token-ids --min-runs-per-group 8
