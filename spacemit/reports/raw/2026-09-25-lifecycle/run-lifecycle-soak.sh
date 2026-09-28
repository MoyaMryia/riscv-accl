#!/bin/bash
set -uo pipefail
while [ -d /proc/151664 ] && ! grep -q '^State:.*Z' /proc/151664/status; do sleep 20; done
if ! python3 - <<'PY'
import json
from pathlib import Path
needed = {f'{size}-{mode}-long' for size in ('2B', '4B') for mode in ('plain', 'mtp')}
passed = set()
path = Path('/tmp/lifecycle-followup.jsonl')
if path.exists():
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get('kind') != 'measurement' or row.get('label') not in needed:
            continue
        result = row['results'][0]
        if (result.get('stop_type') == 'limit' and result.get('tokens_predicted') == 2048
                and result.get('streamed_tokens') == 2048 and not result.get('error')):
            passed.add(row['label'])
missing = needed - passed
print('long-run gate:', 'passed' if not missing else f'missing or failed {sorted(missing)}')
raise SystemExit(bool(missing))
PY
then
  echo 'Skipping soak because the initial long-generation gate did not pass' >&2
  exit 1
fi
ROOT="$HOME/Projects/spacemit-llama-integrated"
MODELS="$HOME/Projects/spacemit-llama/models"
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$ROOT/build/bin"
for size in 2B 4B; do
  repeats=4
  if [ "$size" = 4B ]; then repeats=2; fi
  for mode in plain mtp; do
    label="${size}-${mode}-soak"
    echo "START $label repeats=$repeats"
    python3 /tmp/bench-lifecycle.py \
      --server "$ROOT/build/bin/llama-server" \
      --model "$MODELS/Qwen3.5-${size}-MTP-Q4_0-embQ4_0-dv64k.gguf" \
      --label "$label" --mode "$mode" --contexts 128 \
      --n-predict 2048 --ctx-size 4096 --ignore-eos --repeats "$repeats" \
      --output /tmp/lifecycle-soak.jsonl \
      --log "/tmp/lifecycle-${label}.log" || echo "FAILED $label"
  done
done
