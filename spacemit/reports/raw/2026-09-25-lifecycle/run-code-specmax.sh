#!/bin/bash
set -euo pipefail
while [ -d /proc/243199 ] && ! grep -q '^State:.*Z' /proc/243199/status; do sleep 20; done
ROOT="$HOME/Projects/spacemit-llama-integrated"
MODELS="$HOME/Projects/spacemit-llama/models"
SOURCE=/tmp/lifecycle-code-divergence.jsonl
OUTPUT=/tmp/lifecycle-code-specmax.jsonl
if [ ! -s "$SOURCE" ] || [ -e "$OUTPUT" ]; then echo 'missing source or existing output' >&2; exit 1; fi
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$ROOT/build/bin"
unset SPINE_FA_WIDE_TILE
for size in 2B 4B; do
  n=$(python3 - "$SOURCE" "$size" <<'PY'
import json,re,sys
rows={}
for row in map(json.loads,open(sys.argv[1])):
    m=re.fullmatch(rf'{sys.argv[2]}-(plain|mtp)-code-prefix-n(\d+)',row.get('label',''))
    if row.get('kind')=='measurement' and m:
        mode,n=m.groups(); rows[(int(n),mode)]=row['results'][0]['tokens_sha256']
for n in sorted({n for n,mode in rows}):
    if (n,'plain') in rows and (n,'mtp') in rows and rows[(n,'plain')]!=rows[(n,'mtp')]:
        print(n);break
PY
)
  if [ -z "$n" ]; then echo "NO_MISMATCH $size"; continue; fi
  for max in 1 2; do
    label="${size}-mtp-code-specmax${max}-n${n}"
    echo "START $label"
    python3 /tmp/bench-lifecycle-specmax.py --server "$ROOT/build/bin/llama-server" \
      --model "$MODELS/Qwen3.5-${size}-MTP-Q4_0-embQ4_0-dv64k.gguf" \
      --label "$label" --mode mtp --spec-draft-n-max "$max" \
      --contexts 128 --prompt-file /tmp/lifecycle-code-prompt.cpp \
      --n-predict "$n" --ignore-eos --ctx-size 8192 --capture-token-ids \
      --timeout 14400 --output "$OUTPUT" --log "/tmp/lifecycle-${label}.log"
    python3 - "$SOURCE" "$OUTPUT" "$size" "$n" "$max" <<'PY'
import json,sys
source,output,size,n,maximum=sys.argv[1],sys.argv[2],sys.argv[3],int(sys.argv[4]),int(sys.argv[5])
def ids(path,label):
    for row in map(json.loads,open(path)):
        if row.get('kind')=='measurement' and row.get('label')==label:
            return row['results'][0]['token_ids']
    raise ValueError(f'missing {label}')
a=ids(source,f'{size}-plain-code-prefix-n{n}')
b=ids(output,f'{size}-mtp-code-specmax{maximum}-n{n}')
assert len(a)==len(b)==n
first=next((i for i,(x,y) in enumerate(zip(a,b)) if x!=y),None)
print(f'{"MATCH" if first is None else "MISMATCH"} {size} n={n} specmax={maximum} first_zero_based={first}')
PY
  done
done
python3 /tmp/audit-lifecycle.py "$OUTPUT" --require-token-ids
