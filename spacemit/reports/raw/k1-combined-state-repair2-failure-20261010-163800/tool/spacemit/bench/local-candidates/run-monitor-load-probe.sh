#!/usr/bin/env bash
set -eu
base=/home/moyamryia/Projects/riscv-accl-bench-2026-09-27
out=$1
exec 9>"$base/document-quality-suite.lock"
flock -x 9
mkdir -p "$out"
exec >"$out/driver.log" 2>&1
trap 'printf "%s\n" "$?" >"$out/exit-status"' EXIT
cd "$out"
date --iso-8601=seconds >start-clock.log
lslocks >locks.log
tmux list-sessions >sessions.log
cp "$base/monitor-load-probe.c" "$base/monitor-load-probe.S" .
printf 'build fixed load probe\n' >phase
cc --version >compiler-version.log
cc -O2 -g -march=rv64gc -mabi=lp64d monitor-load-probe.c monitor-load-probe.S -o monitor-load-probe >build.log 2>&1
objdump -d monitor-load-probe >disassembly.log
sha256sum monitor-load-probe.c monitor-load-probe.S monitor-load-probe /usr/lib/riscv64-linux-gnu/libc.so.6 >identities.sha256
for cpu in $(seq 0 7); do
    printf 'fixed load probe CPU %s\n' "$cpu" >phase
    cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq /sys/class/thermal/thermal_zone*/temp >"cpu-$cpu-state.log"
    set +e
    timeout 120 taskset -c "$cpu" ./monitor-load-probe >"cpu-$cpu.log" 2>&1
    result=$?
    set -e
    printf '%s %s\n' "$cpu" "$result" >>results.log
    if [ "$result" -ne 0 ]; then exit "$result"; fi
done
journalctl -k --no-pager --since '2026-10-09 22:23:00' >kernel-after.log
sha256sum -c identities.sha256 >identity-check.log
date --iso-8601=seconds >end-clock.log
printf 'fixed load probe complete\n' >phase
