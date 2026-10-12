#!/usr/bin/env python3
"""对同一加载消费二进制生成完整轨迹和冻结模型预测。"""
import argparse
from pathlib import Path
import subprocess
import time
from analyze import load, write, sha, seal
from k1cost import compile_program, predict


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('payload',type=Path)
    p.add_argument('--qemu',type=Path,required=True)
    p.add_argument('--plugin',type=Path,required=True)
    p.add_argument('--cpu',default='rv64,v=true,vlen=256,elen=64')
    p.add_argument('--profiles',type=Path,nargs='+',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    out=a.output.resolve();binary=(a.payload/'measure').resolve();plan=load(a.payload/'plan.json')
    inventory=load(a.payload/'inventory/inventory.json')
    if sha(binary)!=plan['binary_sha256'] or inventory['elf_sha256']!=plan['binary_sha256']:
        raise ValueError('加载消费二进制身份不同。')
    functions={f['symbol']:f for f in inventory['functions']}
    if set(functions)!={r['id'] for r in plan['records']}:
        raise ValueError('热点库存与计划不同。')
    records=[];dumps={};start=time.perf_counter()
    for row in plan['records']:
        function=functions[row['id']]
        for loops in plan['trace_lengths']:
            target=out/row['id']/str(loops);target.mkdir(parents=True)
            inv={**inventory,'functions':[function]};write(target/'inventory.json',inv)
            first=function['start'];end=first+function['size_bytes']
            argv=[str(a.qemu.resolve()),'-R','4G','-cpu',a.cpu,
                '-plugin',f'{a.plugin.resolve()},start={first},end={end},out={target}/trace,max=65536',
                str(binary),'trace',row['id'],str(loops),str(target/'complete.bin')]
            write(target/'command.json',argv)
            with (target/'qemu.log').open('w') as log:
                subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=30)
            key=(row['group'],row['operations'],loops)
            value=sha(target/'complete.bin')
            if key in dumps and dumps[key]!=value:
                raise ValueError('两个算法臂的完整有效输出不同。')
            dumps[key]=value
            program=target/'program';program.mkdir()
            meta=compile_program(target,target/'inventory.json',program)
            if not meta['complete'] or len(meta['threads'])!=1:
                raise ValueError('单线程轨迹不完整。')
            costdir=target/'cost';costdir.mkdir();cost=predict(program,a.profiles,costdir)
            if cost['model_sha256']!=plan['frozen_component_model_sha256']:
                raise ValueError('预测模型身份不同。')
            records.append(dict(id=row['id'],group=row['group'],arm=row['arm'],unroll=row['operations'],
                loops=loops,dump_sha256=value,program=meta,cost=cost))
            write(out/'results.json',dict(schema=4,status='running',records=records))
    write(out/'results.json',dict(schema=4,status='complete',records=records,
        elapsed_seconds=time.perf_counter()-start,plan_sha256=sha(a.payload/'plan.json'),
        binary_sha256=sha(binary),qemu_sha256=sha(a.qemu),plugin_sha256=sha(a.plugin),
        qemu_cpu=a.cpu,trace_driver_sha256=sha(Path(__file__)),
        scope='same binary; two loop lengths remove fixed entry and exit contribution; hot read-only CPU 0 schedule pair'))
    seal(out)
