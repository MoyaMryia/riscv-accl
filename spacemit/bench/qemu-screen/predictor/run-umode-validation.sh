#!/usr/bin/env bash
# 在服务器共用锁内检查修复后的周期模型。
set -euo pipefail
if [[ $# -ne 3 || -z ${TMUX:-} ]]; then
    echo '必须在 tmux 内提供载荷、插件和新结果目录。' >&2
    exit 2
fi
validation_tools=$(cd "$(dirname "$0")" && pwd)
validation_payload=$(realpath "$1")
validation_plugin=$(realpath "$2")
validation_output=$(realpath -m "$3")
mkdir "$validation_output"
validation_finish() { validation_status=$?; printf '%s\n' "$validation_status" > "$validation_output/exit-status"; exit "$validation_status"; }
trap validation_finish EXIT
exec 9>lab/qemu-screen-server.lock
printf '%s\n' waiting-lock > "$validation_output/phase"
flock 9
source spacemit/bench/qemu-screen/server-env.sh
date -Is > "$validation_output/identity.log"
printf '%s\n' "$TMUX" > "$validation_output/tmux.log"
lscpu > "$validation_output/topology.log"
taskset -pc $$ > "$validation_output/affinity.log"
printf '%s\n' running > "$validation_output/phase"
python3 "$validation_tools/validate-cost.py" "$validation_payload" \
    --samples "$validation_payload/native-samples.jsonl" --qemu "$K1_QEMU_PREFIX/bin/qemu-riscv64" \
    --plugin "$validation_plugin" --profiles "$validation_tools/profiles/k1-cpu0-umode-20261012/components.json" \
    "$validation_tools/profiles/k1-cpu0-umode-20261012/ime.json" \
    "$validation_tools/profiles/k1-cpu0-umode-20261012/reductions.json" \
    "$validation_tools/profiles/k1-cpu0-umode-20261012/scalar.json" \
    "$validation_tools/profiles/k1-cpu0-umode-20261012/gaps.json" \
    --output "$validation_output/result" > "$validation_output/driver.log" 2>&1
printf '%s\n' complete > "$validation_output/phase"
