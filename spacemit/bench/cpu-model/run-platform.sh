#!/usr/bin/env bash
# 在共用锁内记录每核扩展与平台快照。
set -euo pipefail
if [[ $# -ne 1 || -z ${TMUX:-} ]]; then
    echo '必须在 tmux 内提供载荷目录。' >&2
    exit 2
fi
cpu_platform=$(realpath "$1")
cd "$cpu_platform"
mkdir run
cpu_finish() {
    cpu_status=$?
    printf '%s\n' "$cpu_status" > run/exit-status
    find run -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > run/SHA256SUMS
    exit "$cpu_status"
}
trap cpu_finish EXIT
exec 9>/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock
printf '%s\n' waiting-lock > run/phase
flock 9
sha256sum -c SHA256SUMS > run/input-check.log 2>&1
date -Is > run/start-time
printf '%s\n' "$TMUX" > run/tmux.txt
python3 platform.py --probe core-probe --output run/platform > run/driver.log 2>&1
date -Is > run/end-time
printf '%s\n' complete > run/phase
