#!/usr/bin/env bash
# 在 tmux 内持有板端共用锁。
set -euo pipefail
if [[ $# -ne 1 || -z ${TMUX:-} ]]; then
    echo '必须在 tmux 内提供新载荷目录。' >&2
    exit 2
fi
matched_payload=$(realpath "$1")
mkdir "$matched_payload/run"
matched_finish() {
    matched_status=$?
    printf '%s\n' "$matched_status" > "$matched_payload/run/exit-status"
    cd "$matched_payload"
    find run -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > run/SHA256SUMS
    exit "$matched_status"
}
trap matched_finish EXIT
exec 9>/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock
printf '%s\n' waiting-lock > "$matched_payload/run/phase"
flock 9
cd "$matched_payload"
sha256sum -c SHA256SUMS > run/input-check.log 2>&1
printf '%s\n' running > run/phase
date -Is > run/identity.log
uname -a >> run/identity.log
printf '%s\n' "$TMUX" > run/tmux.log
cat /sys/class/thermal/thermal_zone*/temp > run/temperature-before.log
for matched_shape in '6144 8' '8192 8' '6144 32' '8192 32'; do
    read -r matched_channels matched_tokens <<< "$matched_shape"
    matched_id="C$matched_channels-T$matched_tokens"
    for matched_mode in bench bench-roi; do
        timeout 120 ./matched "$matched_mode" "$matched_channels" "$matched_tokens" 7 "run/$matched_id-$matched_mode.bin" > "run/$matched_id-$matched_mode.jsonl" 2> "run/$matched_id-$matched_mode.log"
    done
done
cat /sys/class/thermal/thermal_zone*/temp > run/temperature-after.log
printf '%s\n' complete > run/phase
