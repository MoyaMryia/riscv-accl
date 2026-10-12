#!/usr/bin/env bash
# Compile one fixed candidate on K1.
set -euo pipefail
if [[ $# -ne 2 ]]; then
    echo 'usage: build-k1.sh CANDIDATE_ROOT BUILD_DIR' >&2
    exit 2
fi
candidate_root=$(realpath "$1")
candidate_build=$(realpath -m "$2")
candidate_here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
candidate_source="$candidate_root/source"
python3 - "$candidate_source" "$candidate_root/manifest.json" "$candidate_here" <<'PY'
import hashlib
import json
from pathlib import Path
import sys
source, manifest_path, here = map(Path, sys.argv[1:])
manifest = json.loads(manifest_path.read_text())
snapshot = here.parents[2]/'spacemit/reports/raw/local-reference-quality-20261006-194015/source-verification.json'
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
if digest(snapshot) != manifest['snapshot_manifest_sha256']:
    raise SystemExit('snapshot receipt differs')
files = json.loads(snapshot.read_text())['files_sha256']
files.update(manifest['files_sha256'])
for relative, expected in files.items():
    if digest(source/relative) != expected:
        raise SystemExit('candidate source differs: '+relative)
print('PASS: fixed candidate source')
PY
candidate_cc=${K1_CC:-$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/gcc-14}
candidate_cxx=${K1_CXX:-$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/g++-14}
candidate_spert=${K1_SPERT_DIR:-$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2}
candidate_tcm=${K1_TCM_DIR:-$HOME/Projects/llm-bench/.toolchain/spine-tcm}
export LD_LIBRARY_PATH="$candidate_tcm:$candidate_spert/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
cmake -S "$candidate_source" -B "$candidate_build" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER="$candidate_cc" \
  -DCMAKE_CXX_COMPILER="$candidate_cxx" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
  -DGGML_CPU_RISCV64_SPACEMIT=ON -DSPERT_DIR="$candidate_spert" \
  -DGGML_OPENMP=OFF -DGGML_RV_ZBA=ON -DGGML_NATIVE=OFF \
  -DGGML_CPU_REPACK=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_OPENSSL=OFF \
  -DLLAMA_CURL=OFF -DLLAMA_BUILD_UI=OFF -DLLAMA_USE_PREBUILT_UI=OFF
timeout --signal=TERM --kill-after=30s 14400s \
  cmake --build "$candidate_build" --target llama-server llama-bench -j4
candidate_kind=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["candidate"])' "$candidate_root/manifest.json")
candidate_flags=(-O3 -std=c++17 -DSPINE_K1_BOARD -march=rv64gcv_zfh_zvfh_zicbop_zihintpause_zba -mabi=lp64d
  "-I$candidate_source/include" "-I$candidate_source/ggml/include" "-I$candidate_here/.."
  "-I$candidate_source/ggml/src/ggml-cpu"
  "-L$candidate_build/bin" "-Wl,-rpath,$candidate_build/bin")
case "$candidate_kind" in
  A1|B1)
    "$candidate_cxx" "${candidate_flags[@]}" "$candidate_here/test-attention.cpp" \
      -lggml-cpu -lggml-base -o "$candidate_build/bin/test-attention"
    ;;
  C)
    "$candidate_cxx" "${candidate_flags[@]}" "$candidate_here/../test-k1-ssm-conv.cpp" \
      -lggml-cpu -lggml-base -o "$candidate_build/bin/test-ssm"
    "$candidate_cxx" "${candidate_flags[@]}" "$candidate_here/../test-k1-gdn.cpp" \
      -lggml-cpu -lggml-base -o "$candidate_build/bin/test-gdn"
    "$candidate_cxx" "${candidate_flags[@]}" "$candidate_root/test-c-state.cpp" \
      -lllama -lggml -lggml-cpu -lggml-base -o "$candidate_build/bin/test-c-state"
    ;;
  D)
    "$candidate_cxx" "${candidate_flags[@]}" "$candidate_here/test-conv-silu.cpp" \
      -lggml-cpu -lggml-base -o "$candidate_build/bin/test-conv-silu"
    ;;
esac
