#!/bin/bash
set -euo pipefail

# Run only after the serialized RVV, draft-length, page, and KV jobs finish.
while [ -d /proc/243450 ] && ! grep -q '^State:.*Z' /proc/243450/status; do sleep 20; done

ROOT="$HOME/Projects/spacemit-llama-integrated"
MODELS="$HOME/Projects/spacemit-llama/models"
PATCH=/tmp/spec-logits-trace.patch
OUTPUT=/tmp/lifecycle-spec-logits-trace.jsonl
if [ -e "$OUTPUT" ]; then echo "existing $OUTPUT" >&2; exit 1; fi

cd "$ROOT"
git apply --check "$PATCH"
git apply "$PATCH"
restore_source_and_binary() {
  git apply -R "$PATCH"
  cmake --build build --target llama-server -j 4
}
trap restore_source_and_binary EXIT
cmake --build build --target llama-server -j 4

export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$ROOT/build/bin"
unset SPINE_FA_WIDE_TILE
for size in 2B 4B; do
  if [ "$size" = 2B ]; then
    n=256
    export SPINE_TRACE_LOGITS_BEGIN=177 SPINE_TRACE_LOGITS_END=181
  else
    n=512
    export SPINE_TRACE_LOGITS_BEGIN=301 SPINE_TRACE_LOGITS_END=305
  fi
  for mode in plain mtp; do
    label="${size}-${mode}-spec-logits-n${n}"
    echo "START $label"
    python3 /tmp/bench-lifecycle-telemetry.py --server "$ROOT/build/bin/llama-server" \
      --model "$MODELS/Qwen3.5-${size}-MTP-Q4_0-embQ4_0-dv64k.gguf" \
      --label "$label" --mode "$mode" --contexts 128 \
      --prompt-file /tmp/lifecycle-code-prompt.cpp \
      --n-predict "$n" --ignore-eos --ctx-size 8192 --capture-token-ids \
      --timeout 14400 --output "$OUTPUT" --log "/tmp/lifecycle-${label}.log"
  done
done
python3 /tmp/audit-lifecycle.py "$OUTPUT" --require-token-ids
python3 - /tmp/lifecycle-code-divergence.jsonl "$OUTPUT" <<'PYCHECK'
import json, sys

def measurements(path):
    return {row['label']: row['results'][0]['token_ids']
            for row in map(json.loads, open(path)) if row.get('kind') == 'measurement'}

baseline, traced = map(measurements, sys.argv[1:])
for size, n in [('2B', 256), ('4B', 512)]:
    for mode in ('plain', 'mtp'):
        base = baseline[f'{size}-{mode}-code-prefix-n{n}']
        trace = traced[f'{size}-{mode}-spec-logits-n{n}']
        assert trace == base, f'trace changed {size} {mode} output'
    direct = traced[f'{size}-plain-spec-logits-n{n}']
    mtp = traced[f'{size}-mtp-spec-logits-n{n}']
    first = next((i for i, (a, b) in enumerate(zip(direct, mtp)) if a != b), None)
    print(f'{size} first_zero_based={first}')
PYCHECK
for size in 2B 4B; do
  for mode in plain mtp; do
    n=256; [ "$size" = 4B ] && n=512
    grep 'SPINE_TRACE_LOGITS:' "/tmp/lifecycle-${size}-${mode}-spec-logits-n${n}.log" | tail -n 25
  done
done
