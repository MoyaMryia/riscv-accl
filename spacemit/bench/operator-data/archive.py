#!/usr/bin/env python3
"""归档已完成的批次，只在文件关闭后公开归档路径。"""
import argparse
import json
import os
from pathlib import Path
import tarfile

import summarize


def publish(root, target, build=None):
    root, target = Path(root).resolve(), Path(target).resolve()
    if target.is_relative_to(root):
        raise ValueError('archive must be outside the batch')
    if target.exists():
        raise FileExistsError(target)
    temporary = target.with_name(target.name+'.partial')
    if build is None:
        summarize.summarize(root)
        if (root/'exit-status').read_text().strip() != '0':
            raise ValueError('batch exit status')
        def build(handle):
            with tarfile.open(fileobj=handle, mode='w:gz') as archive:
                archive.add(root, arcname=root.name)
    with temporary.open('xb') as handle:
        build(handle)
        handle.flush()
        os.fsync(handle.fileno())
    # 硬链接同时公开完整文件，并拒绝覆盖已有路径。
    os.link(temporary, target)
    temporary.unlink()
    return dict(status='published', archive=str(target), bytes=target.stat().st_size,
                sha256=summarize.file_hash(target))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path)
    p.add_argument('target', type=Path)
    p.add_argument('--receipt', type=Path, required=True)
    args = p.parse_args()
    if args.receipt.exists():
        raise FileExistsError(args.receipt)
    value = publish(args.root, args.target)
    with args.receipt.open('x') as handle:
        json.dump(value, handle, indent=2)
        handle.write('\n')
    print(json.dumps(value))
