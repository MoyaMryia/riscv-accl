#!/usr/bin/env bash
# 在板端共用锁内执行新的 CPU 模型实验。
set -euo pipefail
if [[ $# -ne 2 || -z ${TMUX:-} || ! $2 =~ ^(training|calibration|test)$ ]]; then
    echo '必须在 tmux 内提供载荷目录与阶段。' >&2
    exit 2
fi
cpu_payload=$(realpath "$1")
cpu_stage=$2
cd "$cpu_payload"
if [[ $cpu_stage != training ]]; then test -s frozen-model.json; fi
if [[ $cpu_stage == test ]]; then test -s frozen-calibration.json; fi
mkdir "run-$cpu_stage"
cpu_finish() {
    cpu_status=$?
    printf '%s\n' "$cpu_status" > "run-$cpu_stage/exit-status"
    find "run-$cpu_stage" -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > "run-$cpu_stage/SHA256SUMS"
    exit "$cpu_status"
}
trap cpu_finish EXIT
exec 9>/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock
printf '%s\n' waiting-lock > "run-$cpu_stage/phase"
flock 9
sha256sum -c SHA256SUMS > "run-$cpu_stage/input-check.log" 2>&1
if [[ $cpu_stage != training ]]; then cp frozen-model.json "run-$cpu_stage/"; fi
if [[ $cpu_stage == test ]]; then cp frozen-calibration.json "run-$cpu_stage/"; fi
date -Is > "run-$cpu_stage/start-time"
uname -a > "run-$cpu_stage/kernel.txt"
lscpu > "run-$cpu_stage/lscpu.txt"
cat /proc/cpuinfo > "run-$cpu_stage/cpuinfo.txt"
cat /proc/interrupts > "run-$cpu_stage/interrupts-before.txt"
ps -eo pid,comm,pcpu,args > "run-$cpu_stage/tasks-before.txt"
find /sys/devices/system/cpu/cpu*/cache -name shared_cpu_list -o -name size -o -name coherency_line_size -o -name ways_of_associativity | sort | while read -r cpu_file; do
    printf '%s ' "$cpu_file"; cat "$cpu_file"
done > "run-$cpu_stage/cache-topology.txt"
find /sys/devices/system/cpu/cpufreq /sys/class/thermal -maxdepth 3 -type f \( -name scaling_cur_freq -o -name scaling_governor -o -name temp -o -name type \) -print 2>/dev/null | sort | while read -r cpu_file; do
    printf '%s ' "$cpu_file"; cat "$cpu_file"
done > "run-$cpu_stage/environment-before.txt"
printf '%s\n' "$TMUX" > "run-$cpu_stage/tmux.txt"
if [[ $cpu_stage == training ]]; then
    timeout 120 sudo -n ./counter-audit --all-modes > "run-$cpu_stage/counter-audit.jsonl" 2> "run-$cpu_stage/counter-audit.log"
fi
mkdir "run-$cpu_stage/dumps"
timeout 120 sudo -n ./measure check "$cpu_stage" "run-$cpu_stage/dumps" > "run-$cpu_stage/check.log" 2>&1
printf '%s\n' running > "run-$cpu_stage/phase"
for cpu_session in 0 1; do
    date -Is > "run-$cpu_stage/session-$cpu_session-start"
    timeout 1200 sudo -n ./measure bench "$cpu_stage" > "run-$cpu_stage/samples-$cpu_session.jsonl" 2> "run-$cpu_stage/measure-$cpu_session.log"
done
cat /proc/interrupts > "run-$cpu_stage/interrupts-after.txt"
ps -eo pid,comm,pcpu,args > "run-$cpu_stage/tasks-after.txt"
date -Is > "run-$cpu_stage/end-time"
printf '%s\n' complete > "run-$cpu_stage/phase"
