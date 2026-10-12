#!/usr/bin/env bash
# 在 tmux 内持锁执行统一分析器。
set -euo pipefail
if [[ $# -lt 2 || -z ${TMUX:-} ]]; then
    echo '必须在 tmux 内提供新目录和分析器参数。' >&2
    exit 2
fi
predictor_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
predictor_repo=$(cd "$predictor_dir/../../../.." && pwd)
predictor_out=$(realpath -m "$1")
shift
mkdir "$predictor_out"
predictor_finish() {
    predictor_status=$?
    printf '%s\n' "$predictor_status" > "$predictor_out/exit-status"
    if [[ $predictor_status -eq 0 ]]; then
        printf '%s\n' complete > "$predictor_out/phase"
    else
        printf '%s\n' stopped > "$predictor_out/phase"
    fi
    cd "$predictor_out"
    find . -type f ! -path ./SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
    exit "$predictor_status"
}
trap predictor_finish EXIT
printf '%s\n' "$TMUX" > "$predictor_out/tmux.log"
cd "$predictor_repo"
source spacemit/bench/qemu-screen/server-env.sh
predictor_previous=''
for predictor_arg in "$@"; do
    if [[ "$predictor_previous" == --mca ]]; then
        predictor_runtime=$(realpath "$(dirname "$predictor_arg")/../../x86_64-linux-gnu")
        export LD_LIBRARY_PATH="$predictor_runtime:$LD_LIBRARY_PATH"
    fi
    predictor_previous=$predictor_arg
done
exec 9>lab/qemu-screen-server.lock
printf '%s\n' waiting-lock > "$predictor_out/phase"
flock 9
printf '%s\n' running > "$predictor_out/phase"
date -Is > "$predictor_out/identity.log"
hostname >> "$predictor_out/identity.log"
lscpu -e > "$predictor_out/topology.log"
taskset -pc $$ > "$predictor_out/affinity.log"
set +e
python3 "$predictor_dir/analyze.py" "$@" --output "$predictor_out/result" > "$predictor_out/driver.log" 2>&1
predictor_status=$?
set -e
exit "$predictor_status"
