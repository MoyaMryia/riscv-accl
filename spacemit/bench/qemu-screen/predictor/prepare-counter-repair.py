#!/usr/bin/env python3
"""更换周期事件，并证明分项内核的实际字节不变。"""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
from analyze import load,write,sha,seal

HERE=Path(__file__).resolve().parent


def main(a):
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    old=a.payload.resolve();plan=load(old/'plan.json');before=load(a.inventory)
    if sha(old/'measure')!=plan['binary_sha256'] or before['elf_sha256']!=plan['binary_sha256']:
        raise ValueError('旧分项二进制身份不同。')
    for p in old.iterdir():
        if p.is_file() and p.name not in ('measure','SHA256SUMS','BINARY-SHA256SUMS','plan.json'):
            shutil.copy2(p,out/p.name)
    source=(out/'measure.c').read_text()
    source,count=re.subn(r'attr\.type\s*=\s*PERF_TYPE_HARDWARE','attr.type=PERF_TYPE_RAW',source)
    if count==0:
        source,count=re.subn(r'a\.type\s*=\s*PERF_TYPE_HARDWARE','a.type=PERF_TYPE_RAW',source)
    if count!=1:raise ValueError('周期事件类型边界不同。')
    source,count=re.subn(r'(?:attr|a)\.config\s*=\s*PERF_COUNT_HW_CPU_CYCLES',lambda m:m[0].split('.')[0]+'.config=0x22',source)
    if count!=1:raise ValueError('周期事件配置边界不同。')
    (out/'measure.c').write_text(source)
    original=load(old/'build-command.json');argv=[]
    for word in original:
        name=Path(word).name
        argv.append(str(out/name) if name in ('measure.c','kernels.s','measure') else word)
    write(out/'build-command.json',argv)
    with (out/'build-repair.log').open('w') as log:subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,check=True)
    prefix=str(Path(argv[0])).removesuffix('gcc')
    symbols=[r.get('symbol',r['id']) for r in plan['records']]
    subprocess.run(['python3',HERE.parent/'assembly-inventory.py',out/'measure',out/'inventory',
        '--symbol-regex','^'+re.escape(os.path.commonprefix(symbols)),'--tool-prefix',prefix],check=True)
    after=load(out/'inventory/inventory.json');index={f['symbol']:f for f in after['functions']}
    checks=[]
    for f in before['functions']:
        old_bytes=[(i['bytes'],i['encoding']) for i in f['instructions']]
        new_bytes=[(i['bytes'],i['encoding']) for i in index[f['symbol']]['instructions']]
        if old_bytes!=new_bytes:raise ValueError('更换周期事件改变了内核的实际字节。')
        checks.append(dict(symbol=f['symbol'],instruction_bytes_equal=True))
    write(out/'byte-identity.json',dict(old_inventory_sha256=sha(a.inventory),
        new_inventory_sha256=sha(out/'inventory/inventory.json'),functions=checks))
    plan.update(binary_sha256=sha(out/'measure'),origin_binary_sha256=sha(old/'measure'),
        origin_plan_sha256=sha(old/'plan.json'),counter=dict(type='PERF_TYPE_RAW',config='0x22',
            scope='U-mode cycle event; generic cycle filter is not reliable on this board',
            audit_samples_sha256=sha(a.audit),byte_identity_sha256=sha(out/'byte-identity.json')))
    write(out/'plan.json',plan)
    (out/'BINARY-SHA256SUMS').write_text(sha(out/'measure')+'  measure\n')
    runner=(HERE/'run-board-calibration.sh').read_text().replace('timeout 60 ./measure','timeout 300 ./measure')
    (out/'run-board-calibration.sh').write_text(runner);seal(out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('payload',type=Path)
    p.add_argument('--inventory',type=Path,required=True);p.add_argument('--audit',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);main(p.parse_args())
