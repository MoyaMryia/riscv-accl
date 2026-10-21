#!/usr/bin/env bash
# 冻结长上下文自然回答任务，不生成模型或启动推理。
# 用法：stage-long-context.sh 新任务目录 案例JSON
set -euo pipefail
if [ "$#" -ne 2 ]; then
    echo '用法：stage-long-context.sh 新任务目录 案例JSON' >&2
    exit 2
fi
job=$1
cases=$2
test ! -e "$job"
test -f "$cases"
repo=$(cd "$(dirname "$0")/../../.." && pwd)
tools="$repo/spacemit/bench/mtp-r3"
mkdir -p "$job"
export PYTHONDONTWRITEBYTECODE=1
cp "$tools"/{long_context_cases.py,long_context_batch.py,diagnostic.py,repetition_guard.py} "$job"/
cp "$tools"/{batch_controller.py,multi_turn_batch.py,multi_turn_suite.py,multi_turn_cases.py,local_multi_turn_replay.py} "$job"/
cp "$tools"/test_{long_context_cases,long_context_batch,batch_controller,multi_turn_batch}.py "$job"/
cp "$repo/spacemit/serve/cached-document-chat.py" "$job/chat.py"
cp "$repo/spacemit/release-candidate/tests/quality.py" "$job/quality.py"
cp "$repo/spacemit/bench/final-default/effective.py" "$job/effective.py"
cp "$repo/spacemit/experiments/2026-10-21-long-context-natural.md" "$job/PROTOCOL.md"
cp "$cases" "$job/cases.json"
python3 - "$job" <<'PY'
import hashlib
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
sys.path.insert(0, str(root))
import long_context_cases

cases = long_context_cases.read_cases(root / 'cases.json')
names = {'diagnostic': 'diagnostic.py', 'chat': 'chat.py', 'quality': 'quality.py',
         'effective': 'effective.py', 'long_context_batch': 'long_context_batch.py',
         'long_context_cases': 'long_context_cases.py'}
receipt = {key: hashlib.sha256((root / name).read_bytes()).hexdigest() for key, name in names.items()}
with (root / 'tools.json').open('x') as stream:
    json.dump(receipt, stream, indent=2)
    stream.write('\n')
frozen = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(root.glob('*.py'))}
with (root / 'frozen-tools.json').open('x') as stream:
    json.dump(frozen, stream, indent=2)
    stream.write('\n')
print('FROZEN_CASES', [(case['case_id'], case['local_token_count']) for case in cases])
PY
printf '%s\n' '#!/usr/bin/env bash' 'set -euo pipefail' 'cd "$(dirname "$0")"' \
    'exec >run.log 2>&1' "trap 'rc=\$?; printf \"%s\\n\" \"\$rc\" > exit-status' EXIT" \
    'export PYTHONDONTWRITEBYTECODE=1' > "$job/launch.sh"
python3 - "$job/launch.sh" <<'PY'
from pathlib import Path
import sys

script = '''python3 - "$PWD" <<'RUNTIME'
import json
from pathlib import Path
import sys
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
}
with (Path(sys.argv[1]) / 'runtime.json').open('x') as stream:
    json.dump(runtime, stream, indent=2)
    stream.write('\\n')
RUNTIME
python3 -u long_context_batch.py --job "$PWD" --runtime "$PWD/runtime.json" --models 2B 4B
'''
with Path(sys.argv[1]).open('a') as stream:
    stream.write(script)
PY
chmod +x "$job/launch.sh"
echo "STAGED $job models=2B,4B requests=12"
