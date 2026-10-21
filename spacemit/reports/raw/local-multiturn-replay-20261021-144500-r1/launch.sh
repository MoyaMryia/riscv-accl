#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
exec >run.log 2>&1
trap 'rc=$?; printf "%s\n" "$rc" > exit-status; date -Is' EXIT
export PYTHONDONTWRITEBYTECODE=1
repo=/home/moyamryia/Projects/riscv-accl
date -Is
python3 -u input/local_multi_turn_replay.py \
    --output "$PWD/result" \
    --source-batch "$repo/spacemit/reports/raw/delivery-multiturn-20261021-115000-r2" \
    --server "$repo/lab/local-reference/build-a990751-generic/bin/llama-server" \
    --models "$repo/lab/local-reference/models" \
    --manifest "$repo/spacemit/final-release/manifest.json" \
    --chat "$PWD/input/chat.py" --port 18260 --timeout 900
