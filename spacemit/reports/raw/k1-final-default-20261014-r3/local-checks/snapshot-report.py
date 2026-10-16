"""保留更新前的综合报告与导出工具。"""
import hashlib
import json
import os
from pathlib import Path
import shutil

assert os.environ.get('TMUX')
root = Path(__file__).resolve().parent
reports = root.parents[1] / 'spacemit/reports'
output = root / 'report-snapshot-20261012'
assert not output.exists()
output.mkdir()
receipt = {}
for name in ('SUBMISSION-REPORT.md', 'SUBMISSION-EVIDENCE.md', 'SUBMISSION-REPORT.tex',
        'SUBMISSION-REPORT.pdf', 'build-report.py', 'report-template.tex', 'report-format.lua'):
    source = reports / name
    target = output / name
    expected = hashlib.sha256(source.read_bytes()).hexdigest()
    shutil.copy2(source, target)
    assert hashlib.sha256(target.read_bytes()).hexdigest() == expected
    receipt[name] = dict(sha256=expected, bytes=target.stat().st_size)
(output / 'receipts.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(dict(status='pass', files=len(receipt), output=str(output)), indent=2))
