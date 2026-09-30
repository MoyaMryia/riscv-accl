#!/usr/bin/env bash
# Execute the entire requested cache-quality matrix sequentially on the board.
set -uo pipefail
RUN_ROOT=$1
MODELS=$2
CONTEXTS=$3
MAX_TOKENS=$4
CASE_IDS=${5:-}
exec 9> "$HOME/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock"
if ! flock -n 9; then
  echo 'another document quality suite holds the board lock' >&2
  printf '1\n' > "$RUN_ROOT/board-exit-status"
  exit 1
fi
SERVER_ROOT=${SERVER_ROOT:-"$HOME/Projects/spacemit-llama-integrated"}
MODEL_ROOT=${MODEL_ROOT:-"$HOME/Projects/spacemit-llama/models"}
export LD_LIBRARY_PATH="$HOME/Projects/llm-bench/.toolchain/spine-tcm:$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2/lib:$SERVER_ROOT/build/bin${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export SPINE_FA_WIDE_TILE=1
unset SPINE_MTP_WINDOW SPINE_SPEC_RS
if pgrep -x llama-server >/dev/null; then
  echo 'another llama-server is active' >&2
  printf '1\n' > "$RUN_ROOT/board-exit-status"
  exit 1
fi
overall=0
for model in $MODELS; do
  for context in $CONTEXTS; do
    label="$model-$context"
    case_args=()
    for case_id in $CASE_IDS; do case_args+=(--case-id "$case_id"); done
    (
      ulimit -v 12582912
      timeout --signal=TERM --kill-after=30s 43200s \
        python3 "$RUN_ROOT/bench/bench-shared-document-cache.py" \
        --quality-suite --server "$SERVER_ROOT/build/bin/llama-server" \
        --model "$MODEL_ROOT/Qwen3.5-$model-MTP-Q4_0-embQ4_0-dv64k.gguf" \
        --model-size "$model" --context "$context" --ctx-size "$((context + MAX_TOKENS + 1024))" \
        --document "$HOME/Projects/riscv-accl-bench-2026-09-27/shared-document-public-llamacpp.txt" \
        --source-readme "$SERVER_ROOT/tools/server/README.md" --n-predict "$MAX_TOKENS" \
        --allow-eos --timeout 5400 --output "$RUN_ROOT/$label.jsonl" \
        --log "$RUN_ROOT/$label.server.log" "${case_args[@]}"
    ) > "$RUN_ROOT/$label.driver.log" 2>&1
    status=$?
    printf '%s\n' "$status" > "$RUN_ROOT/$label.exit-status"
    if [ "$status" != 0 ]; then overall=1; fi
  done
done
printf '%s\n' "$overall" > "$RUN_ROOT/board-exit-status"
exit "$overall"
