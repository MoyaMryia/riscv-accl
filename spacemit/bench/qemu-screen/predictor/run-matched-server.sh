#!/usr/bin/env bash
# 在 tmux 内持有服务器共用锁。
set -euo pipefail
if [[ $# -ne 2 || -z ${TMUX:-} ]]; then
    echo '必须在 tmux 内提供载荷目录和新结果目录。' >&2
    exit 2
fi
matched_dir=$(cd "$(dirname "$0")" && pwd)
matched_payload=$(realpath "$1")
matched_output=$(realpath -m "$2")
mkdir "$matched_output"
matched_finish() {
    matched_status=$?
    printf '%s\n' "$matched_status" > "$matched_output/exit-status"
    exit "$matched_status"
}
trap matched_finish EXIT
exec 9>lab/qemu-screen-server.lock
printf '%s\n' waiting-lock > "$matched_output/phase"
flock 9
date -Is > "$matched_output/identity.log"
lscpu > "$matched_output/topology.log"
taskset -pc $$ > "$matched_output/affinity.log"
printf '%s\n' "$TMUX" > "$matched_output/tmux.log"
source spacemit/bench/qemu-screen/server-env.sh
printf '%s\n' running > "$matched_output/phase"
python3 "$matched_dir/matched-trace.py" "$matched_payload" --qemu "$K1_QEMU_PREFIX/bin/qemu-riscv64" \
    --header "$K1_QEMU_PREFIX/include/qemu-plugin.h" \
    --profiles "$matched_dir/profiles/k1-cpu0-umode-20261012/components.json" \
    "$matched_dir/profiles/k1-cpu0-umode-20261012/ime.json" \
    "$matched_dir/profiles/k1-cpu0-umode-20261012/reductions.json" \
    "$matched_dir/profiles/k1-cpu0-umode-20261012/scalar.json" \
    "$matched_dir/profiles/k1-cpu0-umode-20261012/gaps.json" \
    --output "$matched_output/result" > "$matched_output/driver.log" 2>&1
printf '%s\n' complete > "$matched_output/phase"
