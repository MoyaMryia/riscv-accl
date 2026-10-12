#!/usr/bin/env bash
# 在 tmux 内持有服务器共用锁。
set -euo pipefail
if [[ $# -ne 2 || -z ${TMUX:-} ]]; then
    echo '必须在 tmux 内提供源结果目录和新输出目录。' >&2
    exit 2
fi
explain_dir=$(cd "$(dirname "$0")" && pwd)
explain_source=$(realpath "$1")
explain_output=$(realpath -m "$2")
mkdir "$explain_output"
explain_finish() {
    explain_status=$?
    printf '%s\n' "$explain_status" > "$explain_output/exit-status"
    exit "$explain_status"
}
trap explain_finish EXIT
exec 9>lab/qemu-screen-server.lock
printf '%s\n' waiting-lock > "$explain_output/phase"
flock 9
date -Is > "$explain_output/identity.log"
lscpu > "$explain_output/topology.log"
taskset -pc $$ > "$explain_output/affinity.log"
printf '%s\n' "$TMUX" > "$explain_output/tmux.log"
printf '%s\n' running > "$explain_output/phase"
python3 "$explain_dir/explain-suite.py" "$explain_source" \
    --profiles "$explain_dir/profiles/k1-cpu0-umode-20261012/components.json" \
    "$explain_dir/profiles/k1-cpu0-umode-20261012/ime.json" \
    "$explain_dir/profiles/k1-cpu0-umode-20261012/reductions.json" \
    "$explain_dir/profiles/k1-cpu0-umode-20261012/scalar.json" \
    "$explain_dir/profiles/k1-cpu0-umode-20261012/gaps.json" \
    --output "$explain_output/result" > "$explain_output/driver.log" 2>&1
printf '%s\n' complete > "$explain_output/phase"
