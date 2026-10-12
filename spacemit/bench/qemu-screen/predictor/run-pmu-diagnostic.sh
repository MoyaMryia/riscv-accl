#!/usr/bin/env bash
# 采集原始 PMU 事件，并全程持有板端共用锁。
set -euo pipefail
if [[ $# -ne 1 || -z ${TMUX:-} ]]; then
    echo '必须在 tmux 内提供新载荷目录。' >&2
    exit 2
fi
pmu_payload=$(realpath "$1")
mkdir "$pmu_payload/run"
pmu_finish() {
    pmu_status=$?
    printf '%s\n' "$pmu_status" > "$pmu_payload/run/exit-status"
    cd "$pmu_payload"
    find run -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > run/SHA256SUMS
    exit "$pmu_status"
}
trap pmu_finish EXIT
exec 9>/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock
printf '%s\n' waiting-lock > "$pmu_payload/run/phase"
flock 9
cd "$pmu_payload"
sha256sum -c SHA256SUMS > run/input-check.log 2>&1
date -Is > run/identity.log
uname -a >> run/identity.log
perf --version >> run/identity.log
printf '%s\n' "$TMUX" > run/tmux.log
cat /sys/class/thermal/thermal_zone*/temp > run/temperature-before.log
for pmu_shape in '6144 8' '8192 8' '6144 32' '8192 32'; do
    read -r pmu_channels pmu_tokens <<< "$pmu_shape"
    pmu_id="C$pmu_channels-T$pmu_tokens"
    printf '%s\n' "$pmu_id" > run/phase
    timeout 120 perf stat --no-big-num -x ';' \
        -e r22:u,r3:u,r4:u,r64:u,raa:u,rab:u,rb8:u,rb9:u,r81:u,r85:u \
        -o "run/$pmu_id-pmu.csv" -- ./matched bench "$pmu_channels" "$pmu_tokens" 2 "run/$pmu_id.bin" \
        > "run/$pmu_id.jsonl" 2> "run/$pmu_id.log"
done
cat /sys/class/thermal/thermal_zone*/temp > run/temperature-after.log
printf '%s\n' complete > run/phase
