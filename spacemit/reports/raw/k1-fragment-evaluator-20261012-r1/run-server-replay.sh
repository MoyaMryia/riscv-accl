#!/bin/bash
set -eu
fragment_work=/home/moyamryia/Projects/riscv-accl/lab/k1-fragment-evaluator-20261012-r1
trap 'printf "%s\n" "$?" > "$fragment_work/server-exit-status"' EXIT
exec 9>/home/moyamryia/Projects/riscv-accl/lab/qemu-screen-server.lock
flock -n 9
cd "$fragment_work"
sha256sum -c archive-SHA256SUMS
mkdir unpacked
tar -xzf fragment-examples.tar.gz -C unpacked
python3 -B unpacked/fragment-examples/run-fragment-examples.py \
  --root unpacked/fragment-examples --output server-replay.json
