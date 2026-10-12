#!/usr/bin/env bash
# 在 tmux 内持有服务器共用锁。
set -euo pipefail
if [[ $# -ne 2 || -z ${TMUX:-} ]]; then
    echo '必须在 tmux 内提供载荷目录和新结果目录。' >&2
    exit 2
fi
load_dir=$(cd "$(dirname "$0")" && pwd)
load_payload=$(realpath "$1")
load_output=$(realpath -m "$2")
mkdir "$load_output"
load_finish() {
    load_status=$?
    printf '%s\n' "$load_status" > "$load_output/exit-status"
    exit "$load_status"
}
trap load_finish EXIT
exec 9>lab/qemu-screen-server.lock
printf '%s\n' waiting-lock > "$load_output/phase"
flock 9
date -Is > "$load_output/identity.log"
lscpu > "$load_output/topology.log"
printf '%s\n' "$TMUX" > "$load_output/tmux.log"
source spacemit/bench/qemu-screen/server-env.sh
printf '%s\n' running > "$load_output/phase"
python3 "$load_dir/load-use-trace.py" "$load_payload" --qemu "$K1_QEMU_PREFIX/bin/qemu-riscv64" \
    --plugin lab/k1-matched-umode-results-v3/result/trace.so \
    --profiles "$load_dir/profiles/k1-cpu0-umode-20261012/components.json" \
    "$load_dir/profiles/k1-cpu0-umode-20261012/ime.json" \
    "$load_dir/profiles/k1-cpu0-umode-20261012/reductions.json" \
    "$load_dir/profiles/k1-cpu0-umode-20261012/scalar.json" \
    "$load_dir/profiles/k1-cpu0-umode-20261012/gaps.json" \
    --output "$load_output/result" > "$load_output/driver.log" 2>&1
printf '%s\n' complete > "$load_output/phase"
