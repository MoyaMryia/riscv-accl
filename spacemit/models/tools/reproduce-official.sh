#!/usr/bin/env bash
# 从固定官方检查点生成独立模型产物，并保留加工记录。
set -euo pipefail
if [ "$#" -ne 6 ]; then
  echo "用法：$0 2B或4B 官方检查点目录 转换源码目录 量化器 元数据证据目录 新输出目录" >&2
  exit 2
fi
model_size=$1
case "$model_size" in
  2B) draft_layer=24 ;;
  4B) draft_layer=32 ;;
  *) echo '仅支持 2B 或 4B' >&2; exit 2 ;;
esac
checkpoint_dir=$(realpath "$2")
converter_dir=$(realpath "$3")
quantizer_path=$(realpath "$4")
evidence_dir=$(realpath "$5")
model_output=$6
tool_dir=$(cd "$(dirname "$0")" && pwd)
model_python=${MODEL_PYTHON:-python3}
unset NO_LOCAL_GGUF
export PYTHONNOUSERSITE=1
export PYTHONPATH="$converter_dir:$converter_dir/gguf-py"
test -x "$quantizer_path"
test ! -e "$model_output"
mkdir -p "$model_output"
model_output=$(realpath "$model_output")
exec > "$model_output/driver.log" 2>&1
trap 'run_status=$?; printf "%s\n" "$run_status" > "$model_output/exit-status"' EXIT
set -x
"$model_python" "$tool_dir/record-reproduction.py" snapshot --model "$model_size" \
  --checkpoint "$checkpoint_dir" \
  --metadata "$evidence_dir/Qwen--Qwen3.5-$model_size.api.json" \
  --output "$model_output/input-receipt.json"
"$model_python" "$tool_dir/record-reproduction.py" source --root "$converter_dir" \
  --receipt "$evidence_dir/converter-source-receipt.json" \
  --output "$model_output/source-receipt.json"
"$model_python" -m pip freeze > "$model_output/python-packages.txt"
"$model_python" --version > "$model_output/python-version.txt"
uname -a > "$model_output/host.txt"
"$model_python" "$tool_dir/record-reproduction.py" artifacts \
  "$quantizer_path" "$0" "$tool_dir/record-reproduction.py" \
  "$tool_dir/add-prefix-head.py" --output "$model_output/tool-receipt.json"
# 默认转换保留官方 MTP。此步骤不导出视觉投影器。
"$model_python" "$converter_dir/convert_hf_to_gguf.py" "$checkpoint_dir" \
  --outtype bf16 --outfile "$model_output/official-BF16.gguf" \
  --model-name "Qwen3.5-$model_size-official-MTP" \
  > "$model_output/convert.log" 2>&1
# 官方 BF16 输入只量化一次，不启用重复量化选项。
"$quantizer_path" --token-embedding-type q4_0 --output-tensor-type q4_0 \
  "$model_output/official-BF16.gguf" "$model_output/official-Q4_0-embQ4_0.gguf" Q4_0 \
  > "$model_output/quantize.log" 2>&1
"$model_python" "$tool_dir/add-prefix-head.py" \
  "$model_output/official-Q4_0-embQ4_0.gguf" \
  "$model_output/official-Q4_0-embQ4_0-dv64k.gguf" \
  --layer "$draft_layer" --rows 65536 > "$model_output/pack.log" 2>&1
"$model_python" "$tool_dir/record-reproduction.py" artifacts \
  "$model_output/official-BF16.gguf" "$model_output/official-Q4_0-embQ4_0.gguf" \
  "$model_output/official-Q4_0-embQ4_0-dv64k.gguf" \
  --output "$model_output/output-receipt.json"
"$model_python" "$tool_dir/record-reproduction.py" snapshot --model "$model_size" \
  --checkpoint "$checkpoint_dir" \
  --metadata "$evidence_dir/Qwen--Qwen3.5-$model_size.api.json" \
  --output "$model_output/input-after-receipt.json"
"$model_python" "$tool_dir/record-reproduction.py" source --root "$converter_dir" \
  --receipt "$evidence_dir/converter-source-receipt.json" \
  --output "$model_output/source-after-receipt.json"
# 加工完成后仍需结构、模型推理和匹配性能验收。
printf '%s\n' 'conversion-complete-validation-pending' > "$model_output/phase"
