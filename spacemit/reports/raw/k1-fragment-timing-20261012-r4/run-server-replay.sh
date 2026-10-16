#!/usr/bin/env bash
set -euo pipefail
fragment_root=/home/moyamryia/Projects/riscv-accl/lab/k1-fragment-timing-20261012-r4
cd "$fragment_root"
: "${TMUX:?tmux is required}"
exec 9>/home/moyamryia/Projects/riscv-accl/lab/qemu-screen-server.lock
if ! flock -n 9; then printf '73\n' > "$fragment_root/server-exit-status"; exit 73; fi
trap 'status=$?; printf "%s\n" "$status" > "$fragment_root/server-exit-status"' EXIT
sha256sum portable.tar.gz > server-archive-SHA256SUMS
tar -xzf portable.tar.gz
cd portable
sha256sum -c SHA256SUMS > "$fragment_root/server-input-verification.log"
python3 -B replay.py > "$fragment_root/server-replay.log" 2>&1
