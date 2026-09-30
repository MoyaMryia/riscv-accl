#!/usr/bin/env bash
# Run inside local tmux: wait for the board, then collect and cloud-score locally.
set -uo pipefail
REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
ARCHIVE="$REPO_ROOT/spacemit/reports/raw/2026-09-25-lifecycle"
BOARD=${BOARD:-musepipro-wg}
REMOTE_ROOT='~/Projects/riscv-accl-bench-2026-09-27'
log="$ARCHIVE/quality256-cloud-watcher.log"
status_file="$ARCHIVE/quality256-cloud-exit-status"
echo "WATCH $(date -Is)" > "$log"
deadline=$(( $(date +%s) + 18000 ))
while ! ssh "$BOARD" "test -f $REMOTE_ROOT/quality256-exit-status" 2>/dev/null; do
  if [ "$(date +%s)" -ge "$deadline" ]; then
    echo 'FAIL: board result did not complete within five hours' >> "$log"
    printf '124\n' > "$status_file"
    exit 124
  fi
  sleep 60
done
bash "$REPO_ROOT/spacemit/bench/finish-shared-document-quality.sh" >> "$log" 2>&1
status=$?
printf '%s\n' "$status" > "$status_file"
echo "DONE exit=$status $(date -Is)" >> "$log"
exit "$status"
