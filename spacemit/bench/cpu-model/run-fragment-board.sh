#!/bin/bash
# 在 K1 共用锁内完成有限片段数值与配对性能检查。
set -euo pipefail
if [[ $# -ne 1 || -z ${TMUX:-} ]]; then exit 2; fi
fragment_payload=$(realpath "$1")
fragment_run="$fragment_payload/../native"
mkdir "$fragment_run"
fragment_finish() {
    fragment_status=$?
    printf '%s\n' "$fragment_status" > "$fragment_run/exit-status"
    date -Is > "$fragment_run/end-time"
    (cd "$fragment_run"; find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS)
    exit "$fragment_status"
}
trap fragment_finish EXIT
exec 9>/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock
flock -n 9
cd "$fragment_payload"
sha256sum -c SHA256SUMS > "$fragment_run/input-check.log"
date -Is > "$fragment_run/start-time"
printf '%s\n' "$TMUX" > "$fragment_run/tmux.txt"
ps -eo pid,comm,pcpu,args > "$fragment_run/tasks-before.txt"
uname -a > "$fragment_run/kernel.txt"
mkdir "$fragment_run/dumps"
timeout 60 ./fragment check-all "$fragment_run/dumps" > "$fragment_run/numerical.log" 2>&1
for fragment_session in 0 1; do
    date -Is > "$fragment_run/session-$fragment_session-start"
    timeout 180 sudo -n ./fragment bench > "$fragment_run/samples-$fragment_session.jsonl" 2> "$fragment_run/bench-$fragment_session.log"
done
ps -eo pid,comm,pcpu,args > "$fragment_run/tasks-after.txt"
