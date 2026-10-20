#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
trap 'rc=$?; printf "%s\n" "$rc" > exit-status' EXIT
exec >run.log 2>&1
date -u '+START %Y-%m-%dT%H:%M:%SZ'
exec 9>"$HOME/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock"
printf 'WAIT_LOCK\n'
flock 9
printf 'LOCK_ACQUIRED\n'
mkdir proxy-tools
source_url='https://gh-proxy.com/https://raw.githubusercontent.com/MoyaMryia/riscv-accl/0e487a3592fd2df3bbb6ba86eba038be7e33055e/spacemit/models/tools'
for name in extract-mtp-safetensors.py add-mtp-4b.py; do
    curl --fail --silent --show-error --max-time 90 "$source_url/$name" --output "proxy-tools/$name"
done
printf 'SOURCE_TOOLS_READY\n'
nice -n 10 python3 -u prove-sources.py \
    --root "$PWD/result" \
    --model-lock "$PWD/official-source-lock.json" \
    --extractor "$PWD/proxy-tools/extract-mtp-safetensors.py" \
    --assembler "$PWD/proxy-tools/add-mtp-4b.py" \
    --base-model "$HOME/Projects/spacemit-llama/models/Qwen3.5-4B-Q4_0-embQ4_0.gguf" \
    --reference-model "$HOME/Projects/spacemit-llama/models/Qwen3.5-4B-MTP-Q4_0-embQ4_0.gguf" \
    --compiler-root "$HOME/Projects/llm-bench/.toolchain/gcc14"
date -u '+END %Y-%m-%dT%H:%M:%SZ'
