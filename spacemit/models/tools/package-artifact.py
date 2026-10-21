#!/usr/bin/env python3
"""把模型产物与加工收据打成一个可核验的压缩包。

压缩包内的模型放在 model/ 下，收据放在 receipts/ 下。
打包前计算文件身份；打包后重新读取成员与大小。
目标已存在时拒绝覆盖。
"""
import argparse
import hashlib
import json
import sys
import tarfile
from pathlib import Path

FORMAT = 1


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def members_of(gguf, receipts):
    """返回 (包内路径, 源文件) 列表。"""
    pairs = [(Path('model') / gguf.name, gguf)]
    for path in sorted(receipts.rglob('*')):
        if path.is_file():
            pairs.append((Path('receipts') / path.relative_to(receipts), path))
    return pairs


def pack(gguf, receipts, name, output_dir, *, expect_sha256=None, epoch=0):
    """生成压缩包与收据，返回两者的路径。"""
    gguf, receipts, output_dir = Path(gguf), Path(receipts), Path(output_dir)
    if not gguf.is_file():
        raise ValueError('missing model artifact: ' + str(gguf))
    if not receipts.is_dir():
        raise ValueError('missing receipts directory: ' + str(receipts))
    if not name or '/' in name or name.startswith('.'):
        raise ValueError('invalid package name')
    observed = sha256(gguf)
    if expect_sha256 is not None and observed != expect_sha256:
        raise ValueError('artifact digest differs from the expected value')
    pairs = members_of(gguf, receipts)
    if len(pairs) < 2:
        raise ValueError('receipts directory has no files')
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / (name + '.tar.gz')
    manifest_path = output_dir / (name + '.manifest.json')
    receipt_path = output_dir / (name + '.receipt.json')
    for path in (archive, manifest_path, receipt_path):
        if path.exists():
            raise ValueError('output already exists: ' + str(path))
    manifest = {'format': FORMAT, 'name': name, 'artifact_sha256': observed,
                'files': [{'path': str(arc), 'size': source.stat().st_size,
                           'sha256': sha256(source)} for arc, source in pairs]}
    manifest_path.write_text(json.dumps(manifest, indent=1, sort_keys=True))
    with tarfile.open(archive, 'w:gz', format=tarfile.PAX_FORMAT) as tar:
        for arc, source in pairs + [(Path(manifest_path.name), manifest_path)]:
            info = tar.gettarinfo(str(source), arcname=str(arc))
            info.mtime, info.uid, info.gid = epoch, 0, 0
            info.uname = info.gname = ''
            with source.open('rb') as stream:
                tar.addfile(info, stream)
    expected = {str(arc): source.stat().st_size
                for arc, source in pairs + [(Path(manifest_path.name), manifest_path)]}
    with tarfile.open(archive, 'r:gz') as tar:
        members = {member.name: member.size for member in tar.getmembers()}
    if members != expected:
        raise ValueError('archive members differ from the manifest')
    receipt = {'format': FORMAT, 'name': name, 'archive': archive.name,
               'archive_size': archive.stat().st_size,
               'archive_sha256': sha256(archive),
               'artifact_sha256': observed,
               'manifest_sha256': sha256(manifest_path),
               'members': len(members)}
    receipt_path.write_text(json.dumps(receipt, indent=1, sort_keys=True))
    return archive, receipt_path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gguf', type=Path, required=True)
    parser.add_argument('--receipts', type=Path, required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expect-sha256')
    parser.add_argument('--epoch', type=int, default=0)
    args = parser.parse_args(argv)
    try:
        archive, receipt = pack(args.gguf, args.receipts, args.name, args.output,
                                expect_sha256=args.expect_sha256, epoch=args.epoch)
    except (ValueError, OSError) as error:
        print('PACKAGE_FAILED', type(error).__name__ + ': ' + str(error))
        return 2
    print('PACKAGE_OK', archive, receipt)
    return 0


if __name__ == '__main__':
    sys.exit(main())
