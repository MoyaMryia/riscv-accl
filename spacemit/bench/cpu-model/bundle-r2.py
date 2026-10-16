#!/usr/bin/env python3
"""发布第二轮冻结模型的标准 Python 便携包。"""
import argparse
import os
from pathlib import Path
import shutil
import tarfile
import tempfile
from common import digest,read,seal,write

HERE=Path(__file__).resolve().parent


def main(a):
    frozen=read(a.work/'frozen-model.json')
    for name,expected in frozen['engine_files'].items():
        if digest(HERE/name)!=expected:
            raise ValueError('引擎与冻结模型不同。')
    if a.output.exists():raise FileExistsError(a.output)
    temporary=a.output.with_name(a.output.name+'.partial')
    with tempfile.TemporaryDirectory(dir=a.output.parent) as directory:
        root=Path(directory)/'k1-cpu-model-r2';root.mkdir()
        for name in frozen['engine_files']:
            shutil.copy2(HERE/name,root/name)
        shutil.copy2(HERE/'replay-r2.py',root/'replay.py')
        for name in ('rank.py','sensitivity.py'):
            shutil.copy2(HERE/name,root/name)
        for name in ('frozen-model.json','frozen-calibration.json','evaluation.json','frozen-protocol.md'):
            shutil.copy2(a.work/name,root/name)
        shutil.copy2(a.work/'payload/plan.json',root/'plan.json')
        seal(root)
        with temporary.open('xb') as stream:
            with tarfile.open(fileobj=stream,mode='w:gz') as archive:
                archive.add(root,arcname=root.name)
            stream.flush();os.fsync(stream.fileno())
        os.link(temporary,a.output);temporary.unlink()
    write(a.receipt,dict(archive_sha256=digest(a.output),bytes=a.output.stat().st_size,model_sha256=digest(a.work/'frozen-model.json')))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--receipt',type=Path,required=True)
    main(p.parse_args())
