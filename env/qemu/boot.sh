#!/bin/sh
# Boot a minimal RISC-V 64-bit Linux in QEMU 11 (qemu-system-riscv64) and drop into a root shell.
#
# Usage:   ./boot.sh [--rebuild] [mem]
#   --rebuild    rebuild the initramfs.cpio.gz from initrd-root/ before booting
#   mem          guest RAM in MiB (default 512)
#   e.g.         ./boot.sh --rebuild 1024
#
# Requires (local, already present):
#   vmlinux-rv64     kernel Image (Debian 6.12 riscv64, EFI-stub capable)
#   initrd-root/     Alpine riscv64 rootfs (busybox) + our /init + /etc/inittab
#   -bios            OpenSBI fw_dynamic from QEMU's share dir
#
# Exit codes: 0 boot ran and was terminated cleanly; 130/124 test-timeout.

set -eu

QEMU=${QEMU:-qemu-system-riscv64}
DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BIOS=${BIOS:-/usr/local/share/qemu/opensbi-riscv64-generic-fw_dynamic.bin}

KERNEL="$DIR/vmlinux-rv64"
INITRD="$DIR/initramfs.cpio.gz"
ROOTFS="$DIR/initrd-root"

MEM=512
if [ "${1:-}" = "--rebuild" ]; then
    shift
    [ -d "$ROOTFS" ] || { echo "error: $ROOTFS missing" >&2; exit 66; }
    ( cd "$ROOTFS" && find . -print | cpio -o -H newc 2>/dev/null | gzip -9 > "$INITRD" )
    echo "rebuilt $INITRD"
fi
case "${1:-}" in
    ''|*[!0-9]*) : ;;
    *) MEM=$1; shift ;;
esac

exec "$QEMU" -M virt -m "${MEM}M" -smp 2 \
    -bios "$BIOS" \
    -kernel "$KERNEL" \
    -initrd "$INITRD" \
    -append "console=ttyS0 rdinit=/init" \
    -nographic -no-reboot
