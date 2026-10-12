#!/usr/bin/env python3
"""固定官方源码版本、来源和许可，不修改系统工具。"""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

SOURCES = [
    ('llvm/llvm-project','llvmorg-22.1.8',[
        'llvm/lib/Target/RISCV/RISCVSchedSpacemitX60.td',
        'llvm/lib/Target/RISCV/RISCVScheduleV.td',
        'llvm/lib/Target/RISCV/MCA/RISCVCustomBehaviour.cpp','LICENSE.TXT']),
    ('qemu/qemu','v10.0.2',['contrib/plugins/execlog.c','include/qemu/qemu-plugin.h','COPYING']),
    ('securesystemslab/LLVM-MCA-Daemon','main',['README.md','LICENSE','LLVM_COMMIT_ID.txt']),
    ('camel-cdr/rvv-bench','main',['README.md','LICENSE']),
    ('gem5/gem5','stable',['src/arch/riscv/RiscvISA.py','src/arch/riscv/RiscvCPU.py','LICENSE']),
    ('spacemit-com/riscv-ime-extension-spec','master',['README.md','LICENSE']),
    ('spacemit-com/docs-chip','main',['en/key_stone/k1/k1_docs/k1_ds.md'])]


def fetch(url):
    request = urllib.request.Request(url,headers={'User-Agent':'K1-source-audit'})
    with urllib.request.urlopen(request,timeout=45) as stream: return stream.read()


def main(out):
    out.mkdir(parents=True,exist_ok=False)
    records = []
    for repo,ref,paths in SOURCES:
        record = {'repository':repo,'requested_ref':ref,'files':[]}
        records.append(record)
        try:
            commit = json.loads(fetch(f'https://api.github.com/repos/{repo}/commits/{ref}'))['sha']
            record['commit'] = commit
            for path in paths:
                url = f'https://raw.githubusercontent.com/{repo}/{commit}/{path}'
                file_record = {'path':path,'url':url}; record['files'].append(file_record)
                try:
                    data = fetch(url)
                    target = out/(repo.replace('/','--')+'--'+path.replace('/','--'))
                    target.write_bytes(data)
                    file_record.update(file=target.name,sha256=hashlib.sha256(data).hexdigest())
                except Exception as error: file_record['error'] = str(error)
        except Exception as error: record['error'] = str(error)
        (out/'sources.json').write_text(json.dumps(records,indent=2)+'\n')
    (out/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n'
        for p in sorted(out.iterdir()) if p.is_file() and p.name!='SHA256SUMS'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    main(parser.parse_args().output)
