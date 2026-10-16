#!/usr/bin/env bash
set -euo pipefail
cd /home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-fragment-timing-20261012-r4
trap 'status=$?; printf "%s\n" "$status" > driver-exit-status' EXIT
bash payload/run-fragment-board.sh payload
python3 - <<'PYTHON'
import hashlib,json,pathlib,tarfile
root=pathlib.Path.cwd()
with tarfile.open(root/'native.tar.gz','w:gz') as archive:archive.add(root/'native',arcname='native')
path=root/'native.tar.gz'
(root/'native-archive-receipt.json').write_text(json.dumps(dict(archive_bytes=path.stat().st_size,archive_sha256=hashlib.sha256(path.read_bytes()).hexdigest()),indent=2)+'\n')
PYTHON
