#!/usr/bin/env bash
set -euo pipefail
cd /home/moyamryia/Projects/riscv-accl
exec 9>lab/qemu-screen-server.lock
flock 9
trial_root="$PWD/lab/k1-mca-trial-20261011"
trap 'status=$?; echo "$status" > "$trial_root/exit-status"' EXIT
source spacemit/bench/qemu-screen/server-env.sh
export LD_LIBRARY_PATH="$trial_root/runtime/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
printf '%s\n' qemu-conv > "$trial_root/phase"
python3 spacemit/bench/qemu-screen/prepare-conv.py "$trial_root/conv-plan" --tune spacemit-x60 --qemu-prefix lab/qemu-host-runtime
python3 spacemit/bench/qemu-screen/batch.py "$trial_root/conv-plan/plan.json" "$trial_root/qemu-conv"
printf '%s\n' mca-coverage > "$trial_root/phase"
python3 spacemit/bench/qemu-screen/mca-screen.py --mca "$trial_root/runtime/usr/lib/llvm-22/bin/llvm-mca" --inventories "$trial_root/input/combined.json" "$trial_root/input/conv-default.json" "$trial_root/input/conv-x60.json" --output "$trial_root/analysis"
printf '%s\n' complete > "$trial_root/phase"
