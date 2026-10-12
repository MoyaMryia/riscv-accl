#!/usr/bin/env bash
set -euo pipefail
cd /home/moyamryia/Projects/riscv-accl
exec 9>lab/qemu-screen-server.lock
flock 9
trial_root="$PWD/lab/k1-mca-trial-20261011"
trap 'status=$?; echo "$status" > "$trial_root/extra-exit-status"' EXIT
source spacemit/bench/qemu-screen/server-env.sh
mkdir "$trial_root/b2-run" "$trial_root/ime-load-iterations"
for arm in original b2; do
  env LD_LIBRARY_PATH="$trial_root/b2-input/$arm:$trial_root/b2-input/common" SPINE_K1_TRACE=1 qemu-riscv64 -L lab/toolchain/toolchain/riscv/sysroot -cpu rv64,v=true,vlen=256,elen=64,zfh=true,zvfh=true "$trial_root/b2-input/test-b2" --dump "$trial_root/b2-run/$arm.bin" > "$trial_root/b2-run/$arm.log" 2>&1
done
cmp "$trial_root/b2-run/original.bin" "$trial_root/b2-run/b2.bin"
export LD_LIBRARY_PATH="$trial_root/runtime/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
for count in 10 1000; do
  for arm in control candidate; do
    "$trial_root/runtime/usr/lib/llvm-22/bin/llvm-mca" -mtriple=riscv64 -mcpu=spacemit-x60 -mattr=+v -iterations="$count" "$trial_root/ime-load-input/$arm.s" > "$trial_root/ime-load-iterations/$arm-$count.log" 2>&1
  done
done
