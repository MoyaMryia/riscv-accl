#!/usr/bin/env bash
# Apply the measured SpaceMiT X60 changes to an official-fork checkout.
set -euo pipefail

if [[ $# -lt 1 || $# -gt 7 ]]; then
  echo "usage: $0 /path/to/spacemit-com/llama.cpp [--frspec] [--lowacc] [--q8-ime1] [--m4-scale] [--rvv256] [--windowed-mtp]" >&2
  exit 2
fi
frspec=0
lowacc=0
q8_ime1=0
m4_scale=0
rvv256=0
windowed_mtp=0
for option in "${@:2}"; do
  case "$option" in
    --frspec) [[ $frspec -eq 0 ]] || exit 2; frspec=1 ;;
    --lowacc) [[ $lowacc -eq 0 ]] || exit 2; lowacc=1 ;;
    --q8-ime1) [[ $q8_ime1 -eq 0 ]] || exit 2; q8_ime1=1 ;;
    --m4-scale) [[ $m4_scale -eq 0 ]] || exit 2; m4_scale=1 ;;
    --rvv256) [[ $rvv256 -eq 0 ]] || exit 2; rvv256=1 ;;
    --windowed-mtp) [[ $windowed_mtp -eq 0 ]] || exit 2; windowed_mtp=1 ;;
    *) echo "unknown option: $option" >&2; exit 2 ;;
  esac
done
checkout=$(git -C "$1" rev-parse --show-toplevel)
patches=$(cd "$(dirname "${BASH_SOURCE[0]}")/patches" && pwd)
if [[ $(git -C "$checkout" rev-parse --short=7 HEAD) != 5ad05d8 ]]; then
  echo "expected official-fork base commit 5ad05d8 in $checkout" >&2
  exit 1
fi
if [[ -n $(git -C "$checkout" status --porcelain) ]]; then
  echo "checkout must be clean before applying patches: $checkout" >&2
  exit 1
fi
for n in 0001 0002 0003 0004; do
  patch=$(find "$patches" -maxdepth 1 -name "$n-*.patch" -print -quit)
  git -C "$checkout" apply --check "$patch"
  git -C "$checkout" apply "$patch"
done
if [[ $frspec -eq 1 ]]; then
  git -C "$checkout" apply --check "$patches/0005-frequency-ranked-d2t.patch"
  git -C "$checkout" apply "$patches/0005-frequency-ranked-d2t.patch"
fi
if [[ $lowacc -eq 1 ]]; then
  git -C "$checkout" apply --check "$patches/0006-low-acceptance-fallback.patch"
  git -C "$checkout" apply "$patches/0006-low-acceptance-fallback.patch"
fi
if [[ $q8_ime1 -eq 1 ]]; then
  git -C "$checkout" apply --check "$patches/0007-q8-ime1.patch"
  git -C "$checkout" apply "$patches/0007-q8-ime1.patch"
fi
if [[ $m4_scale -eq 1 ]]; then
  git -C "$checkout" apply --check "$patches/0008-ime-m4-scale.patch"
  git -C "$checkout" apply "$patches/0008-ime-m4-scale.patch"
fi
if [[ $rvv256 -eq 1 ]]; then
  git -C "$checkout" apply --check "$patches/0009-wide-rvv-vlen256.patch"
  git -C "$checkout" apply "$patches/0009-wide-rvv-vlen256.patch"
fi
if [[ $windowed_mtp -eq 1 ]]; then
  git -C "$checkout" apply --check "$patches/0010-windowed-mtp.patch"
  git -C "$checkout" apply "$patches/0010-windowed-mtp.patch"
fi
git -C "$checkout" diff --check
printf 'Applied SpaceMiT patches to %s\n' "$checkout"
