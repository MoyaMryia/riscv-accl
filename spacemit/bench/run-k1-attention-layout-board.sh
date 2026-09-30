#!/usr/bin/env bash
set -euo pipefail
RUN_ROOT=$1
exec > "$RUN_ROOT/driver.log" 2>&1
trap 'status=$?; printf "%s\n" "$status" > "$RUN_ROOT/exit-status"' EXIT
printf 'waiting for document quality benchmark\n' > "$RUN_ROOT/phase"
exec 9> "$HOME/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock"
flock -w 43200 9
if pgrep -x llama-server >/dev/null; then
  echo 'another llama-server is active; stopping before building' >&2
  exit 1
fi
BASE="$HOME/Projects/spacemit-llama-integrated"
WORKTREE="$RUN_ROOT/source"
MODEL_ROOT="$HOME/Projects/spacemit-llama/models"
printf 'building isolated layout experiment\n' > "$RUN_ROOT/phase"
git -C "$BASE" worktree add --detach "$WORKTREE" a990751
python3 - "$RUN_ROOT" "$WORKTREE" <<'PY'
import hashlib, json, shutil, sys
from pathlib import Path
root, worktree = map(Path, sys.argv[1:])
manifest = json.loads((root/'source-manifest.json').read_text())
for path in manifest['modified_paths']:
    source = root/'baseline'/Path(path).name
    if hashlib.sha256(source.read_bytes()).hexdigest() != manifest['source_sha256'][path]:
        raise SystemExit(f'baseline source hash mismatch: {path}')
    shutil.copyfile(source, worktree/path)
PY
git -C "$WORKTREE" apply --check "$RUN_ROOT/layout.patch"
git -C "$WORKTREE" apply "$RUN_ROOT/layout.patch"
CXX="$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/g++-14"
SPERT_DIR="$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2"
cmake -S "$WORKTREE" -B "$WORKTREE/build" -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER="$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/gcc-14" \
  -DCMAKE_CXX_COMPILER="$CXX" -DGGML_CPU_RISCV64_SPACEMIT=ON -DSPERT_DIR="$SPERT_DIR" \
  -DGGML_OPENMP=OFF -DGGML_RV_ZBA=ON -DGGML_NATIVE=OFF -DGGML_CPU_REPACK=OFF \
  -DLLAMA_BUILD_TESTS=OFF -DLLAMA_OPENSSL=OFF -DLLAMA_CURL=OFF \
  -DLLAMA_BUILD_UI=OFF -DLLAMA_USE_PREBUILT_UI=OFF > "$RUN_ROOT/configure.log" 2>&1
cmake --build "$WORKTREE/build" --target llama-server -j4 > "$RUN_ROOT/build.log" 2>&1
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$SPERT_DIR/lib:$WORKTREE/build/bin"
export SPINE_FA_WIDE_TILE=1
unset SPINE_MTP_WINDOW SPINE_SPEC_RS SPINE_KV_PAGE_GATHER
"$CXX" -O3 -std=c++17 -march=rv64gcv_zfh_zvfh_zicbop_zihintpause_zba -mabi=lp64d \
  -I"$WORKTREE/ggml/include" -I"$WORKTREE/ggml/src" -I"$WORKTREE/ggml/src/ggml-cpu" \
  "$RUN_ROOT/test-k1-attention-layout.cpp" -L"$WORKTREE/build/bin" \
  -lggml-cpu -lggml-base -pthread -o "$RUN_ROOT/test-layout" > "$RUN_ROOT/test-build.log" 2>&1
printf 'checking numerical outputs and scratch guards\n' > "$RUN_ROOT/phase"
for rows in 0 16 32; do
  SPINE_FA_K1_LAYOUT=$rows timeout --kill-after=30s 600s \
    "$RUN_ROOT/test-layout" "$RUN_ROOT/layout-$rows.bin" > "$RUN_ROOT/numeric-$rows.log" 2>&1
done
cmp "$RUN_ROOT/layout-0.bin" "$RUN_ROOT/layout-16.bin"
cmp "$RUN_ROOT/layout-0.bin" "$RUN_ROOT/layout-32.bin"
printf 'PASS: both layouts match baseline float outputs bit for bit\n' > "$RUN_ROOT/numeric-status"
printf 'running 2B and 4B short comparisons\n' > "$RUN_ROOT/phase"
for model in 2B 4B; do
  pass=0
  for rows in 0 16 32 32 16 0; do
    pass=$((pass+1))
    label="$model-layout-$rows-pass$pass"
    export SPINE_FA_K1_LAYOUT=$rows
    timeout --kill-after=30s 3600s python3 "$RUN_ROOT/bench-lifecycle.py" \
      --server "$WORKTREE/build/bin/llama-server" \
      --model "$MODEL_ROOT/Qwen3.5-$model-MTP-Q4_0-embQ4_0-dv64k.gguf" \
      --label "$label" --mode plain --contexts 128 2048 --n-predict 32 --ignore-eos \
      --capture-token-ids --ctx-size 4096 --timeout 1800 \
      --output "$RUN_ROOT/results.jsonl" --log "$RUN_ROOT/$label.log"
  done
done
python3 "$RUN_ROOT/audit-lifecycle.py" "$RUN_ROOT/results.jsonl" \
  --require-identical --require-token-ids --min-runs-per-group 6 > "$RUN_ROOT/audit.log" 2>&1
python3 "$RUN_ROOT/summarize-k1-attention-layout.py" "$RUN_ROOT"
printf 'complete; long-context validation remains separate\n' > "$RUN_ROOT/phase"
