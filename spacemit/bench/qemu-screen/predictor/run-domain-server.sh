#!/usr/bin/env bash
# 在服务器共用锁内采集固定形状的动态计数。
set -euo pipefail
if [[ $# -ne 2 || -z ${TMUX:-} ]]; then
    echo '必须在 tmux 内提供载荷目录和新结果目录。' >&2
    exit 2
fi
domain_tools=$(cd "$(dirname "$0")" && pwd)
domain_payload=$(realpath "$1")
domain_output=$(realpath -m "$2")
mkdir "$domain_output"
domain_finish() { domain_status=$?; printf '%s\n' "$domain_status" > "$domain_output/exit-status"; exit "$domain_status"; }
trap domain_finish EXIT
exec 9>lab/qemu-screen-server.lock
printf '%s\n' waiting-lock > "$domain_output/phase"
flock 9
source spacemit/bench/qemu-screen/server-env.sh
printf '%s\n' "$TMUX" > "$domain_output/tmux.log"
date -Is > "$domain_output/identity.log"
lscpu > "$domain_output/topology.log"
taskset -pc $$ > "$domain_output/affinity.log"
printf '%s\n' running > "$domain_output/phase"
python3 "$domain_tools/domain-census.py" "$domain_payload" --qemu "$K1_QEMU_PREFIX/bin/qemu-riscv64" \
    --header "$K1_QEMU_PREFIX/include/qemu-plugin.h" --output "$domain_output/result" > "$domain_output/driver.log" 2>&1
printf '%s\n' complete > "$domain_output/phase"
