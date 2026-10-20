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
export NO_PROXY=127.0.0.1,localhost
r3="$HOME/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1/final-r3"
python3 -u tools/router_e2e.py \
    --output "$PWD/result" --server "$r3/build/bin/llama-server" \
    --models "$HOME/Projects/spacemit-llama/models" \
    --spert "$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2" \
    --tcm "$HOME/Projects/llm-bench/.toolchain/spine-tcm" \
    --manifest "$r3/package/manifest.json" --build-receipt "$r3/build/build-receipt.json" \
    --chat "$PWD/tools/chat.py" --quality "$PWD/tools/quality.py" \
    --effective "$PWD/tools/effective.py" --tool-receipt "$PWD/tool-receipt.json" \
    --cases "$PWD/cases.json" --cases-module "$PWD/tools/router_cases.py" \
    --router "$PWD/router" --max-tokens 4096 \
    --bert-model "$PWD/encoder-f32.gguf" --bert-head "$PWD/bert-head.json" \
    --serve --diagnostic-plan "$PWD/diagnostic-plan.json" --legacy-request "$PWD/legacy-request.json"
