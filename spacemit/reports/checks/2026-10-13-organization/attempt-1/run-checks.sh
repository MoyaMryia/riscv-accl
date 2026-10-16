#!/usr/bin/env bash
# 在本地 tmux 会话内复核本次交付材料。
set -u
check_root=/home/moyamryia/Projects/riscv-accl
check_logs="$check_root/spacemit/reports/checks/2026-10-13-organization"
cd "$check_root" || exit 1
printf '%s\n' riscv_delivery_checks > "$check_logs/session-name"
printf '%s\n' "$PWD" > "$check_logs/working-directory"
python3 "$check_logs/run-checks.py" \
  --raw-before /tmp/riscv-accl-organize-20261013/raw-before.json \
  > "$check_logs/driver.log" 2>&1
check_status=$?
printf '%s\n' "$check_status" > "$check_logs/exit-status"
exit "$check_status"
