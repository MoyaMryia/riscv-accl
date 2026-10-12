"""恢复原始证据的全部文件名，并核验完整收据。"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import tarfile

work = Path('/tmp/k1-combined-repair-work')
repo = Path('/home/moyamryia/Projects/riscv-accl')
destination = repo/'spacemit/reports/raw/k1-combined-failure-20261010-162500'
destination.mkdir(exist_ok=False)
with tarfile.open(work/'failed-full-deduplicated.tar.gz') as archive:
    archive.extractall(destination, filter='data')
expected = {}
for line in (work/'failed-board-SHA256SUMS').read_text().splitlines():
    value, name = line.split('  ',1)
    expected[name.removeprefix('./')] = value
available = {}
for name, value in expected.items():
    path = destination/name
    if path.is_file():
        available.setdefault(value,path)
for name, value in expected.items():
    path = destination/name
    if not path.exists():
        if not name.endswith('.bin'):
            raise ValueError('missing non-dump evidence: '+name)
        os.link(available[value],path)
for name, value in expected.items():
    actual = hashlib.sha256((destination/name).read_bytes()).hexdigest()
    if actual != value:
        raise ValueError('raw evidence hash differs: '+name)
shutil.copyfile(work/'failed-board-SHA256SUMS',destination/'board-SHA256SUMS')
shutil.copyfile(work/'native-independent-review.json',destination/'native-independent-review.json')
(destination/'local-review.json').write_text(json.dumps({
    'original_files_verified':len(expected),'duplicate_dumps_restored':8,
    'native_operator_gate':'pass','failure':'原发布库缺少候选专用日志，旧夹具误判。',
    'model_cold_requests':0,'model_gain':'待验证','original_records_changed':False,
    'algorithm_changed':False,'current_controller':'combined-fixture-r3',
    'repair_monitor':'k1-6'},ensure_ascii=False,indent=2)+'\n')
files = sorted(p for p in destination.rglob('*') if p.is_file())
(destination/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(destination).as_posix()+'\n' for p in files))
report = repo/'spacemit/reports/2026-10-10-combined-candidates-run.md'
report.write_text(report.read_text()+'\n原失败完整证据已同步至 [失败证据目录](raw/k1-combined-failure-20261010-162500/)。\n原 400 个文件均与板端收据相同，八个重复转储已恢复全部文件名。\n')
print(json.dumps({'raw_directory':str(destination),'verified_original_files':len(expected)},ensure_ascii=False),flush=True)
