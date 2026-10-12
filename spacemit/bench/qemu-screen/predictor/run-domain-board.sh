#!/usr/bin/env bash
# 分组执行同一程序，并全程持有板端共用锁。
set -euo pipefail
if [[ $# -ne 2 || -z ${TMUX:-} ]]; then
    echo '必须在 tmux 内提供载荷目录和分组。' >&2
    exit 2
fi
domain_payload=$(realpath "$1")
domain_stage=$2
case "$domain_stage" in training|calibration|test) ;; *) exit 2 ;; esac
domain_run="run-$domain_stage"
mkdir "$domain_payload/$domain_run"
domain_finish() {
    domain_status=$?
    printf '%s\n' "$domain_status" > "$domain_payload/$domain_run/exit-status"
    cd "$domain_payload"
    find "$domain_run" -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > "$domain_run/SHA256SUMS"
    exit "$domain_status"
}
trap domain_finish EXIT
exec 9>/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock
printf '%s\n' waiting-lock > "$domain_payload/$domain_run/phase"
flock 9
cd "$domain_payload"
sha256sum -c SHA256SUMS > "$domain_run/input-check.log" 2>&1
date -Is > "$domain_run/identity.log"
uname -a >> "$domain_run/identity.log"
printf '%s\n' "$TMUX" > "$domain_run/tmux.log"
cat /sys/class/thermal/thermal_zone*/temp > "$domain_run/temperature-before.log"
while read -r domain_channels domain_tokens domain_split; do
    [[ "$domain_split" == "$domain_stage" ]] || continue
    printf '%s\n' "$domain_split C$domain_channels-T$domain_tokens" > "$domain_run/phase"
    domain_id="C$domain_channels-T$domain_tokens"
    timeout 120 ./matched bench "$domain_channels" "$domain_tokens" 7 "$domain_run/$domain_id.bin" > "$domain_run/$domain_id.jsonl" 2> "$domain_run/$domain_id.log"
done < workloads.tsv
cat /sys/class/thermal/thermal_zone*/temp > "$domain_run/temperature-after.log"
printf '%s\n' complete > "$domain_run/phase"
