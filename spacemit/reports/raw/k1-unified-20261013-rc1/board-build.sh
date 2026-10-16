#!/usr/bin/env bash
set -u
rc_root=$(cd "$(dirname "$0")" && pwd)
printf '%s\n' 'k1_unified_build' > "$rc_root/build-session"
bash "$rc_root/package/with-lock.sh" bash "$rc_root/package/build.sh" "$rc_root/source" "$rc_root/build" > "$rc_root/build.log" 2>&1
printf '%s\n' "$?" > "$rc_root/build-exit-status"
