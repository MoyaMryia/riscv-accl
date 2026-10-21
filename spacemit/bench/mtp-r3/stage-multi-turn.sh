#!/usr/bin/env bash
# 生成固定多轮任务目录：复制工具、写入收据与启动脚本。
# 用法：stage-multi-turn.sh JOB_DIR 2B或4B或both
set -euo pipefail
if [ "$#" -ne 2 ]; then
    echo '用法：stage-multi-turn.sh JOB_DIR 2B或4B或both' >&2
    exit 2
fi
job=$1
model=$2
case "$model" in
    2B|4B|both) ;;
    *) echo '型号只支持 2B、4B 或 both。' >&2; exit 2 ;;
esac
test ! -e "$job"
repo=$(cd "$(dirname "$0")/../../.." && pwd)
tools="$repo/spacemit/bench/mtp-r3"
mkdir -p "$job"
export PYTHONDONTWRITEBYTECODE=1
cp "$tools"/{diagnostic.py,repetition_guard.py,multi_turn_suite.py,multi_turn_cases.py} "$job"/
cp "$tools"/{batch_controller.py,multi_turn_batch.py} "$job"/
cp "$tools"/test_{multi_turn_batch,multi_turn_suite,multi_turn_cases,batch_controller}.py "$job"/
cp "$repo/spacemit/serve/cached-document-chat.py" "$job/chat.py"
cp "$repo/spacemit/release-candidate/tests/quality.py" "$job/quality.py"
cp "$repo/spacemit/bench/final-default/effective.py" "$job/effective.py"
cp "$tools/run-board.sh" "$job/run-board.sh"
cp "$repo/spacemit/experiments/2026-10-21-fixed-multi-turn-v2.md" "$job/PROTOCOL.md"
python3 - "$job" "$repo" <<'PY'
import hashlib
import json
import shutil
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
source = Path(sys.argv[2]) / 'spacemit/reports/raw/delivery-multiturn-20261021-115000-r2'
fixtures = [source / 'cases.json', source / 'multi_turn_cases.py',
            *sorted(source.glob('batch/attempts/*/result/conversations/*/turn-*/answer.txt'))]
fixture_hashes = {}
for path in fixtures:
    target = job / 'fixtures/v1' / path.relative_to(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, target)
    fixture_hashes[str(target.relative_to(job))] = hashlib.sha256(target.read_bytes()).hexdigest()
(job / 'frozen-fixtures.json').write_text(json.dumps(fixture_hashes, indent=1) + '\n')
frozen = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
          for path in sorted(job.glob('*.py'))}
(job / 'frozen-tools.json').write_text(json.dumps(frozen, indent=1) + '\n')
print('PLANNED_TURNS_PER_MODEL', multi_turn_cases.planned_turns(cases))
PY
cat > "$job/launch.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
exec >run.log 2>&1
trap 'rc=$?; printf "%s\n" "$rc" > exit-status' EXIT
case "$MODEL" in
    both) models=(2B 4B) ;;
    *) models=("$MODEL") ;;
esac
python3 - "$PWD" <<'PY'
import json
import sys
from pathlib import Path

home = Path.home()
bench = home / 'Projects/riscv-accl-bench-2026-09-27'
base = bench / 'k1-final-default-20261013-r1/final-r3'
runtime = {
    'server': str(base / 'build/bin/llama-server'),
    'models': str(home / 'Projects/spacemit-llama/models'),
    'spert': str(home / 'Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2'),
    'tcm': str(home / 'Projects/llm-bench/.toolchain/spine-tcm'),
    'manifest': str(base / 'package/manifest.json'),
    'build_receipt': str(base / 'build/build-receipt.json'),
    'lock': str(bench / 'document-quality-suite.lock'),
    'turn_timeout_s': 900,
}
with (Path(sys.argv[1]) / 'runtime.json').open('x') as output:
    output.write(json.dumps(runtime, indent=2) + '\n')
PY
python3 -u multi_turn_batch.py --job "$PWD" --runtime "$PWD/runtime.json" --models "${models[@]}"
SH
sed -i "s/\$MODEL/$model/" "$job/launch.sh"
chmod +x "$job/launch.sh"
echo "STAGED $job model=$model"
