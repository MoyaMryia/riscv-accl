#!/usr/bin/env bash
# 在服务器共用锁内执行共享缓存诊断。
set -euo pipefail
if [[ $# -ne 2 || -z ${TMUX:-} ]]; then
    echo '必须在 tmux 内提供轨迹目录和新结果目录。' >&2
    exit 2
fi
shared_tools=$(cd "$(dirname "$0")" && pwd)
shared_source=$(realpath "$1")
shared_output=$(realpath -m "$2")
mkdir "$shared_output"
shared_finish() { shared_status=$?; printf '%s\n' "$shared_status" > "$shared_output/exit-status"; exit "$shared_status"; }
trap shared_finish EXIT
exec 9>lab/qemu-screen-server.lock
printf '%s\n' waiting-lock > "$shared_output/phase"
flock 9
date -Is > "$shared_output/identity.log"
printf '%s\n' "$TMUX" > "$shared_output/tmux.log"
lscpu > "$shared_output/topology.log"
taskset -pc $$ > "$shared_output/affinity.log"
printf '%s\n' running > "$shared_output/phase"
python3 "$shared_tools/shared-cache-suite.py" "$shared_source" --output "$shared_output/result" > "$shared_output/driver.log" 2>&1
printf '%s\n' complete > "$shared_output/phase"
