#!/usr/bin/env bash
# 在 tmux 中持有共用锁，执行有界的 MTP 与质量诊断。
set -euo pipefail
if [ "$#" -ne 8 ] && [ "$#" -ne 9 ]; then
    echo '用法：run-board.sh JOB_DIR SERVER MODELS SPERT TCM MANIFEST BUILD_RECEIPT REQUEST [diagnostic|general_suite|multi_turn]' >&2
    echo 'multi_turn 模式下 REQUEST 为模型名，取值为 2B 或 4B。' >&2
    exit 2
fi
job=$1
server=$2
models=$3
spert=$4
tcm=$5
manifest=$6
receipt=$7
request=$8
mode=${9:-diagnostic}
case "$mode" in
    diagnostic) budget=10800 ;;
    general_suite) budget=21600 ;;
    multi_turn) budget=14400 ;;
    *) echo '未知实验入口。' >&2; exit 2 ;;
esac
cd "$job"
trap 'rc=$?; printf "%s\n" "$rc" > exit-status' EXIT
exec >run.log 2>&1
date -u '+START %Y-%m-%dT%H:%M:%SZ'
exec 9>"$HOME/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock"
printf 'WAIT_LOCK\n'
flock 9
export K1_PACKAGE_LOCK_FD=9
printf 'LOCK_ACQUIRED\n'
common=(--output "$PWD/result" --server "$server" --models "$models" \
    --spert "$spert" --tcm "$tcm" --manifest "$manifest" \
    --build-receipt "$receipt" --chat "$PWD/chat.py" --quality "$PWD/quality.py" \
    --effective "$PWD/effective.py" --tool-receipt "$PWD/tools.json")
if [ "$mode" = multi_turn ]; then
    timeout --signal=TERM --kill-after=60s "$budget"s python3 -u multi_turn_suite.py \
        "${common[@]}" --model "$request"
else
    timeout --signal=TERM --kill-after=60s "$budget"s python3 -u "$mode.py" \
        "${common[@]}" --request "$request"
fi
date -u '+END %Y-%m-%dT%H:%M:%SZ'
