#!/usr/bin/env bash
# 生成固定多轮任务目录：复制工具、写入收据与启动脚本。
# 用法：stage-multi-turn.sh JOB_DIR 2B或4B
set -euo pipefail
if [ "$#" -ne 2 ]; then
    echo '用法：stage-multi-turn.sh JOB_DIR 2B或4B' >&2
    exit 2
fi
job=$1
model=$2
case "$model" in
    2B|4B) ;;
    *) echo '型号只支持 2B 或 4B。' >&2; exit 2 ;;
esac
test ! -e "$job"
repo=$(cd "$(dirname "$0")/../../.." && pwd)
tools="$repo/spacemit/bench/mtp-r3"
mkdir -p "$job"
export PYTHONDONTWRITEBYTECODE=1
cp "$tools"/{diagnostic.py,repetition_guard.py,multi_turn_suite.py,multi_turn_cases.py} "$job"/
cp "$repo/spacemit/serve/cached-document-chat.py" "$job/chat.py"
cp "$repo/spacemit/release-candidate/tests/quality.py" "$job/quality.py"
cp "$repo/spacemit/bench/final-default/effective.py" "$job/effective.py"
cp "$tools/run-board.sh" "$job/run-board.sh"
python3 - "$job" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

job = Path(sys.argv[1])
names = {'diagnostic': 'diagnostic.py', 'suite': 'multi_turn_suite.py',
         'assessment': 'multi_turn_cases.py', 'chat': 'chat.py',
         'quality': 'quality.py', 'effective': 'effective.py'}
receipt = {key: hashlib.sha256((job / name).read_bytes()).hexdigest()
           for key, name in names.items()}
(job / 'tools.json').write_text(json.dumps(receipt, indent=1, sort_keys=True) + '\n')
sys.path.insert(0, str(job))
import multi_turn_cases  # noqa: E402  (从任务目录读取冻结题集)

cases = multi_turn_cases.read_cases()
(job / 'cases.json').write_text(json.dumps(cases, ensure_ascii=False, indent=1) + '\n')
print('PLANNED_TURNS', multi_turn_cases.planned_turns(cases))
PY
cat > "$job/launch.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
base="$HOME/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1/final-r3"
exec bash run-board.sh "$PWD" "$base/build/bin/llama-server" \
    "$HOME/Projects/spacemit-llama/models" \
    "$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2" \
    "$HOME/Projects/llm-bench/.toolchain/spine-tcm" \
    "$base/package/manifest.json" "$base/build/build-receipt.json" "$MODEL" multi_turn
SH
sed -i "s/\$MODEL/$model/" "$job/launch.sh"
chmod +x "$job/launch.sh"
echo "STAGED $job model=$model"
