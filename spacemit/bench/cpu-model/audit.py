#!/usr/bin/env python3
"""核对固定循环的实际机器码、归档收据与完整转储。"""
import argparse
from pathlib import Path
import re
from common import digest, read, write


def binary(plan, text):
    starts={name:int(address,16) for address,name in re.findall(r'^([0-9a-f]+) <(cpu_\d+)>:',text,re.M)}
    items={int(address,16):(word,asm) for address,word,asm in re.findall(r'^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.+)$',text,re.M)}
    if set(starts)!={r['id'] for r in plan['records']}:
        raise ValueError('实际函数清单不同。')
    for row in plan['records']:
        start=starts[row['id']]+128
        if start%64:
            raise ValueError('循环入口未按 64 字节对齐。')
        for index,op in enumerate(row['instructions']):
            word,asm=items[start+4*index]
            if op['kind']=='ime':
                valid=int(word,16)==int(op['asm'].split()[1],16)
            else:
                valid=re.sub(r'\s+','',asm.split('#')[0])==re.sub(r'\s+','',op['asm'])
            if not valid:
                raise ValueError(f'实际指令不同：{row["id"]} {index}')
        end=start+4*len(row['instructions'])
        decrement=int(items[end][0],16)
        if decrement!=0xfff50513:
            raise ValueError('循环计数指令不同。')
        branch=int(items[end+4][0],16)
        displacement=((branch>>31)<<12)|(((branch>>7)&1)<<11)|(((branch>>25)&63)<<5)|(((branch>>8)&15)<<1)
        if displacement&4096:
            displacement-=8192
        if branch&0x1fff07f!=0x51063 or end+4+displacement!=start:
            raise ValueError('循环回边不同。')
    return dict(functions=len(starts),instructions=sum(len(r['instructions']) for r in plan['records']),loop_alignment_bytes=64)


def receipts(run):
    run=Path(run)
    lines=(run/'SHA256SUMS').read_text().splitlines()
    seen=set()
    for line in lines:
        expected,name=line.split('  ',1)
        path=(run.parent/name).resolve()
        if not path.is_relative_to(run.resolve()) or path in seen or digest(path)!=expected:
            raise ValueError('收据路径、身份或唯一性不同。')
        seen.add(path)
    actual={p.resolve() for p in run.rglob('*') if p.is_file() and p.name!='SHA256SUMS'}
    if actual!=seen:
        raise ValueError('收据没有覆盖全部文件。')
    return len(lines)


def main(a):
    plan=read(a.payload/'plan.json')
    if digest(a.payload/'measure')!=plan['binary_sha256']:
        raise ValueError('实际二进制身份不同。')
    result=binary(plan,(a.payload/'disassembly.txt').read_text())
    result['binary_sha256']=plan['binary_sha256']
    result['runs']=[]
    for run in a.run:
        stage=run.name.removeprefix('run-')
        expected={f'{r["id"]}-{n}.bin' for r in plan['records'] if r['split']==stage for n in plan['dump_lengths']}
        files={p.name for p in (run/'dumps').glob('*.bin')}
        if files!=expected:
            raise ValueError('完整转储清单不同。')
        for name in files:
            if (run/'dumps'/name).read_bytes()!=(a.qemu_dumps/name).read_bytes():
                raise ValueError('原生与 QEMU 完整转储不同。')
        result['runs'].append(dict(stage=stage,receipt_entries=receipts(run),complete_dump_pairs=len(files)))
    result['status']='passed'
    write(a.output,result)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--payload',type=Path,required=True)
    p.add_argument('--qemu-dumps',type=Path,required=True)
    p.add_argument('--run',type=Path,action='append',default=[])
    p.add_argument('--output',type=Path,required=True)
    main(p.parse_args())
