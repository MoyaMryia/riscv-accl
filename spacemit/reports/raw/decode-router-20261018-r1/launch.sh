#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
trap 'rc=$?; date -u "+END %Y-%m-%dT%H:%M:%SZ"; printf "%s\n" "$rc" > exit-status' EXIT
exec >run.log 2>&1
date -u '+START %Y-%m-%dT%H:%M:%SZ'
exec 9>"$HOME/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock"
printf 'WAIT_LOCK\n'
flock 9
printf 'LOCK_ACQUIRED\n'
if pgrep -x llama-server; then
    printf '存在活动的 llama-server，停止分类延迟测量。\n' >&2
    exit 1
else
    rc=$?
    if [ "$rc" -ne 1 ]; then exit "$rc"; fi
fi
timeout --signal=TERM --kill-after=10s 600s python3 -u evaluate_routing.py \
    --model "$PWD/model.json.gz" --tasks "$PWD/tasks.jsonl" \
    --measurements "$PWD/measurements.json" --requests "$PWD/requests.json" \
    --output "$PWD/result" --repeats 40
