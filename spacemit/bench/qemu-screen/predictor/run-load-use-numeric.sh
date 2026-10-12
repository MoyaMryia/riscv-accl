#!/usr/bin/env bash
# 核对原生完整输出，并持有板端共用锁。
set -euo pipefail
if [[ $# -ne 1 || -z ${TMUX:-} ]]; then
    echo '必须在 tmux 内提供载荷目录。' >&2
    exit 2
fi
load_payload=$(realpath "$1")
mkdir "$load_payload/run-numeric"
load_finish() {
    load_status=$?
    printf '%s\n' "$load_status" > "$load_payload/run-numeric/exit-status"
    cd "$load_payload"
    find run-numeric -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > run-numeric/SHA256SUMS
    exit "$load_status"
}
trap load_finish EXIT
exec 9>/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock
printf '%s\n' waiting-lock > "$load_payload/run-numeric/phase"
flock 9
cd "$load_payload"
sha256sum -c SHA256SUMS > run-numeric/input-check.log 2>&1
cp "$(realpath "$0")" run-numeric/runner.sh
date -Is > run-numeric/identity.log
printf '%s\n' "$TMUX" > run-numeric/tmux.log
python3 -c 'import json; print("\n".join(r["id"] for r in json.load(open("plan.json"))["records"]))' > run-numeric/ids.txt
printf '%s\n' running > run-numeric/phase
while IFS= read -r load_id; do
    timeout 10 ./measure trace "$load_id" 2 "run-numeric/$load_id.bin" > "run-numeric/$load_id.log" 2>&1
done < run-numeric/ids.txt
printf '%s\n' complete > run-numeric/phase
