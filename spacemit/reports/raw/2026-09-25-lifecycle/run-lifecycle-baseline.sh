#!/bin/bash
set -euo pipefail
ROOT="$HOME/Projects/spacemit-llama-integrated"
MODELS="$HOME/Projects/spacemit-llama/models"
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$ROOT/build/bin"
python3 /tmp/bench-lifecycle.py --server "$ROOT/build/bin/llama-server" --model "$MODELS/Qwen3.5-2B-MTP-Q4_0-embQ4_0-dv64k.gguf" --label 2B-plain --contexts 128 2048 8192 12288 --n-predict 32 --ctx-size 16384 --mode plain --output /tmp/lifecycle-baseline.jsonl --log /tmp/lifecycle-2b-plain.log
python3 /tmp/bench-lifecycle.py --server "$ROOT/build/bin/llama-server" --model "$MODELS/Qwen3.5-4B-MTP-Q4_0-embQ4_0-dv64k.gguf" --label 4B-plain --contexts 128 2048 8192 12288 --n-predict 32 --ctx-size 16384 --mode plain --output /tmp/lifecycle-baseline.jsonl --log /tmp/lifecycle-4b-plain.log
