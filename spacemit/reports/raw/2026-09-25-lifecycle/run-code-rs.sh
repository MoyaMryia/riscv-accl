#!/bin/bash
set -euo pipefail
while [ -d /proc/243886 ] && ! grep -q '^State:.*Z' /proc/243886/status; do sleep 20; done
ROOT="$HOME/Projects/spacemit-llama-integrated"
MODELS="$HOME/Projects/spacemit-llama/models"
OUTPUT=/tmp/lifecycle-code-rs.jsonl
SOURCE=/tmp/lifecycle-code-divergence.jsonl
if [ -e "$OUTPUT" ] || [ ! -s "$SOURCE" ]; then echo 'existing output or missing baseline' >&2; exit 1; fi
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$ROOT/build/bin"
export SPINE_SPEC_RS=1
unset SPINE_FA_WIDE_TILE
for size in 2B 4B; do
  n=256; [ "$size" = 4B ] && n=512
  label="${size}-mtp-rs-code-n${n}"
  echo "START $label"
  python3 /tmp/bench-lifecycle-telemetry.py --server "$ROOT/build/bin/llama-server" \
    --model "$MODELS/Qwen3.5-${size}-MTP-Q4_0-embQ4_0-dv64k.gguf" \
    --label "$label" --mode mtp --contexts 128 --prompt-file /tmp/lifecycle-code-prompt.cpp \
    --n-predict "$n" --ignore-eos --ctx-size 8192 --capture-token-ids \
    --timeout 14400 --output "$OUTPUT" --log "/tmp/lifecycle-${label}.log"
done
python3 /tmp/audit-lifecycle.py "$OUTPUT" --require-token-ids
python3 - "$SOURCE" "$OUTPUT" <<'PY'
import json,sys

def rows(path):
    return {row['label']: row['results'][0]['token_ids']
            for row in map(json.loads,open(path)) if row.get('kind')=='measurement'}
base,rs=map(rows,sys.argv[1:])
for size,n in [('2B',256),('4B',512)]:
    direct=base[f'{size}-plain-code-prefix-n{n}']
    draft=rs[f'{size}-mtp-rs-code-n{n}']
    assert len(direct)==len(draft)==n
    first=next((i for i,(a,b) in enumerate(zip(direct,draft)) if a!=b),None)
    print(f'{size} RS_FIRST_DIFFERENCE_ZERO_BASED={first}')
PY
