#!/usr/bin/env python3
"""独立核验证据文件、嵌套收据与归档散列，不解包归档。"""
import argparse
import hashlib
import json
from pathlib import Path
import posixpath
import re
import tarfile


def digest(stream):
    value = hashlib.sha256()
    for block in iter(lambda: stream.read(1048576), b''):
        value.update(block)
    return value.hexdigest()


def entries(text):
    if not text.strip():
        raise ValueError('收据必须至少包含一个文件。')
    for line in text.splitlines():
        if not re.fullmatch(r'[0-9a-fA-F]{64} [ *].+', line):
            raise ValueError('收据格式无效。')
        yield line[:64].lower(), line[66:]


def receipt(path, base):
    base = base.resolve()
    checked, failures = 0, []
    for expected, name in entries(path.read_text()):
        target = (base / name).resolve()
        if not target.is_relative_to(base):
            failures.append(dict(path=name, status='outside-base'))
        elif not target.is_file():
            failures.append(dict(path=name, status='missing'))
        else:
            with target.open('rb') as stream:
                actual = digest(stream)
            checked += 1
            if expected != actual:
                failures.append(dict(path=name, status='hash-mismatch', expected=expected, actual=actual))
    return dict(receipt_entries_checked=checked, failures=failures)


def archive(path, expected, bases=None):
    bases=bases or {}
    for base in bases.values():
        value=posixpath.normpath(base)
        if value.startswith('/') or value=='..' or value.startswith('../'):
            raise ValueError('声明的收据基目录超出归档。')
    with path.open('rb') as stream:
        actual = digest(stream)
    if actual != expected:
        return dict(archive_sha256=actual, failures=[dict(status='archive-hash-mismatch', expected=expected)])
    hashes, receipts, links = {}, {}, {}
    with tarfile.open(path, 'r|*') as source:
        for member in source:
            name = posixpath.normpath(member.name)
            if name.startswith('/') or name == '..' or name.startswith('../'):
                raise ValueError('归档路径超出根目录。')
            if member.issym():
                links[name] = posixpath.normpath(posixpath.join(posixpath.dirname(name), member.linkname))
            elif member.islnk():
                links[name] = posixpath.normpath(member.linkname)
            elif member.isfile():
                if name in hashes:
                    raise ValueError('归档包含重复文件路径。')
                stream = source.extractfile(member)
                if name.endswith('SHA256SUMS'):
                    data = stream.read()
                    hashes[name] = hashlib.sha256(data).hexdigest()
                    receipts[name] = data.decode()
                else:
                    hashes[name] = digest(stream)
    for name, target in links.items():
        visited = {name}
        while target in links and target not in visited:
            visited.add(target)
            target = links[target]
        if target in hashes:
            hashes[name] = hashes[target]
    failures, checked = [], 0
    for source in set(bases)-set(receipts):
        failures.append(dict(receipt=source,status='declared-receipt-missing'))
    if not receipts:
        failures.append(dict(status='no-receipts'))
    for source, text in receipts.items():
        for expected, name in entries(text):
            target = posixpath.normpath(posixpath.join(bases.get(source,posixpath.dirname(source)), name))
            if target not in hashes:
                failures.append(dict(receipt=source, path=name, status='missing'))
            else:
                checked += 1
                if expected != hashes[target]:
                    failures.append(dict(receipt=source, path=name, status='hash-mismatch'))
    return dict(archive_sha256=actual, files_hashed=len(hashes), receipt_files=len(receipts),
                receipt_entries_checked=checked, declared_receipt_bases=bases,failures=failures)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument('--archive', type=Path)
    group.add_argument('--receipt', type=Path)
    p.add_argument('--expected-sha256')
    p.add_argument('--base', type=Path)
    p.add_argument('--receipt-bases',type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        p.error('输出文件必须不存在。')
    if a.archive:
        if not a.expected_sha256 or not re.fullmatch('[0-9a-fA-F]{64}', a.expected_sha256):
            p.error('必须提供归档的原始 SHA-256。')
        bases=json.loads(a.receipt_bases.read_text()) if a.receipt_bases else None
        result = archive(a.archive, a.expected_sha256.lower(),bases)
    else:
        if a.base is None:
            p.error('必须显式提供收据路径的基目录。')
        result = receipt(a.receipt, a.base)
    result['status'] = 'verified' if not result['failures'] else 'evidence-invalid'
    a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    if result['failures']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
