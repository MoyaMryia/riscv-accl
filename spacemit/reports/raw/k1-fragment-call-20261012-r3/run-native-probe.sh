#!/usr/bin/env bash
set -euo pipefail
cd /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-fragment-call-20261012-r3
: "${TMUX:?tmux is required}"
exec 9>/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock
if ! flock -n 9; then printf '73\n' > native-probe-exit-status; exit 73; fi
trap 'status=$?; printf "%s\n" "$status" > native-probe-exit-status' EXIT
sha256sum /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-fragment-source-20261012-r2/payload/fragment > binary-SHA256SUMS
date -u +%Y-%m-%dT%H:%M:%SZ > started-at-utc
timeout 60 gdb -nx -batch -x native-probe.gdb /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-fragment-source-20261012-r2/payload/fragment > native-probe.log 2>&1
date -u +%Y-%m-%dT%H:%M:%SZ > finished-at-utc
