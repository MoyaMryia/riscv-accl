#!/usr/bin/env bash
# 在现有 tmux 中持锁运行短筛选。
set -euo pipefail
if [[ $# -ne 2 || -z ${TMUX:-} ]]; then
    echo 'usage inside tmux: bash run-board.sh PAYLOAD EXPECTED_PROVENANCE' >&2
    exit 2
fi
screen_root=$(realpath "$1")
screen_provenance=$(realpath "$2")
screen_lock=/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock
if [[ -e "$screen_root/run" ]]; then
    echo 'run directory exists' >&2
    exit 2
fi
mkdir "$screen_root/run"
exec 9>"$screen_lock"
printf '%s\n' 'waiting-lock' > "$screen_root/run/phase"
flock 9
set +e
timeout --signal=TERM --kill-after=30s 1800s \
    python3 "$screen_root/run.py" "$screen_root" "$screen_provenance" \
    > "$screen_root/run/driver.log" 2>&1
screen_status=$?
printf '%s\n' "$screen_status" > "$screen_root/run/exit-status"
if [[ $screen_status -ne 0 ]]; then
    printf '%s\n' 'stopped' > "$screen_root/run/phase"
fi
cd "$screen_root/run"
find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
exit "$screen_status"
