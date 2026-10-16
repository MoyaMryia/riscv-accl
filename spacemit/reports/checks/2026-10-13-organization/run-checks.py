#!/usr/bin/env python3
"""复核本次入口、已有矩阵与原始文件保留状态。"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import unicodedata
from urllib.parse import unquote
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def prose(text):
    return re.sub(r'^```.*?^```[^\n]*$', '', text, flags=re.M | re.S)


def slug(text):
    text = re.sub(r'<[^>]*>', '', text).replace('`', '').lower()
    text = ''.join(c for c in text if c in '_- ' or c.isalnum() or unicodedata.category(c).startswith('L'))
    return text.replace(' ', '-')


def check_links(files):
    checked = 0
    errors = []
    for name in files:
        path = ROOT / name
        text = prose(path.read_text())
        for match in re.finditer(r'\[[^\]\n]+\]\(([^)\n]+)\)', text):
            href = match.group(1).strip().strip('<>')
            if re.match(r'[a-zA-Z][a-zA-Z0-9+.-]*:', href):
                continue
            local, _, anchor = unquote(href).partition('#')
            target = path.parent / local if local else path
            checked += 1
            if not target.exists():
                errors.append({'file': name, 'link': href, 'error': 'target absent'})
            elif anchor and target.suffix == '.md':
                headings = re.findall(r'^#{1,6}\s+(.+?)\s*#*$', prose(target.read_text()), re.M)
                if anchor not in {slug(h) for h in headings}:
                    errors.append({'file': name, 'link': href, 'error': 'anchor absent'})
    return {'documents': len(files), 'local_links': checked, 'errors': errors}


def check_raw(before):
    baseline = json.loads(before.read_text())
    current = {str(p.relative_to(ROOT)): digest(p) for p in (ROOT / 'spacemit/reports/raw').rglob('*') if p.is_file()}
    changed = [name for name, value in baseline.items() if current.get(name) != value]
    added = sorted(set(current) - set(baseline))
    return {'before_files': len(baseline), 'after_files': len(current),
            'changed_or_missing': changed, 'added': added,
            'before_manifest_sha256': digest(before)}


def check_existing_changes(before, edited_files):
    def sections(text):
        result = {}
        for section in re.split(r'(?=^diff --git )', text, flags=re.M):
            match = re.match(r'diff --git a/(\S+) b/\S+\n', section)
            if match:
                result[match.group(1)] = section
        return result
    prior = sections(before.read_text())
    current = sections(subprocess.check_output(['git', 'diff', '--binary'], cwd=ROOT, text=True))
    retained = sorted(set(prior) - set(edited_files))
    return {'files': retained, 'changed': [name for name in retained if prior[name] != current.get(name)],
            'before_patch_sha256': digest(before)}


def check_receipts():
    results = []
    for name in ['k1-live-inspect-20261013', 'k1-ime-scalar-schedule-20261013', 'k1-tcm-access-20261013']:
        folder = ROOT / 'spacemit/reports/raw' / name
        receipt = folder / 'collection-receipt.json'
        data = json.loads(receipt.read_text())
        errors = []
        archived = 0
        if 'files_sha256' in data:
            hashes = data['files_sha256']
            for file, value in hashes.items():
                path = folder / file
                if not path.is_file() or digest(path) != value:
                    errors.append(file)
        else:
            hashes = dict((line.split(None, 1)[1].removeprefix('./'), line.split(None, 1)[0])
                          for line in (folder / 'SHA256SUMS').read_text().splitlines())
            archive_path = folder / 'evidence.tar.gz'
            if digest(archive_path) != data['archive_sha256']:
                errors.append('archive checksum')
            if len(hashes) != data['files_checked']:
                errors.append('checksum entry count')
            with tarfile.open(archive_path) as archive:
                members = {m.name.removeprefix('./'): m for m in archive.getmembers() if m.isfile()}
                for file, value in hashes.items():
                    path = folder / file
                    if path.is_file():
                        actual = digest(path)
                    elif file in members:
                        with archive.extractfile(members[file]) as stream:
                            h = hashlib.sha256()
                            for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
                                h.update(chunk)
                            actual = h.hexdigest()
                        archived += 1
                    else:
                        errors.append(file)
                        continue
                    if actual != value:
                        errors.append(file)
        results.append({'directory': str(folder.relative_to(ROOT)),
                        'receipt_sha256': digest(receipt), 'files': len(hashes),
                        'files_read_from_archive': archived, 'errors': errors})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-before', type=Path, required=True)
    parser.add_argument('--reuse-tool-results', action='store_true')
    args = parser.parse_args()
    summary = {'started_at': datetime.datetime.now(ZoneInfo('Asia/Singapore')).isoformat(),
               'working_directory': str(ROOT), 'checks': []}
    failed = False
    commands = [
        [sys.executable, 'spacemit/release/test-release.py'],
        [sys.executable, 'spacemit/models/tools/test_reproduction.py'],
        [sys.executable, 'spacemit/bench/verify-results-matrix.py',
         'spacemit/reports/2026-09-27-resumed-measures.md', 'spacemit/reports/raw/2026-09-25-lifecycle'],
        ['git', 'diff', '--check'],
    ]
    previous = json.loads((HERE / 'summary.json').read_text()) if args.reuse_tool_results else None
    if previous:
        summary['checks'] = previous['checks'][:3]
        summary['tool_check_run'] = previous.get('tool_check_run',
                                                {'started_at': previous['started_at'], 'finished_at': previous['finished_at']})
        for check in summary['checks']:
            failed |= check['exit_status'] != 0 or digest(HERE / check['log']) != check['log_sha256']
    for index, command in enumerate(commands, 1):
        if previous and index <= 3:
            continue
        log = HERE / f'{index:02d}-command.log'
        with log.open('w') as out:
            result = subprocess.run(command, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, timeout=180)
        summary['checks'].append({'command': command, 'exit_status': result.returncode,
                                  'log': log.name, 'log_sha256': digest(log)})
        failed |= result.returncode != 0
    files = json.loads((HERE / 'entry-files.json').read_text())
    links = check_links(files)
    raw = check_raw(args.raw_before)
    existing = check_existing_changes(args.raw_before.with_name('worktree-before.patch'), files)
    receipts = check_receipts()
    for name, data in [('links.json', links), ('raw-preservation.json', raw),
                       ('preexisting-changes.json', existing), ('receipts.json', receipts)]:
        (HERE / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    failed |= bool(links['errors'] or raw['changed_or_missing'] or raw['added'])
    failed |= any(r['errors'] for r in receipts)
    failed |= bool(existing['changed'])
    summary.update(status='failed' if failed else 'passed',
                   local_links=links['local_links'], raw_files=raw['after_files'],
                   receipt_files=sum(r['files'] for r in receipts),
                   preserved_tracked_changes=len(existing['files']),
                   entry_files_sha256={name: digest(ROOT / name) for name in files},
                   check_script_sha256=digest(Path(__file__)),
                   requirements_sha256=digest(ROOT / 'Requirements.md'),
                   finished_at=datetime.datetime.now(ZoneInfo('Asia/Singapore')).isoformat())
    (HERE / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return int(failed)


if __name__ == '__main__':
    sys.exit(main())
