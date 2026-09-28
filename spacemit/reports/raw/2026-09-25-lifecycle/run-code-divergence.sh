#!/bin/bash
set -euo pipefail
ROOT="$HOME/Projects/spacemit-llama-integrated"
MODELS="$HOME/Projects/spacemit-llama/models"
OUTPUT=/tmp/lifecycle-code-divergence.jsonl
if [ -e "$OUTPUT" ]; then echo "existing $OUTPUT" >&2; exit 1; fi
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$ROOT/build/bin"
unset SPINE_FA_WIDE_TILE
for size in 2B 4B; do
  for n in 256 512 1024 2048 4096; do
    for mode in plain mtp; do
      label="${size}-${mode}-code-prefix-n${n}"
      echo "START $label"
      python3 /tmp/bench-lifecycle-capture.py --server "$ROOT/build/bin/llama-server" \
        --model "$MODELS/Qwen3.5-${size}-MTP-Q4_0-embQ4_0-dv64k.gguf" \
        --label "$label" --mode "$mode" --contexts 128 \
        --prompt-file /tmp/lifecycle-code-prompt.cpp --n-predict "$n" \
        --ignore-eos --ctx-size 8192 --capture-token-ids --timeout 14400 \
        --output "$OUTPUT" --log "/tmp/lifecycle-${label}.log"
    done
    if ! python3 - "$OUTPUT" "$size" "$n" <<'PY'
import json,sys
path,size,n=sys.argv[1],sys.argv[2],int(sys.argv[3])
rows={}
for row in map(json.loads,open(path)):
    if row.get('kind')=='measurement' and row.get('label') in (f'{size}-plain-code-prefix-n{n}',f'{size}-mtp-code-prefix-n{n}'):
        rows[row['mode']]=row['results'][0]
assert set(rows)=={'plain','mtp'}
a,b=rows['plain']['token_ids'],rows['mtp']['token_ids']
assert len(a)==len(b)==n
first=next((i for i,(x,y) in enumerate(zip(a,b)) if x!=y),None)
if first is None:
    print(f'MATCH {size} n={n}')
else:
    print(f'MISMATCH {size} n={n} first_zero_based={first} direct_id={a[first]} mtp_id={b[first]}')
    raise SystemExit(1)
PY
    then
      break
    fi
  done
done
python3 /tmp/audit-lifecycle.py "$OUTPUT" --require-token-ids
