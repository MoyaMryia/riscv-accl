#!/bin/bash
set -uo pipefail
cd /home/moyamryia/Projects/riscv-accl
exec 9>lab/qemu-screen-server.lock
flock 9
source spacemit/bench/qemu-screen/server-env.sh
job=lab/k1-host-speed-20261011
printf 'running\n' > "$job/phase-$1"
python3 "$job/benchmark.py" "$1"
status=$?
printf '%s\n' "$status" > "$job/exit-status-$1"
printf 'ended\n' > "$job/phase-$1"
exit "$status"
