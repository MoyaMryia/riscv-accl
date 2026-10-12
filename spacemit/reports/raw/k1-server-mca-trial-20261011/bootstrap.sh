#!/usr/bin/env bash
set -euo pipefail
cd /home/moyamryia/Projects/riscv-accl/lab/k1-mca-trial-20261011
exec 9>../qemu-screen-server.lock
flock 9
trap 'status=$?; echo "$status" > bootstrap-exit-status' EXIT
printf '%s\n' download > phase
apt-cache show llvm-22 libllvm22 > package-metadata.log
mkdir packages runtime
cd packages
apt-get download llvm-22 libllvm22
sha256sum *.deb > SHA256SUMS
for package in *.deb; do dpkg-deb -x "$package" ../runtime; done
cd ..
export LD_LIBRARY_PATH="$PWD/runtime/usr/lib/x86_64-linux-gnu"
printf '%s\n' tool-check > phase
runtime/usr/lib/llvm-22/bin/llvm-mca --version > version.log
runtime/usr/lib/llvm-22/bin/llvm-mca -mtriple=riscv64 -mcpu=help > cpu-help.log 2>&1
printf '%s\n' ready > phase
