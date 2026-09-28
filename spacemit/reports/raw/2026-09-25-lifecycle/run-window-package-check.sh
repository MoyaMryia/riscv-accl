#!/bin/bash
set -euo pipefail
while [ -d /proc/245391 ] && ! grep -q '^State:.*Z' /proc/245391/status; do sleep 20; done
BASE="$HOME/Projects/spacemit-llama-integrated"
WORKTREE=/tmp/riscv-window-package-check
PKG=/tmp/riscv-patchset-20260927
if [ -e "$WORKTREE" ] || [ -e "$PKG" ]; then echo 'existing worktree or package path' >&2; exit 1; fi
mkdir "$PKG"
tar -xzf /tmp/riscv-patchset-20260927.tar.gz -C "$PKG"
git -C "$BASE" worktree add --detach "$WORKTREE" 5ad05d8
cleanup() { git -C "$BASE" worktree remove --force "$WORKTREE"; }
trap cleanup EXIT
bash "$PKG/spacemit/apply-patches.sh" "$WORKTREE" \
  --frspec --lowacc --q8-ime1 --m4-scale --rvv256 --windowed-mtp
git -C "$WORKTREE" diff --check
cmp "$WORKTREE/src/llama-model.cpp" "$BASE/src/llama-model.cpp"
for path in ggml/src/ggml-cpu/ggml-cpu-aarch64.cpp ggml/src/ggml-cpu/ggml-cpu.cpp; do
  if [ -e "$WORKTREE/$path" ] && [ -e "$BASE/$path" ]; then cmp "$WORKTREE/$path" "$BASE/$path"; fi
done
echo 'PASS: all optional patches applied cleanly; integrated model source matches'
