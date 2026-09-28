#!/usr/bin/env bash
# Test whether disabling flash attention removes the fixed-code MTP mismatch.
set -euo pipefail

BENCH_ROOT=${BENCH_ROOT:-"$HOME/Projects/riscv-accl-bench-2026-09-27"}
SERVER_ROOT=${SERVER_ROOT:-"$HOME/Projects/spacemit-llama-integrated"}
SERVER="$SERVER_ROOT/build/bin/llama-server"
SOURCE="$BENCH_ROOT/bench-lifecycle.py"
RUNNER="$BENCH_ROOT/bench-lifecycle-fa-off.py"
OUT="$BENCH_ROOT/lifecycle-code-fa-off.jsonl"
PROMPT="$BENCH_ROOT/lifecycle-code-prompt.cpp"

if [ -e "$OUT" ]; then echo "existing output: $OUT" >&2; exit 1; fi
if pgrep -x llama-server >/dev/null; then echo 'another server is running' >&2; exit 1; fi
grep -q "'-fa', 'on'" "$SOURCE"
sed "s/'-fa', 'on'/'-fa', 'off'/" "$SOURCE" > "$RUNNER"
grep -q "'-fa', 'off'" "$RUNNER"
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$SERVER_ROOT/build/bin"
unset SPINE_FA_WIDE_TILE SPINE_SPEC_RS

for mode in plain mtp; do
  label="2B-${mode}-code-fa-off-n256"
  python3 "$RUNNER" --server "$SERVER" \
    --model "$HOME/Projects/spacemit-llama/models/Qwen3.5-2B-MTP-Q4_0-embQ4_0-dv64k.gguf" \
    --label "$label" --mode "$mode" --contexts 128 \
    --prompt-file "$PROMPT" --n-predict 256 --ignore-eos \
    --capture-token-ids --ctx-size 8192 --timeout 3600 \
    --output "$OUT" --log "$BENCH_ROOT/$label.log"
done
python3 "$BENCH_ROOT/audit-lifecycle.py" "$OUT" --require-token-ids --min-runs-per-group 2
python3 - "$OUT" <<'PY'
import json, sys
rows = {row['mode']: row['results'][0]['token_ids']
        for row in map(json.loads, open(sys.argv[1])) if row.get('kind') == 'measurement'}
a, b = rows['plain'], rows['mtp']
assert len(a) == len(b) == 256
first = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), None)
print(f'FA_OFF_FIRST_DIFFERENCE_ZERO_BASED={first}')
PY
