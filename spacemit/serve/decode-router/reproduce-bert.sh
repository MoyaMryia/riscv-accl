#!/usr/bin/env bash
# 在新目录下载底座、恢复依赖、微调并导出原生模型。
set -euo pipefail
if [ "$#" -ne 1 ]; then
    printf '用法：%s 新输出目录\n' "$0" >&2
    exit 2
fi
script_dir=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$script_dir/../../.." && pwd)
case "$1" in
    /*) output=$1 ;;
    *) output="$PWD/$1" ;;
esac
mkdir -p "$(dirname "$output")"
mkdir "$output"
printf '复现输出：%s\n' "$output"
exec >"$output/run.log" 2>&1
trap 'rc=$?; date -u "+END %Y-%m-%dT%H:%M:%SZ"; printf "%s\n" "$rc" > "$output/exit-status"' EXIT
date -u '+START %Y-%m-%dT%H:%M:%SZ'
if [ "$(uname -s)" != Linux ] || [ "$(uname -m)" != x86_64 ]; then
    printf '本复现入口使用 Linux x86_64 的 CPU 依赖。\n' >&2
    exit 2
fi
for command in uv curl tar python3; do
    command -v "$command" >/dev/null
done
source_records="$repo/spacemit/reports/raw/router-bert-20261018-r1"
python_version=$(python3 - "$source_records/training/training.json" <<'PY'
import json
import sys
print(json.load(open(sys.argv[1]))['versions']['python'])
PY
)
python=$(uv python find --no-python-downloads "$python_version")
mkdir "$output/tools" "$output/base" "$output/converter"
for file in bert_train.py bert_common.py classifier.py train.py model.json.gz; do
    cp "$source_records/training/tools/$file" "$output/tools/"
done
cp "$source_records/source/bert_export.py" "$output/tools/"
cp "$script_dir/bert_reproduce.py" "$output/tools/"
cp "$script_dir/data-v2/tasks-bert-v1.jsonl" "$output/tasks.jsonl"
cp "$script_dir/data-v2/regression.json" "$output/regression.json"
cp "$script_dir/data-v2/bert-source-receipt.json" "$output/receipt.json"
cp "$source_records/training/training.json" "$output/original-training.json"
cp "$source_records/training/dependencies.txt" "$output/requirements.txt"
cp "$source_records/source/artifacts.json" "$output/original-artifacts.json"
cp "$source_records/source/converter-source.tgz" "$output/converter-source.tgz"
uv venv --python "$python" "$output/venv"
python="$output/venv/bin/python"
if ! torch_requirement=$(grep -E '^torch==[^[:space:]]+\+cpu$' "$output/requirements.txt"); then
    printf '冻结依赖缺少 CPU torch 版本。\n' >&2
    exit 1
fi
uv pip install --python "$python" --index-url https://download.pytorch.org/whl/cpu \
    --no-deps "$torch_requirement"
grep -v '^torch==' "$output/requirements.txt" > "$output/requirements-rest.txt"
uv pip install --python "$python" --index-url https://pypi.org/simple \
    --no-deps -r "$output/requirements-rest.txt"
uv pip check --python "$python"
uv pip freeze --python "$python" > "$output/installed.txt"
model_source=$(PYTHONPATH="$output/tools" "$python" -c \
    'import bert_train; print(bert_train.REPOSITORY + "/resolve/" + bert_train.REVISION)')
for file in config.json pytorch_model.bin tokenizer_config.json special_tokens_map.json vocab.txt README.md; do
    curl --fail --location --retry 2 --max-time 180 --silent --show-error \
        "https://hf-mirror.com/$model_source/$file" -o "$output/base/$file"
done
"$python" "$output/tools/bert_reproduce.py" converter \
    --archive "$output/converter-source.tgz" --artifacts "$output/original-artifacts.json"
tar -xzf "$output/converter-source.tgz" -C "$output/converter" --no-same-owner
export TOKENIZERS_PARALLELISM=false
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8
"$python" -u "$output/tools/bert_train.py" \
    --base "$output/base" --tasks "$output/tasks.jsonl" --receipt "$output/receipt.json" \
    --regression "$output/regression.json" --output "$output/result"
"$python" "$output/tools/bert_export.py" \
    --encoder "$output/result/encoder" --converter "$output/converter" \
    --output "$output/result/encoder-f32.gguf"
"$python" "$output/tools/bert_reproduce.py" result \
    --result "$output/result" --artifacts "$output/original-artifacts.json" \
    --training "$output/original-training.json" --output "$output/reproduction.json"
