#!/usr/bin/env bash
set -u
rc_root=$(cd "$(dirname "$0")" && pwd)
cd "$rc_root"
for rc_wait in $(seq 1 1500); do
 [[ ! -f build-exit-status ]] || break
 sleep 10
done
if [[ ! -f build-exit-status || $(cat build-exit-status) != 0 ]]; then
 echo 'Build does not pass.' > validation-driver.log
 echo 1 > validation-exit-status
 exit 1
fi
bash package/with-lock.sh python3 package/validate.py --source source --build build \
 --reference "$HOME/Projects/riscv-accl-bench-2026-09-27/k1-release-check-20261007-125712/build/bin" \
 --models "$HOME/Projects/spacemit-llama/models" --output validation > validation-driver.log 2>&1
printf '%s\n' "$?" > validation-exit-status
