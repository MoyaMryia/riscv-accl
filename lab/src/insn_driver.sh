#!/bin/bash
# 7-boot instruction-count measurement driver
RES=/home/moyamryia/llm-artifacts/insn-results.txt
: > "$RES"
QEMU=/usr/local/bin/qemu-system-riscv64
[ -x "$QEMU" ] || QEMU=qemu-system-riscv64

run_boot() { # <initrd> <tag> <bench>
  local rootfs=$1 tag=$2 bench=$3
  local log=/home/moyamryia/llm-artifacts/insn-$tag.log
  rm -f "$log"
  "$QEMU" -M virt -m 4096M -smp 1 -cpu xiangshan-kunminghu \
    -bios /usr/local/share/qemu/opensbi-riscv64-generic-fw_dynamic.bin \
    -kernel /home/moyamryia/Projects/riscv-accl/env/qemu/vmlinux-rv64 \
    -initrd "$rootfs" \
    -append "console=ttyS0 rdinit=/init bench=$bench" \
    -nographic -no-reboot \
    -plugin file=/home/moyamryia/llm-artifacts/libinsnsum.so \
    > "$log" 2>&1
  local v=$(grep -o 'insn_total=[0-9]*' "$log" | cut -d= -f2)
  echo "$tag bench=$bench insn_total=$v" >> "$RES"
}

S=/home/moyamryia/llm-artifacts/initramfs-insn-s.cpio.gz
R=/home/moyamryia/llm-artifacts/initramfs-insn-r.cpio.gz
run_boot "$S" s-null null
run_boot "$S" s-load load
run_boot "$S" s-tg   tg
run_boot "$S" s-pp   pp
run_boot "$R" r-load load
run_boot "$R" r-tg   tg
run_boot "$R" r-pp   pp
echo "ALL-DONE" >> "$RES"
