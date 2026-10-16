#!/usr/bin/env python3
"""关闭完整归档后发布文件，并拒绝覆盖已有归档。"""
import argparse
import os
from pathlib import Path
import tarfile
from common import digest, write


def publish(root,target):
    root,target=Path(root).resolve(),Path(target).resolve()
    if target.is_relative_to(root):
        raise ValueError('归档必须位于工作目录之外。')
    if target.exists():
        raise FileExistsError(target)
    temporary=target.with_name(target.name+'.partial')
    with temporary.open('xb') as stream:
        with tarfile.open(fileobj=stream,mode='w:gz') as archive:
            archive.add(root,arcname=root.name)
        stream.flush();os.fsync(stream.fileno())
    os.link(temporary,target)
    temporary.unlink()
    return dict(archive_sha256=digest(target),bytes=target.stat().st_size)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('root',type=Path)
    p.add_argument('output',type=Path)
    p.add_argument('--receipt',type=Path,required=True)
    a=p.parse_args()
    write(a.receipt,publish(a.root,a.output))
