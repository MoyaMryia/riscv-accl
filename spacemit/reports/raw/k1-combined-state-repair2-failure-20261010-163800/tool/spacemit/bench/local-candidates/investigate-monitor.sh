#!/usr/bin/env bash
set -u
out=$1
mkdir -p "$out"
exec 9>/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock
flock -x 9
exec >"$out/driver.log" 2>&1
trap 'printf "%s\n" "$?" >"$out/exit-status"' EXIT
cd "$out" || exit 1
printf 'initial diagnostics\n' >phase
capture() {
    local name=$1
    shift
    "$@" >"$name" 2>&1
    printf '%s %s\n' "$?" "$name" >>command-status
}
capture clock.log date --iso-8601=seconds
capture processes.log ps -eo pid,ppid,stat,etime,pcpu,pmem,args
capture locks.log lslocks
capture sessions.log tmux list-sessions
capture uname.log uname -a
capture memory.log cat /proc/meminfo
capture cpu.log cat /proc/cpuinfo
capture core-pattern.log cat /proc/sys/kernel/core_pattern
capture core-limits.log bash -c 'ulimit -a; cat /proc/sys/fs/suid_dumpable; cat /proc/sys/kernel/core_uses_pid'
capture core-directories.log ls -la /var/lib/systemd/coredump /var/crash /home/moyamryia/core
capture core-config.log bash -c 'cat /etc/systemd/coredump.conf /etc/systemd/coredump.conf.d/* /etc/default/apport /proc/sys/kernel/tainted'
capture core-record.log coredumpctl --no-pager info 4114
capture core-list.log coredumpctl --no-pager list --since '2026-10-08 21:00:00' --until '2026-10-08 21:12:00'
capture journal-event.log journalctl --no-pager --since '2026-10-08 21:00:00' --until '2026-10-08 21:12:00'
capture kernel-event.log journalctl -k --no-pager --since '2026-10-08 20:50:00' --until '2026-10-08 21:20:00'
capture kernel-all.log journalctl -k --no-pager
capture tools.log bash -c 'command -v gdb objdump readelf addr2line coredumpctl dpkg-query taskset timeout'
capture python-link.log readlink -f /usr/bin/python3
capture python-stat.log stat /usr/bin/python3 /usr/bin/python3.12
capture python-version.log /usr/bin/python3 --version
capture python-hash.log sha256sum /usr/bin/python3.12
capture python-libraries.log ldd /usr/bin/python3.12
capture python-library-hashes.log bash -c 'ldd /usr/bin/python3.12 | awk "{for(i=1;i<=NF;i++) if(\$i ~ /^\//) print \$i}" | xargs -r sha256sum'
capture python-packages.log dpkg-query -W python3.12 python3.12-minimal libpython3.12-stdlib libc6 libexpat1 zlib1g libssl3t64
capture python-elf.log readelf -h -n -l /usr/bin/python3.12
capture python-instruction.log objdump -d --start-address=0x1c45d0 --stop-address=0x1c4660 /usr/bin/python3.12
capture python-symbols.log addr2line -f -C -e /usr/bin/python3.12 0x1c4612 0xa1244 0x1c4610
capture package-log.log bash -c 'ls -l /var/log/dpkg.log* /var/log/apt/history.log*; tail -n 100 /var/log/dpkg.log'
capture relevant-environment.log bash -c 'for n in PATH LD_LIBRARY_PATH LD_PRELOAD PYTHONPATH PYTHONHOME PYTHONMALLOC PYTHONHASHSEED LANG LC_ALL; do printf "%s=%s\n" "$n" "${!n-}"; done; pwd'
capture core-search.log find /home/moyamryia /var/lib/systemd/coredump /var/crash -maxdepth 4 -type f -name 'core*' -ls
printf 'initial diagnostics complete\n' >phase
