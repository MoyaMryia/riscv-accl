#!/usr/bin/env bash
# Blocking, bounded build of the pinned release on the K1 board.
set -euo pipefail
if [[ $# -ne 2 ]]; then echo 'usage: build.sh SOURCE BUILD_DIR' >&2; exit 2; fi
release_source=$(realpath "$1")
release_build=$(realpath -m "$2")
release_here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
python3 - "$release_source" "$release_here/manifest.json" <<'PY'
import hashlib,json,sys
from pathlib import Path
p=Path(sys.argv[1]); m=json.load(open(sys.argv[2]))
for n,h in m['patched_source_sha256'].items():
    if hashlib.sha256((p/n).read_bytes()).hexdigest()!=h: raise SystemExit('release source differs: '+n)
PY
release_cc=${K1_CC:-$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/gcc-14}
release_cxx=${K1_CXX:-$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/g++-14}
release_spert=${K1_SPERT_DIR:-$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2}
release_tcm=${K1_TCM_DIR:-$HOME/Projects/llm-bench/.toolchain/spine-tcm}
export LD_LIBRARY_PATH="$release_tcm:$release_spert/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
cmake -S "$release_source" -B "$release_build" -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER="$release_cc" -DCMAKE_CXX_COMPILER="$release_cxx" \
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DGGML_CPU_RISCV64_SPACEMIT=ON \
  -DSPERT_DIR="$release_spert" -DGGML_OPENMP=OFF -DGGML_RV_ZBA=ON \
  -DGGML_NATIVE=OFF -DGGML_CPU_REPACK=OFF -DLLAMA_BUILD_TESTS=OFF \
  -DLLAMA_OPENSSL=OFF -DLLAMA_CURL=OFF -DLLAMA_BUILD_UI=OFF -DLLAMA_USE_PREBUILT_UI=OFF
timeout --signal=TERM --kill-after=30s 14400s \
  cmake --build "$release_build" --target llama-server llama-bench -j4
