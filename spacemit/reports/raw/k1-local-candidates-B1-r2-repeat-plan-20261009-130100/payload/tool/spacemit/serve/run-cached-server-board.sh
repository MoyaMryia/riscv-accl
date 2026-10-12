#!/usr/bin/env bash
# Single-slot, direct-decoding llama-server for repeated questions over one document.
set -euo pipefail

SERVER_ROOT=${SERVER_ROOT:-"$HOME/Projects/spacemit-llama-integrated"}
MODEL_PATH=${MODEL_PATH:-"$HOME/Projects/spacemit-llama/models/Qwen3.5-2B-MTP-Q4_0-embQ4_0-dv64k.gguf"}
CTX_SIZE=${CTX_SIZE:-8192}
PORT=${PORT:-18085}

if [ ! -x "$SERVER_ROOT/build/bin/llama-server" ]; then
  echo "missing llama-server: $SERVER_ROOT/build/bin/llama-server" >&2
  exit 1
fi
if [ ! -s "$MODEL_PATH" ]; then
  echo "missing model: $MODEL_PATH" >&2
  exit 1
fi
if pgrep -x llama-server >/dev/null; then
  echo 'another llama-server is already running; its slot cache could interfere' >&2
  exit 1
fi

export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$SERVER_ROOT/build/bin${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export SPINE_FA_WIDE_TILE=1
unset SPINE_MTP_WINDOW SPINE_SPEC_RS
exec "$SERVER_ROOT/build/bin/llama-server" \
  -m "$MODEL_PATH" --alias local --host 127.0.0.1 --port "$PORT" \
  -t 4 -c "$CTX_SIZE" --parallel 1 -b 32 -ub 32 -fa on
