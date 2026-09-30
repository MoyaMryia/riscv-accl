#!/usr/bin/env bash
# Detached board smoke: a cold question followed by a changed warm question.
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
RUN_DIR=${RUN_DIR:-"$HOME/Projects/riscv-accl-bench-2026-09-27/cached-document-smoke"}
mkdir -p "$RUN_DIR"
if [ -e "$RUN_DIR/result.jsonl" ] || [ -e "$RUN_DIR/server.log" ]; then
  echo "smoke output already exists in $RUN_DIR" >&2
  exit 1
fi
python3 - "$RUN_DIR/document.md" <<'PY'
from pathlib import Path
import sys
source = Path.home() / 'Projects/spacemit-llama-integrated/tools/server/README.md'
Path(sys.argv[1]).write_text(source.read_text(encoding='utf-8')[:8000], encoding='utf-8')
PY
CTX_SIZE=4096 "$SCRIPT_DIR/run-cached-server-board.sh" > "$RUN_DIR/server.log" 2>&1 &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true' EXIT
python3 - <<'PY'
import time, urllib.request
for _ in range(120):
    try:
        with urllib.request.urlopen('http://127.0.0.1:18085/health', timeout=2) as response:
            if response.status == 200:
                break
    except Exception:
        pass
    time.sleep(1)
else:
    raise SystemExit('server health timeout')
PY
python3 "$SCRIPT_DIR/cached-document-chat.py" \
  --document "$RUN_DIR/document.md" --ctx-size 4096 --max-tokens 64 \
  --question 'What project does this document describe?' \
  --question 'Which HTTP API does this server provide?' \
  --output "$RUN_DIR/result.jsonl" > "$RUN_DIR/client.log" 2>&1
python3 - "$RUN_DIR/result.jsonl" <<'PY'
import json, sys
rows = [json.loads(line) for line in open(sys.argv[1])]
assert len(rows) == 2, rows
assert rows[0]['document_sha256'] == rows[1]['document_sha256']
assert rows[0]['cache_prompt'] and rows[1]['cache_prompt']
assert rows[0]['slot'] == rows[1]['slot'] == 0
assert rows[0]['answer'] and rows[1]['answer']
assert rows[1]['ttft_s'] < rows[0]['ttft_s'] * .25, rows
print(f"PASS: cold TTFT {rows[0]['ttft_s']:.2f}s; changed-question warm TTFT {rows[1]['ttft_s']:.2f}s")
PY
