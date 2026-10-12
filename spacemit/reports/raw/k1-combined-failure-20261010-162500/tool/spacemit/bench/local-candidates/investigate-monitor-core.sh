#!/usr/bin/env bash
set -u
out=$1
exec 9>/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock
flock -x 9
mkdir -p "$out"
exec >"$out/driver.log" 2>&1
trap 'printf "%s\n" "$?" >"$out/exit-status"' EXIT
cd "$out" || exit 1
printf 'original core diagnostics\n' >phase
sha256sum /var/crash/_usr_bin_python3.12.1000.crash ../original.core >input-hashes.log
lslocks >locks.log
tmux list-sessions >sessions.log
gdb -nx -batch /usr/bin/python3.12 ../original.core \
    -ex 'set pagination off' -ex 'info files' -ex 'info sharedlibrary' \
    -ex 'info proc mappings' -ex 'info registers' -ex 'thread apply all bt full' \
    -ex 'x/24i $pc-32' -ex 'x/16gx $a0-32' -ex 'x/16gx $sp' \
    -ex 'info address _Py_NoneStruct' -ex 'info address PyLong_Type' \
    -ex 'info symbol $a0' -ex 'py-bt' >gdb-core.log 2>&1
printf '%s\n' "$?" >gdb-status
readelf -n ../original.core >core-notes.log 2>&1
ls -l /usr/share/gdb/auto-load/usr/bin/python* /usr/lib/debug/.build-id/ >debug-files.log 2>&1
sha256sum /usr/bin/python3.12 /usr/lib/riscv64-linux-gnu/libc.so.6 >current-identities.log
printf 'original core diagnostics complete\n' >phase
