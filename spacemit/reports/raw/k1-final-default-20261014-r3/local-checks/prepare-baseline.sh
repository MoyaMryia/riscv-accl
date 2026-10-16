#!/usr/bin/env bash
set -euo pipefail
rc_root=$HOME/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1
rc_repo=$HOME/Projects/spacemit-llama/llama.cpp
rc_commit=5ad05d8796cb094ee23a3a0152874f8a2b3060f8
[[ -n ${TMUX:-} && ${K1_PACKAGE_LOCK_FD:-} == 9 ]] || exit 2
[[ ! -e "$rc_root/baseline-source" && ! -e "$rc_root/baseline-build" ]] || exit 2
mkdir "$rc_root/baseline-source"
git -C "$rc_repo" archive "$rc_commit" | tar -xf - -C "$rc_root/baseline-source"
printf '%s\n' "$rc_commit" > "$rc_root/baseline-commit"
python3 - "$rc_root/baseline-source" "$rc_root/baseline-source-receipt.json" <<'PY'
import hashlib,json,sys
from pathlib import Path
r=Path(sys.argv[1]);files={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(r.rglob('*')) if p.is_file()}
Path(sys.argv[2]).write_text(json.dumps({'commit':'5ad05d8796cb094ee23a3a0152874f8a2b3060f8','files_sha256':files},indent=2)+'\n')
PY
rc_cc=$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/gcc-14
rc_cxx=$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/g++-14
rc_spert=$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2
rc_tcm=$HOME/Projects/llm-bench/.toolchain/spine-tcm
export LD_LIBRARY_PATH="$rc_tcm:$rc_spert/lib"
unset LD_PRELOAD LD_AUDIT
cmake -S "$rc_root/baseline-source" -B "$rc_root/baseline-build" -G Ninja -DCMAKE_BUILD_TYPE=Release \
 -DCMAKE_C_COMPILER="$rc_cc" -DCMAKE_CXX_COMPILER="$rc_cxx" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
 -DCMAKE_BUILD_RPATH_USE_ORIGIN=ON '-DCMAKE_INSTALL_RPATH=$ORIGIN' \
 -DGGML_CPU_RISCV64_SPACEMIT=ON -DSPERT_DIR="$rc_spert" -DGGML_OPENMP=OFF \
 -DGGML_RV_ZBA=ON -DGGML_NATIVE=OFF -DGGML_CPU_REPACK=OFF -DLLAMA_BUILD_TESTS=OFF \
 -DLLAMA_OPENSSL=OFF -DLLAMA_CURL=OFF -DLLAMA_BUILD_UI=OFF -DLLAMA_USE_PREBUILT_UI=OFF
set +e
timeout --signal=TERM --kill-after=30s 14400s cmake --build "$rc_root/baseline-build" --target llama-server llama-bench -j4
rc_status=$?
printf '%s\n' "$rc_status" > "$rc_root/baseline-build-exit-status"
exit "$rc_status"
