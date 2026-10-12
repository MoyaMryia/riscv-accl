#!/usr/bin/env bash
# 在服务器共用锁内重放已经核验的配对轨迹。
set -euo pipefail
if [[ $# -ne 2 || -z ${TMUX:-} ]]; then
    echo '必须在 tmux 内提供轨迹目录和新结果目录。' >&2
    exit 2
fi
replay_tools=$(cd "$(dirname "$0")" && pwd)
replay_source=$(realpath "$1")
replay_output=$(realpath -m "$2")
mkdir "$replay_output"
replay_finish() { replay_status=$?; printf '%s\n' "$replay_status" > "$replay_output/exit-status"; exit "$replay_status"; }
trap replay_finish EXIT
exec 9>lab/qemu-screen-server.lock
printf '%s\n' waiting-lock > "$replay_output/phase"
flock 9
date -Is > "$replay_output/identity.log"
printf '%s\n' "$TMUX" > "$replay_output/tmux.log"
lscpu > "$replay_output/topology.log"
taskset -pc $$ > "$replay_output/affinity.log"
printf '%s\n' running > "$replay_output/phase"
python3 "$replay_tools/replay-matched-cost.py" "$replay_source" \
    --profiles "$replay_tools/profiles/k1-cpu0-umode-20261012/components.json" \
    "$replay_tools/profiles/k1-cpu0-umode-20261012/ime.json" \
    "$replay_tools/profiles/k1-cpu0-umode-20261012/reductions.json" \
    "$replay_tools/profiles/k1-cpu0-umode-20261012/scalar.json" \
    "$replay_tools/profiles/k1-cpu0-umode-20261012/gaps.json" \
    --output "$replay_output/result" > "$replay_output/driver.log" 2>&1
printf '%s\n' complete > "$replay_output/phase"
