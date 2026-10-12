#!/usr/bin/env bash
# One scoreable 2B/16k changed-question comparison; runs only on MUSE-Pi-Pro.
set -euo pipefail
BENCH_ROOT=${BENCH_ROOT:-"$HOME/Projects/riscv-accl-bench-2026-09-27"}
SERVER_ROOT=${SERVER_ROOT:-"$HOME/Projects/spacemit-llama-integrated"}
label=2B-shared-document-16384-quality256-rvv1
output="$BENCH_ROOT/$label.jsonl"
log="$BENCH_ROOT/$label.log"
document="$BENCH_ROOT/shared-document-public-llamacpp.txt"
model="$HOME/Projects/spacemit-llama/models/Qwen3.5-2B-MTP-Q4_0-embQ4_0-dv64k.gguf"
if [ -e "$output" ] || [ -e "$log" ]; then echo 'quality output already exists' >&2; exit 1; fi
if pgrep -x llama-server >/dev/null; then echo 'another server is running' >&2; exit 1; fi
if [ ! -s "$document" ]; then echo 'public document corpus missing' >&2; exit 1; fi
if [ "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -lt 10485760 ]; then
  echo 'less than 10 GiB MemAvailable' >&2; exit 1
fi
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$SERVER_ROOT/build/bin"
export SPINE_FA_WIDE_TILE=1
unset SPINE_MTP_WINDOW SPINE_SPEC_RS
(
  ulimit -v 12582912
  timeout --signal=TERM --kill-after=20s 14400s python3 "$BENCH_ROOT/bench-shared-document-cache.py" \
    --server "$SERVER_ROOT/build/bin/llama-server" --model "$model" --model-size 2B \
    --document "$document" --context 16384 --ctx-size 20480 \
    --n-predict 256 --allow-eos --timeout 5400 --output "$output" --log "$log"
)
grep -q 'SPINE_FA_WIDE_TILE: RVV tiled attention enabled for 256-dim heads' "$log"
python3 - "$output" <<'PY'
import json, sys
cfg, a, w, c = [json.loads(line) for line in open(sys.argv[1])]
assert cfg['n_predict'] == 256 and cfg['ignore_eos'] is False
assert [r['name'] for r in (a,w,c)] == ['question_a_cold','question_b_warm','question_b_cold_control']
for record in (a,w,c):
    result = record['result']
    assert result['error'] is None
    assert isinstance(result.get('text'), str) and len(result['text']) >= 40
    assert result['tokens_predicted'] >= 32
assert a['result']['timings']['cache_n'] == 0
assert w['result']['timings']['cache_n'] >= 0.9 * 16384
assert c['result']['timings']['cache_n'] == 0
print('PASS quality records: three readable answers, warm shared prefix, cold control')
PY
