#!/usr/bin/env bash
# Quantize Qwen3.5 weights and tied token/output embeddings to the X60 IME1 Q4_0 path.
set -euo pipefail
if [ "$#" -ne 3 ]; then
  echo "usage: $0 /path/to/llama-quantize source.gguf output.gguf" >&2
  exit 2
fi
quantizer=$1
source=$2
output=$3
[ -x "$quantizer" ] || { echo "quantizer not executable: $quantizer" >&2; exit 1; }
[ -f "$source" ] || { echo "source not found: $source" >&2; exit 1; }
[ ! -e "$output" ] || { echo "output exists: $output" >&2; exit 1; }
"$quantizer" --token-embedding-type q4_0 --output-tensor-type q4_0 \
  --allow-requantize "$source" "$output" Q4_0
