#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
exec >run.log 2>&1
trap 'rc=$?; date -u "+END %Y-%m-%dT%H:%M:%SZ"; printf "%s\n" "$rc" > exit-status' EXIT
date -u '+START %Y-%m-%dT%H:%M:%SZ'
python="$PWD/../venv/bin/python"
/home/moyamryia/.local/bin/uv pip freeze --python "$python" > dependencies.txt
export TOKENIZERS_PARALLELISM=false
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8
timeout --signal=TERM --kill-after=30s 3600s "$python" -u tools/bert_train.py \
    --base "$PWD/../base" --tasks "$PWD/tasks.jsonl" \
    --receipt "$PWD/receipt.json" --regression "$PWD/regression.json" \
    --output "$PWD/result"
