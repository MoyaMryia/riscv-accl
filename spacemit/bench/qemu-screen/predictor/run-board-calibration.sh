#!/usr/bin/env bash
# 在 tmux 内全程持有板端共用锁。
set -euo pipefail
if [[ $# -ne 1 || -z ${TMUX:-} ]]; then
    echo '必须在 tmux 内提供冻结载荷目录。' >&2
    exit 2
fi
predictor_payload=$(realpath "$1")
predictor_lock=/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock
mkdir "$predictor_payload/run"
predictor_finish() {
    predictor_status=$?
    printf '%s\n' "$predictor_status" > "$predictor_payload/run/exit-status"
    if [[ $predictor_status -eq 0 ]]; then
        printf '%s\n' complete > "$predictor_payload/run/phase"
    else
        printf '%s\n' stopped > "$predictor_payload/run/phase"
    fi
    cd "$predictor_payload"
    find run -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > run/SHA256SUMS
    exit "$predictor_status"
}
trap predictor_finish EXIT
printf '%s\n' "$TMUX" > "$predictor_payload/run/tmux.log"
exec 9>"$predictor_lock"
printf '%s\n' waiting-lock > "$predictor_payload/run/phase"
flock 9
cd "$predictor_payload"
set +e
sha256sum -c SHA256SUMS > run/input-check.log 2>&1
predictor_status=$?
if [[ $predictor_status -eq 0 ]]; then
    sha256sum -c BINARY-SHA256SUMS >> run/input-check.log 2>&1
    predictor_status=$?
fi
if [[ $predictor_status -eq 0 ]]; then
    printf '%s\n' running > run/phase
    date -Is > run/identity.log
    uname -a >> run/identity.log
    objdump -d measure > run/actual.asm
    cat /sys/class/thermal/thermal_zone*/temp > run/temperature-before.log
    timeout 60 ./measure > run/samples.jsonl 2>run/measure-error.log
    predictor_status=$?
    cat /sys/class/thermal/thermal_zone*/temp > run/temperature-after.log
fi
exit "$predictor_status"
