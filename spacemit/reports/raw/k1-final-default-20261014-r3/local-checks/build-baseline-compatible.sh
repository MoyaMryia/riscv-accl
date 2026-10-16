#!/usr/bin/env bash
set -euo pipefail
rc_root=$HOME/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1
cd "$rc_root"
[[ -n ${TMUX:-} && ${K1_PACKAGE_LOCK_FD:-} == 9 ]] || exit 2
[[ ! -e baseline-k1-source && ! -e baseline-k1-build ]] || exit 2
cp -a baseline-source baseline-k1-source
python3 - <<'PY'
import difflib,hashlib,json
from pathlib import Path
p=Path('baseline-k1-source/ggml/src/ggml-cpu/CMakeLists.txt')
s=p.read_text();line='                ggml-cpu/spacemit/ime2_kernels.cpp\n'
assert s.count(line)==1
new=s.replace(line,'');p.write_text(new)
patch=''.join(difflib.unified_diff(s.splitlines(True),new.splitlines(True),fromfile='a/ggml/src/ggml-cpu/CMakeLists.txt',tofile='b/ggml/src/ggml-cpu/CMakeLists.txt'))
Path('baseline-k1-build-only.patch').write_text(patch)
original=json.loads(Path('baseline-source-receipt.json').read_text())['files_sha256']
actual={str(p.relative_to('baseline-k1-source')):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path('baseline-k1-source').rglob('*')) if p.is_file()}
changed=[n for n,h in actual.items() if original[n]!=h]
assert changed==['ggml/src/ggml-cpu/CMakeLists.txt']
Path('baseline-k1-source-receipt.json').write_text(json.dumps({'commit':'5ad05d8796cb094ee23a3a0152874f8a2b3060f8','compatibility_only':changed,'patch_sha256':hashlib.sha256(patch.encode()).hexdigest(),'files_sha256':actual},indent=2)+'\n')
PY
rc_cc=$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/gcc-14
rc_cxx=$HOME/Projects/llm-bench/.toolchain/gcc14/usr/bin/g++-14
rc_spert=$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2
rc_tcm=$HOME/Projects/llm-bench/.toolchain/spine-tcm
export LD_LIBRARY_PATH="$rc_tcm:$rc_spert/lib"
unset LD_PRELOAD LD_AUDIT
cmake -S baseline-k1-source -B baseline-k1-build -G Ninja -DCMAKE_BUILD_TYPE=Release \
 -DCMAKE_C_COMPILER="$rc_cc" -DCMAKE_CXX_COMPILER="$rc_cxx" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
 -DCMAKE_BUILD_RPATH_USE_ORIGIN=ON '-DCMAKE_INSTALL_RPATH=$ORIGIN' \
 -DGGML_CPU_RISCV64_SPACEMIT=ON -DSPERT_DIR="$rc_spert" -DGGML_OPENMP=OFF \
 -DGGML_RV_ZBA=ON -DGGML_NATIVE=OFF -DGGML_CPU_REPACK=OFF -DLLAMA_BUILD_TESTS=OFF \
 -DLLAMA_OPENSSL=OFF -DLLAMA_CURL=OFF -DLLAMA_BUILD_UI=OFF -DLLAMA_USE_PREBUILT_UI=OFF
set +e
timeout --signal=TERM --kill-after=30s 14400s cmake --build baseline-k1-build --target llama-server llama-bench -j4
rc_status=$?
printf '%s\n' "$rc_status" > baseline-k1-build-exit-status
exit "$rc_status"
