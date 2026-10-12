#!/usr/bin/env bash
# Stage the code and start a bounded board run in a detached tmux session.
set -euo pipefail
REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
BENCH_DIR="$REPO_ROOT/spacemit/bench"
BOARD=${BOARD:-musepipro-wg}
REMOTE_ROOT='~/Projects/riscv-accl-bench-2026-09-27'
scp "$BENCH_DIR/bench-lifecycle.py" "$BENCH_DIR/bench-shared-document-cache.py" \
    "$BENCH_DIR/run-shared-document-quality-board.sh" \
    "$BENCH_DIR/run-shared-document-quality-detached-board.sh" "$BOARD:$REMOTE_ROOT/"
ssh "$BOARD" 'cd ~/Projects/riscv-accl-bench-2026-09-27 && \
  if tmux has-session -t shared_doc_quality_2b16k 2>/dev/null; then echo "quality run already active"; exit 1; fi; \
  if pgrep -x llama-server >/dev/null; then echo "another server is active"; exit 1; fi; \
  if [ -e quality256-exit-status ] || [ -e 2B-shared-document-16384-quality256-rvv1.jsonl ]; then echo "quality run artifacts already exist"; exit 1; fi; \
  tmux new-session -d -s shared_doc_quality_2b16k "bash ./run-shared-document-quality-detached-board.sh" && \
  echo "Started tmux session shared_doc_quality_2b16k"'
