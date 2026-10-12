#!/usr/bin/env bash
# 在服务器共用锁内重放既有完整轨迹。
set -euo pipefail
if [[ -z ${TMUX:-} || $# -lt 1 ]]; then
    echo '必须在 tmux 内提供结果根目录。' >&2
    exit 2
fi
cost_run=$(realpath "$1")
shift
mkdir "$cost_run/host-run"
exec 9>lab/qemu-screen-server.lock
printf '%s\n' waiting-lock > "$cost_run/host-run/phase"
flock 9
cost_finish() {
    cost_status=$?
    printf '%s\n' "$cost_status" > "$cost_run/host-run/exit-status"
    if [[ $cost_status -eq 0 ]]; then
        printf '%s\n' complete > "$cost_run/host-run/phase"
    else
        printf '%s\n' stopped > "$cost_run/host-run/phase"
    fi
    exit "$cost_status"
}
trap cost_finish EXIT
printf '%s\n' "$TMUX" > "$cost_run/host-run/tmux.log"
lscpu > "$cost_run/host-run/topology.log"
taskset -pc $$ > "$cost_run/host-run/affinity.log"
printf '%s\n' running > "$cost_run/host-run/phase"
python3 "$(dirname "$0")/cost-evidence.py" "$@" --output "$cost_run/host-results" > "$cost_run/host-run/driver.log" 2>&1
