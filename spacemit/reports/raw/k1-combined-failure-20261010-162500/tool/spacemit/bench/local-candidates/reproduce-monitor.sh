#!/usr/bin/env bash
set -u
out=$1
base=/home/moyamryia/Projects/riscv-accl-bench-2026-09-27
exec 9>"$base/document-quality-suite.lock"
flock -x 9
mkdir -p "$out/binaries"
exec >"$out/driver.log" 2>&1
trap 'printf "%s\n" "$?" >"$out/exit-status"' EXIT
cd "$out" || exit 1
date --iso-8601=seconds >start-clock.log
lslocks >locks.log
tmux list-sessions >sessions.log
printf 'file identities\n' >phase
for target in /usr/bin/python3.12 /usr/lib/riscv64-linux-gnu/libc.so.6 /usr/lib/riscv64-linux-gnu/libexpat.so.1.9.1 /usr/lib/riscv64-linux-gnu/libz.so.1.3.1.zlib-ng /usr/lib/riscv64-linux-gnu/libm.so.6 /usr/lib/riscv64-linux-gnu/ld-linux-riscv64-lp64d.so.1 /usr/lib/python3.12/lib-dynload/_json.cpython-312-riscv64-linux-gnu.so; do
    sha256sum "$target" >>mapped-hashes.log
    stat "$target" >>mapped-stat.log
    readelf -n "$target" >>mapped-build-ids.log
    dpkg-query -S "$target" >>mapped-packages.log 2>&1
    cp -p "$target" binaries/
done
find "$base/k1-local-candidates-C-repair2-20261008-190930" "$base/k1-local-candidates-C1-repeat-20261008-202900" -type f \( -name '*.json' -o -name '*.server.log' -o -name '*failure.txt' -o -name phase -o -name exit-status \) -print0 | sort -z | xargs -0 sha256sum >inputs-before.sha256
cd /home/moyamryia || exit 1
printf 'direct stdin reproduction\n' >"$out/phase"
for iteration in $(seq 1 16); do
    timeout 60 /usr/bin/python3 - <"$base/original-monitor.py" >"$out/direct-$iteration.log" 2>&1
    result=$?
    printf '%s %s\n' "$iteration" "$result" >>"$out/direct-status.log"
    if [ "$result" -ne 0 ]; then exit "$result"; fi
done
printf 'GDB CPU 6 reproduction\n' >"$out/phase"
for iteration in $(seq 1 16); do
    timeout 60 taskset -c 6 gdb -nx -batch /usr/bin/python3 \
        -ex 'set disable-randomization off' -ex 'set pagination off' \
        -ex "run - < $base/original-monitor.py" -ex 'info program' \
        -ex 'thread apply all bt full' \
        -ex "generate-core-file $out/repro-$iteration.core" >"$out/gdb-$iteration.log" 2>&1
    result=$?
    printf '%s %s\n' "$iteration" "$result" >>"$out/gdb-status.log"
    if [ -f "$out/repro-$iteration.core" ]; then exit 139; fi
    if ! grep -q 'exited normally' "$out/gdb-$iteration.log"; then exit 1; fi
done
cd "$out" || exit 1
sha256sum -c inputs-before.sha256 >inputs-after-check.log 2>&1 || exit 1
journalctl -k --no-pager --since '2026-10-09 22:23:00' >kernel-after.log
date --iso-8601=seconds >end-clock.log
printf 'finite reproduction complete\n' >phase
