#!/usr/bin/env bash
set -u
audit_root=$(cd -- "$(dirname -- "$0")" && pwd)
audit_bundle="$HOME/Projects/riscv-accl-bench-2026-09-27/k1-committee-release-20261016-r1"
bash "$audit_bundle/runtime/package/with-lock.sh" strace -f -tt -yy -e trace=openat,mmap,munmap,ioctl -o "$audit_root/syscalls.log" python3 "$audit_root/audit.py" > "$audit_root/run.log" 2>&1
audit_code=$?
printf '%s\n' "$audit_code" > "$audit_root/exit-status"
exit "$audit_code"
