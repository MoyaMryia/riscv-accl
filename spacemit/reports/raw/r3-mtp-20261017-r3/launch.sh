#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
base="$HOME/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1/final-r3"
exec bash run-board.sh "$PWD" "$base/build/bin/llama-server" \
    "$HOME/Projects/spacemit-llama/models" \
    "$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2" \
    "$HOME/Projects/llm-bench/.toolchain/spine-tcm" \
    "$base/package/manifest.json" "$base/build/build-receipt.json" "$PWD/request.json"
