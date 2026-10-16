#!/usr/bin/env bash
set -euo pipefail
cd /home/moyamryia/Projects/riscv-accl/lab/k1-fragment-call-20261012-r3
: "${TMUX:?tmux is required}"
exec 9>/home/moyamryia/Projects/riscv-accl/lab/qemu-screen-server.lock
if ! flock -n 9; then printf '73\n' > server-exit-status; exit 73; fi
trap 'status=$?; printf "%s\n" "$status" > server-exit-status' EXIT
sha256sum portable.tar.gz > server-archive-SHA256SUMS
tar -xzf portable.tar.gz
cd portable
sha256sum -c SHA256SUMS > ../server-input-verification.log
python3 -B replay.py > ../server-replay.log 2>&1
