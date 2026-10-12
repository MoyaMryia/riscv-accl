#!/bin/bash
set -uo pipefail
cd /home/moyamryia/Projects/riscv-accl
exec 9>lab/qemu-screen-server.lock
flock 9
source spacemit/bench/qemu-screen/server-env.sh
job=lab/k1-server-parallel-20261011
printf 'validation\n' > "$job/phase"
python3 -m unittest discover -s spacemit/bench/qemu-screen -p test_parallel.py -v &&
python3 "$job/validate.py"
status=$?
printf '%s\n' "$status" > "$job/exit-status"
if [ "$status" -eq 0 ]; then
    printf 'complete\n' > "$job/phase"
else
    printf 'failed\n' > "$job/phase"
fi
exit "$status"
