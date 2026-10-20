#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
exec >run.log 2>&1
trap 'rc=$?; date -u "+END %Y-%m-%dT%H:%M:%SZ"; printf "%s\n" "$rc" > exit-status' EXIT
date -u '+START %Y-%m-%dT%H:%M:%SZ'
exec 9>"$HOME/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock"
printf 'WAIT_LOCK\n'
flock 9
export K1_PACKAGE_LOCK_FD=9
printf 'LOCK_ACQUIRED\n'
python3 - '/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/2b-router-e2e-20261018-054840-r1' <<'PY'
import json,sys
from pathlib import Path
root=Path(sys.argv[1])
if int((root/'exit-status').read_text()) not in (0,2):
    raise RuntimeError('automatic batch failed before controls')
p=json.loads((root/'result/progress.json').read_text())
if p['completed'] != p['planned']:
    raise RuntimeError('automatic batch matrix is incomplete')
PY
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy
export NO_PROXY=127.0.0.1,localhost
r3="$HOME/Projects/riscv-accl-bench-2026-09-27/k1-final-default-20261013-r1/final-r3"
timeout --signal=TERM --kill-after=60s 3600s python3 -u tools/router_e2e.py \
    --output "$PWD/result" --server "$r3/build/bin/llama-server" \
    --models "$HOME/Projects/spacemit-llama/models" \
    --spert "$HOME/Projects/spacemit-llama/spert/spine-runtime.riscv64.0.6.2" \
    --tcm "$HOME/Projects/llm-bench/.toolchain/spine-tcm" \
    --manifest "$r3/package/manifest.json" --build-receipt "$r3/build/build-receipt.json" \
    --chat "$PWD/tools/chat.py" --quality "$PWD/tools/quality.py" \
    --effective "$PWD/tools/effective.py" --tool-receipt "$PWD/tool-receipt.json" \
    --cases "$PWD/cases.json" --cases-module "$PWD/tools/router_cases.py" \
    --router "$PWD/router" --code-controls
