#!/usr/bin/env bash
# 在当前 shell 中启用项目私有工具。
qemu_screen_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
export K1_QEMU_PREFIX="$qemu_screen_root/lab/qemu-host-runtime"
export PATH="$K1_QEMU_PREFIX/bin:$qemu_screen_root/lab/toolchain/toolchain/riscv/bin:$PATH"
export LD_LIBRARY_PATH="$K1_QEMU_PREFIX/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PKG_CONFIG_PATH="$K1_QEMU_PREFIX/lib/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
unset qemu_screen_root
