#!/bin/bash
set -euo pipefail
while [ -d /proc/243410 ] && ! grep -q '^State:.*Z' /proc/243410/status; do sleep 20; done
ROOT="$HOME/Projects/spacemit-llama-integrated"
MODEL="$HOME/Projects/spacemit-llama/models/Qwen3.5-4B-MTP-Q4_0-embQ4_0-dv64k.gguf"
OUTPUT=/tmp/lifecycle-4b-kv-long.jsonl
if [ -e "$OUTPUT" ]; then echo "existing $OUTPUT" >&2; exit 1; fi
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$ROOT/build/bin"
unset SPINE_FA_WIDE_TILE
for kv in f16 q4_0; do
  label="4B-kv-${kv}-512out"
  echo "START $label"
  python3 /tmp/bench-lifecycle-telemetry.py --server "$ROOT/build/bin/llama-server" \
    --model "$MODEL" --label "$label" --mode plain --contexts 2048 \
    --n-predict 512 --ignore-eos --ctx-size 16384 \
    --cache-type-k "$kv" --cache-type-v "$kv" --capture-token-ids \
    --output "$OUTPUT" --log "/tmp/lifecycle-${label}.log"
done
python3 /tmp/audit-lifecycle.py "$OUTPUT" --require-token-ids --min-runs-per-group 2
python3 - "$OUTPUT" <<'PY'
import json,sys
rows={}
for row in map(json.loads,open(sys.argv[1])):
    if row.get('kind')=='measurement':
        rows[row['label']]=row['results'][0]['token_ids']
a,b=rows['4B-kv-f16-512out'],rows['4B-kv-q4_0-512out']
assert len(a)==len(b)==512
first=next((i for i,(x,y) in enumerate(zip(a,b)) if x!=y),None)
print(f'KV_OUTPUT_FIRST_DIFFERENCE_ZERO_BASED={first}')
PY
