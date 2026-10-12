#!/usr/bin/env bash
set -u
out=$1
exec 9>/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock
flock -x 9
mkdir -p "$out"
exec >"$out/driver.log" 2>&1
trap 'printf "%s\n" "$?" >"$out/exit-status"' EXIT
cd "$out" || exit 1
lslocks >locks.log
tmux list-sessions >sessions.log
objdump -d --start-address=0xa120a --stop-address=0xa1340 /usr/bin/python3.12 >function-traverse.log
objdump -d --start-address=0x1c4e10 --stop-address=0x1c4e80 /usr/bin/python3.12 >gc-caller.log
readelf -Ws /usr/bin/python3.12 | grep -E 'PyFunction_Type|PyBytes_Type|PyFrame_Type' >type-symbols.log
apt-cache policy python3.12-minimal python3.12-minimal-dbgsym python3.12-dbgsym >debug-package-policy.log 2>&1
journalctl --list-boots --no-pager >boots.log
journalctl --no-pager --since '2026-10-08 20:50:00' --until '2026-10-08 21:20:00' >journal-wide.log
ls -la /sys/devices/system/edac/mc /sys/class/thermal >hardware-counters.log 2>&1
sha256sum /var/crash/_usr_bin_python3.12.1000.crash >original-crash-hash.log
printf 'native evidence complete\n' >phase
