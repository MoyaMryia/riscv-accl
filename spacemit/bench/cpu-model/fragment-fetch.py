#!/usr/bin/env python3
"""完整接收并核验片段归档后才发布目录，不重复启动原生批次。"""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import tarfile
from common import digest,write


def receive(host,remote,output):
    output=Path(output).absolute();partial=output.with_name(output.name+'.partial')
    if output.exists():raise ValueError('接收目录已经存在。')
    partial.mkdir(parents=True,exist_ok=False)
    try:
        argv=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','-o','ServerAliveInterval=5',
              '-o','ServerAliveCountMax=2',host,'cat -- '+shlex.quote(str(Path(remote)/'native-archive-receipt.json'))]
        response=subprocess.run(argv,capture_output=True,text=True,check=True,timeout=30)
        receipt=json.loads(response.stdout)
        if type(receipt['archive_bytes']) is not int or not 0<receipt['archive_bytes']<=128*1024*1024:
            raise ValueError('归档大小超出本入口的 128 MiB 接收预算。')
        write(partial/'native-archive-receipt.json',receipt)
        archive=partial/'native.tar.gz.partial'
        source=host+':'+shlex.quote(str(Path(remote)/'native.tar.gz'))
        subprocess.run(['scp','-o','BatchMode=yes','-o','ConnectTimeout=8','-o','ServerAliveInterval=5',
                        '-o','ServerAliveCountMax=2',source,str(archive)],check=True,timeout=180)
        if archive.stat().st_size!=receipt['archive_bytes'] or digest(archive)!=receipt['archive_sha256']:
            raise ValueError('完整归档身份不同。')
        with tarfile.open(archive) as stream:
            for member in stream.getmembers():
                path=(partial/member.name).resolve()
                if not path.is_relative_to((partial/'native').resolve()) or member.issym() or member.islnk():
                    raise ValueError('归档路径或链接未覆盖。')
            stream.extractall(partial)
        native=partial/'native'
        if (native/'exit-status').read_text().strip()!='0':raise ValueError('原生批次未成功结束。')
        count=0
        for line in (native/'SHA256SUMS').read_text().splitlines():
            expected,name=line.split('  ',1);path=(native/name).resolve()
            if not path.is_relative_to(native.resolve()) or digest(path)!=expected:
                raise ValueError('原生证据收据不同。')
            count+=1
        archive.rename(partial/'native.tar.gz')
        write(partial/'transfer-receipt.json',dict(status='passed',host=host,remote=str(remote),
              archive_sha256=receipt['archive_sha256'],native_receipt_entries=count,native_restart=False))
        partial.rename(output)
    except Exception as error:
        write(partial/'transfer-failure.json',dict(status='failed',error=str(error),published=False,native_restart=False))
        raise
    return dict(status='passed',output=str(output),native_receipt_entries=count)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host',choices=['musepipro-wg','server-wg'],required=True)
    parser.add_argument('--remote',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();print(json.dumps(receive(a.host,a.remote,a.output),ensure_ascii=False))
