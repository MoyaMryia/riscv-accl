#!/usr/bin/env bash
# 在 tmux 中取得项目共用锁。
set -euo pipefail
[[ -n ${TMUX:-} ]] || { echo 'Run this command in tmux.' >&2; exit 2; }
[[ $# -gt 0 ]] || { echo 'usage: with-lock.sh COMMAND [ARGS]' >&2; exit 2; }
exec 9>"$HOME/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock"
flock -x 9
export K1_PACKAGE_LOCK_FD=9
exec "$@"
