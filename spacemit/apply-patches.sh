#!/usr/bin/env bash
# Apply the measured SpaceMiT X60 changes to an official-fork checkout.
set -euo pipefail

if [[ $# -lt 1 || $# -gt 3 ]]; then
  echo "usage: $0 /path/to/spacemit-com/llama.cpp [--frspec] [--lowacc]" >&2
  exit 2
fi
frspec=0
lowacc=0
for option in "${@:2}"; do
  case "$option" in
    --frspec) [[ $frspec -eq 0 ]] || exit 2; frspec=1 ;;
    --lowacc) [[ $lowacc -eq 0 ]] || exit 2; lowacc=1 ;;
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
git -C "$checkout" diff --check
printf 'Applied SpaceMiT patches to %s\n' "$checkout"
