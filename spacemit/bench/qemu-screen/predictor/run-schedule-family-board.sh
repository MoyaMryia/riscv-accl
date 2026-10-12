#!/usr/bin/env bash
# 在 tmux 内持有板端共用锁。
set -euo pipefail
if [[ $# -ne 2 || -z ${TMUX:-} || ! $2 =~ ^(training|calibration|test)$ ]]; then
    echo '必须在 tmux 内提供载荷目录和阶段。' >&2
    exit 2
fi
load_payload=$(realpath "$1")
load_stage=$2
if [[ $load_stage != training ]]; then
    test -s "$load_payload/frozen-model.json"
fi
if [[ $load_stage == test ]]; then
    test -s "$load_payload/frozen-calibration.json"
fi
mkdir "$load_payload/run-$load_stage"
load_finish() {
    load_status=$?
    printf '%s\n' "$load_status" > "$load_payload/run-$load_stage/exit-status"
    cd "$load_payload"
    find "run-$load_stage" -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > "run-$load_stage/SHA256SUMS"
    exit "$load_status"
}
trap load_finish EXIT
exec 9>/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock
printf '%s\n' waiting-lock > "$load_payload/run-$load_stage/phase"
flock 9
cd "$load_payload"
sha256sum -c SHA256SUMS > "run-$load_stage/input-check.log" 2>&1
date -Is > "run-$load_stage/identity.log"
uname -a >> "run-$load_stage/identity.log"
printf '%s\n' "$TMUX" > "run-$load_stage/tmux.log"
if [[ $load_stage != training ]]; then
    cp frozen-model.json "run-$load_stage/frozen-model.json"
fi
if [[ $load_stage == test ]]; then
    cp frozen-calibration.json "run-$load_stage/frozen-calibration.json"
fi
printf '%s\n' running > "run-$load_stage/phase"
timeout 180 ./measure bench "$load_stage" > "run-$load_stage/samples.jsonl" 2> "run-$load_stage/measure.log"
printf '%s\n' complete > "run-$load_stage/phase"
