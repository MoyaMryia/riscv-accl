#!/usr/bin/env bash
set -euo pipefail
out=$1
rounds=${2:-64}
base=/home/moyamryia/Projects/riscv-accl-bench-2026-09-27
script_dir=$(cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$out"
test ! -e "$out/driver.log"
exec >"$out/driver.log" 2>&1
trap 'status=$?; date -Is >"$out/end-clock.log"; printf "%s\n" "$status" >"$out/exit-status"' EXIT
printf 'wait for shared lock\n' >"$out/phase"
exec 9>"$base/document-quality-suite.lock"
flock -x 9
date -Is >"$out/start-clock.log"
lslocks >"$out/locks.log"
tmux list-sessions >"$out/sessions.log"
sha256sum /usr/bin/python3.12 "$base/original-monitor.py" "$script_dir"/* >"$out/source-identities.sha256"
test "$(sha256sum /usr/bin/python3.12 | cut -d' ' -f1)" = 630db2135a33fddb6416e77341ef48e5376f903fcb81d3e0fe36a496a4d0e2d0
readelf -n /usr/bin/python3.12 >"$out/python-build-id.log"
mkdir "$out/fixtures" "$out/attempts" "$out/input-blobs"
for name in k1-local-candidates-C-repair2-20261008-190930 k1-local-candidates-C1-repeat-20261008-202900; do
    (
        cd "$base"
        find "$name" -type f \( -name '*.json' -o -name '*.server.log' -o -name '*failure.txt' -o -name phase -o -name exit-status \) -print0 |
            xargs -0 cp --parents -p -t "$out/fixtures"
    )
done
find "$base/k1-local-candidates-C-repair2-20261008-190930" "$base/k1-local-candidates-C1-repeat-20261008-202900" -type f \( -name '*.json' -o -name '*.server.log' -o -name '*failure.txt' -o -name phase -o -name exit-status \) -print0 | sort -z | xargs -0 sha256sum >"$out/old-inputs-before.sha256"
export MONITOR_ORIGINAL="$base/original-monitor.py"
export MONITOR_TARGET="$script_dir/monitor-debug-target.py"
export MONITOR_SHADOW="$out/fixtures"
export PYTHONDONTWRITEBYTECODE=1
cd /home/moyamryia
for variant in capture-self-test exact malloc-debug trace gc-stress guard; do
    iterations=$rounds
    if [ "$variant" = guard ]; then iterations=$(( (rounds + 7) / 8 )); fi
    if [ "$variant" = capture-self-test ]; then iterations=1; fi
    for ((index=0; index<iterations; index++)); do
        cpu=$((index % 8))
        if [ "$variant" = guard ]; then cpu=6; fi
        export MONITOR_VARIANT="$variant"
        export MONITOR_ATTEMPT="$out/attempts/$variant-$index-cpu$cpu"
        export MONITOR_LOOPS=1
        unset PYTHONMALLOC
        export MONITOR_MALLOC=default
        if [ "$variant" = malloc-debug ] || [ "$variant" = gc-stress ]; then export MONITOR_MALLOC=debug; fi
        if [ "$variant" = gc-stress ] || [ "$variant" = guard ]; then export MONITOR_LOOPS=8; fi
        mkdir "$MONITOR_ATTEMPT"
        printf '%s %s CPU %s\n' "$variant" "$index" "$cpu" >"$out/phase"
        date -Is >"$MONITOR_ATTEMPT/start-clock.log"
        set +e
        timeout --signal=TERM --kill-after=10s 180s taskset -c "$cpu" gdb -nx -batch /usr/bin/python3.12 -x "$script_dir/monitor-debug-gdb.py" >"$MONITOR_ATTEMPT/gdb.log" 2>&1
        status=$?
        set -e
        printf '%s %s %s %s\n' "$variant" "$index" "$cpu" "$status" >>"$out/attempt-status.log"
        printf '%s\n' "$status" >"$MONITOR_ATTEMPT/driver-status"
        date -Is >"$MONITOR_ATTEMPT/end-clock.log"
        if [ "$variant" = capture-self-test ]; then
            test "$status" = 2
            test -s "$MONITOR_ATTEMPT/captured.core"
            test -s "$MONITOR_ATTEMPT/python-stack.log"
            grep -q '"reason": "signal:SIGUSR2"' "$MONITOR_ATTEMPT/debug-result.json"
            continue
        fi
        if [ "$status" -ne 0 ]; then
            printf 'stopped: inspect captured evidence; status %s\n' "$status" >"$out/phase"
            journalctl -k --no-pager --since "$(cat "$out/start-clock.log")" >"$out/kernel-after.log"
            exit "$status"
        fi
    done
done
sha256sum -c "$out/old-inputs-before.sha256" >"$out/old-inputs-after-check.log"
journalctl -k --no-pager --since "$(cat "$out/start-clock.log")" >"$out/kernel-after.log"
printf 'bounded debug campaign complete; no captured fault\n' >"$out/phase"
