#!/bin/bash
set -uo pipefail
while [ -d /proc/186804 ] && ! grep -q '^State:.*Z' /proc/186804/status; do sleep 20; done
BASE="$HOME/Projects/spacemit-llama-integrated"
WORKTREE="$HOME/Projects/spacemit-llama-rvv32"
MODELS="$HOME/Projects/spacemit-llama/models"
if [ -e "$WORKTREE" ]; then echo "worktree already exists: $WORKTREE" >&2; exit 1; fi
if ! git -C "$BASE" worktree add --detach "$WORKTREE" a990751; then exit 1; fi
if ! git -C "$WORKTREE" apply /tmp/2026-09-26-wide-rvv-vlen256.patch; then exit 1; fi
if ! cmake -S "$WORKTREE" -B "$WORKTREE/build" -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER="$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/gcc-14" \
  -DCMAKE_CXX_COMPILER="$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/g++-14" \
  -DGGML_CPU_RISCV64_SPACEMIT=ON \
  -DSPERT_DIR="$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2" \
  -DGGML_OPENMP=OFF -DGGML_RV_ZBA=ON -DGGML_NATIVE=OFF \
  -DGGML_CPU_REPACK=OFF -DLLAMA_BUILD_TESTS=OFF \
  -DLLAMA_OPENSSL=OFF -DLLAMA_CURL=OFF \
  -DLLAMA_BUILD_UI=OFF -DLLAMA_USE_PREBUILT_UI=OFF; then exit 1; fi
if ! cmake --build "$WORKTREE/build" --target llama-server -j4; then exit 1; fi
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$WORKTREE/build/bin"
for size in 2B 4B; do
  pass=0
  for enabled in 0 1 1 0; do
    pass=$((pass+1))
    export SPINE_FA_WIDE_TILE="$enabled"
    label="${size}-rvv32-${enabled}-pass${pass}"
    echo "START $label"
    python3 /tmp/bench-lifecycle.py --server "$WORKTREE/build/bin/llama-server" \
      --model "$MODELS/Qwen3.5-${size}-MTP-Q4_0-embQ4_0-dv64k.gguf" \
      --label "$label" --mode plain --contexts 128 2048 --n-predict 32 \
      --ctx-size 4096 --output /tmp/lifecycle-rvv32.jsonl \
      --log "/tmp/lifecycle-${label}.log" || exit 1
  done
done
python3 /tmp/audit-lifecycle.py /tmp/lifecycle-rvv32.jsonl \
  --require-identical --require-token-ids --min-runs-per-group 4 || exit 1
python3 - <<'PY'
from pathlib import Path
marker='SPINE_FA_WIDE_TILE: RVV tiled attention enabled for 256-dim heads'
for size in ('2B','4B'):
    for arm in (2,3):
        path=Path(f'/tmp/lifecycle-{size}-rvv32-1-pass{arm}.log')
        if marker not in path.read_text(errors='replace'):
            raise SystemExit(f'wide RVV kernel did not activate: {path}')
print('PASS: all enabled arms activated the 256-head kernel')
PY
