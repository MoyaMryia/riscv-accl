#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
exec >run.log 2>&1
trap 'rc=$?; date -u "+END %Y-%m-%dT%H:%M:%SZ"; printf "%s\n" "$rc" > exit-status' EXIT
date -u '+START %Y-%m-%dT%H:%M:%SZ'
exec 9>"$HOME/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock"
printf 'WAIT_LOCK\n'
flock 9
export K1_PACKAGE_LOCK_FD=9
printf 'LOCK_ACQUIRED\n'
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy
r3="$HOME/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1/final-r3"
timeout --signal=TERM --kill-after=60s 1800s python3 -u tools/bert_bench.py \
    --server "$r3/build/bin/llama-server" \
    --spert "$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2" \
    --tcm "$HOME/Projects/llm-bench/.toolchain/spine-tcm" \
    --router "$PWD/router" --head "$PWD/head.json" \
    --model "$PWD/encoder-f32.gguf" --reference "$PWD/reference.json" \
    --receipt "$PWD/receipt.json" --output "$PWD/result"
