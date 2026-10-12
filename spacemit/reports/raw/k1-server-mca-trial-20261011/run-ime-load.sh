#!/usr/bin/env bash
set -euo pipefail
cd /home/moyamryia/Projects/riscv-accl
exec 9>lab/qemu-screen-server.lock
flock 9
trial_root="$PWD/lab/k1-mca-trial-20261011"
trap 'status=$?; echo "$status" > "$trial_root/ime-load-exit-status"' EXIT
source spacemit/bench/qemu-screen/server-env.sh
export LD_LIBRARY_PATH="$trial_root/runtime/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
mkdir "$trial_root/ime-load-run"
cd "$trial_root/ime-load-run"
riscv64-unknown-linux-gnu-g++ -O3 -static -ffp-contract=off -march=rv64gcv_zfh_zvfh -mtune=spacemit-x60 ../ime-load-input/verify.cpp ../ime-load-input/functions.s -o verify > build.log 2>&1
qemu-riscv64 -cpu rv64,v=true,vlen=256,elen=64,zfh=true,zvfh=true ./verify complete.bin > numeric.log 2>&1
for arm in control candidate; do
  "$trial_root/runtime/usr/lib/llvm-22/bin/llvm-mca" -mtriple=riscv64 -mcpu=spacemit-x60 -mattr=+v -iterations=100 -timeline -timeline-max-iterations=2 "../ime-load-input/$arm.s" > "$arm.log" 2>&1
done
sha256sum ./* > SHA256SUMS
