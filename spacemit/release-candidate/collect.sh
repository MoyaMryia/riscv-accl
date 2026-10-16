#!/usr/bin/env bash
# 只收集已结束的验证，不重启构建或模型请求。
set -euo pipefail
[[ $# == 3 ]] || { echo 'usage: collect.sh BOARD REMOTE_ROOT NEW_LOCAL_DIR' >&2; exit 2; }
[[ -n ${TMUX:-} ]] || { echo 'Run this command in tmux.' >&2; exit 2; }
rc_board=$1
rc_remote=$2
rc_local=$3
[[ "$rc_remote" =~ ^/[a-zA-Z0-9_./-]+$ ]] || { echo 'Invalid remote path.' >&2; exit 2; }
[[ ! -e "$rc_local" ]] || { echo 'Local output exists.' >&2; exit 2; }
mkdir -p "$rc_local"
ssh "$rc_board" "test -f '$rc_remote/validation-exit-status'"
ssh "$rc_board" "cd '$rc_remote' && tar --exclude=validation/relocated-build -czf collected.tar.gz validation validation-driver.log validation-exit-status build.log build-exit-status build-session board-build.sh board-validate.sh package build/bin build/build-receipt.json build/CMakeCache.txt build/compile_commands.json && sha256sum collected.tar.gz > collected.tar.gz.sha256"
scp "$rc_board:$rc_remote/collected.tar.gz" "$rc_board:$rc_remote/collected.tar.gz.sha256" "$rc_local/"
(cd "$rc_local" && sha256sum -c collected.tar.gz.sha256 && tar -xzf collected.tar.gz)
python3 - "$rc_local" <<'PY'
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]); evidence=root/'validation'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
pins=json.loads((evidence/'receipts.json').read_text())
for n,h in pins.items():
 if sha(evidence/n)!=h:raise SystemExit('Evidence differs: '+n)
result={'receipt_files':len(pins),'build_exit_status':(root/'build-exit-status').read_text().strip(),
        'validation_exit_status':(root/'validation-exit-status').read_text().strip(),
        'summary_status':json.loads((evidence/'summary.json').read_text())['status']}
(root/'collection.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
PY
