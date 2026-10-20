#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
trap 'rc=$?; date -u "+END %Y-%m-%dT%H:%M:%SZ"; printf "%s\n" "$rc" > exit-status' EXIT
exec > run.log 2>&1
date -u '+START %Y-%m-%dT%H:%M:%SZ'
exec 9>"$HOME/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock"
printf 'WAIT_LOCK\n'
flock 9
export K1_PACKAGE_LOCK_FD=9
printf 'LOCK_ACQUIRED\n'
base="$HOME/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1/final-r3"
timeout --signal=TERM --kill-after=60s 2400s python3 -u head_probe.py \
    --output "$PWD/result" --server "$base/build/bin/llama-server" \
    --models "$HOME/Projects/spacemit-llama/models" \
    --spert "$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2" \
    --tcm "$HOME/Projects/llm-bench/.toolchain/spine-tcm" \
    --manifest "$base/package/manifest.json" --build-receipt "$base/build/build-receipt.json" \
    --request "$PWD/cases.json" --records "$PWD/records.json" \
    --chat "$PWD/chat.py" --quality "$PWD/quality.py" --effective "$PWD/effective.py" \
    --tool-receipt "$PWD/tools.json" --prefix-rows 65536 --case-id chinese_technical_explanation
