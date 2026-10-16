#!/usr/bin/env bash
# 在本地 tmux 会话内复核本次交付材料。
set -u
check_root=/home/moyamryia/Projects/riscv-accl
check_logs="$check_root/spacemit/reports/checks/2026-10-13-organization"
cd "$check_root" || exit 1
rm -f "$check_logs/exit-status"
printf '%s\n' local-checks > "$check_logs/phase"
printf '%s\n' riscv_delivery_checks > "$check_logs/session-name"
printf '%s\n' "$PWD" > "$check_logs/working-directory"
python3 "$check_logs/run-checks.py" \
  --raw-before /tmp/riscv-accl-organize-20261013/raw-before.json \
  "$@" \
  > "$check_logs/driver.log" 2>&1
check_status=$?
printf '%s\n' "$check_status" > "$check_logs/exit-status"
if [[ "$check_status" == 0 ]]; then
  printf '%s\n' complete > "$check_logs/phase"
else
  printf '%s\n' failed > "$check_logs/phase"
fi
exit "$check_status"
