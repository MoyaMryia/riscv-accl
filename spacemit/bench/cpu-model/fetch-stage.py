#!/usr/bin/env python3
"""完整下载并核验阶段证据后才发布本地目录。"""
import argparse
import os
from pathlib import Path
import shlex
import subprocess
import tarfile
import tempfile
from audit import receipts
from common import digest,write

REMOTE='''
import hashlib,pathlib,sys,tarfile
root=pathlib.Path(sys.argv[1]);run=root/('run-'+sys.argv[2])
if (run/'exit-status').read_text().strip()!='0' or (run/'phase').read_text().strip()!='complete':
    raise ValueError('stage is not complete')
seen=set()
for line in (run/'SHA256SUMS').read_text().splitlines():
    want,name=line.split('  ',1);p=(root/name).resolve()
    if not p.is_relative_to(run.resolve()) or p in seen or hashlib.sha256(p.read_bytes()).hexdigest()!=want:
        raise ValueError('receipt differs')
    seen.add(p)
actual={p.resolve() for p in run.rglob('*') if p.is_file() and p.name!='SHA256SUMS'}
if seen!=actual:raise ValueError('receipt is incomplete')
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|gz') as archive:
    archive.add(run,arcname=run.name)
'''


def publish(archive,root,stage):
    root=Path(root);name='run-'+stage;target=root/name
    if target.exists():raise FileExistsError(target)
    with tempfile.TemporaryDirectory(prefix='stage-download-',dir=root) as directory:
        with tarfile.open(archive) as source:
            members=source.getmembers()
            for item in members:
                p=Path(item.name)
                if p.is_absolute() or '..' in p.parts or not p.parts or p.parts[0]!=name or not (item.isfile() or item.isdir()):
                    raise ValueError('归档路径或条目类型不同。')
            source.extractall(directory)
        run=Path(directory)/name
        count=receipts(run)
        if (run/'exit-status').read_text().strip()!='0' or (run/'phase').read_text().strip()!='complete':
            raise ValueError('下载阶段未完整结束。')
        if target.exists():raise FileExistsError(target)
        os.rename(run,target)
    return count


def main(a):
    a.output.mkdir(parents=True,exist_ok=True)
    archive=a.output/('transfer-'+a.stage+'.tar.gz')
    partial=archive.with_name(archive.name+'.partial')
    if archive.exists() or (a.output/('run-'+a.stage)).exists():raise FileExistsError('阶段或传输归档已存在。')
    argv=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','ServerAliveInterval=5','-o','ServerAliveCountMax=3',
          a.host,'python3 - '+shlex.quote(str(a.root))+' '+shlex.quote(a.stage)]
    with partial.open('xb') as stream:
        result=subprocess.run(argv,input=REMOTE.encode(),stdout=stream,stderr=subprocess.PIPE,timeout=60)
        stream.flush();os.fsync(stream.fileno())
    if result.returncode:raise RuntimeError(result.stderr.decode(errors='replace'))
    os.link(partial,archive);partial.unlink()
    count=publish(archive,a.output,a.stage)
    write(a.output/('transfer-'+a.stage+'-receipt.json'),dict(status='verified',host=a.host,root=str(a.root),
        stage=a.stage,archive_sha256=digest(archive),receipt_entries=count))
    print(f'阶段下载与收据核验通过：{count} 项。')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host',choices=['musepipro-wg','server-wg'],required=True)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--stage',choices=['training','calibration','test'],required=True)
    p.add_argument('--output',type=Path,required=True)
    main(p.parse_args())
