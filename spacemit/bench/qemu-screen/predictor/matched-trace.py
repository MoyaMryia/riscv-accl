#!/usr/bin/env python3
"""生成同一卷积二进制的完整热点轨迹和成本记录。"""
import argparse
from pathlib import Path
import shlex
import subprocess
import time
from analyze import load,write,sha,seal
from k1cost import compile_program,predict

HERE=Path(__file__).resolve().parent


def main(a):
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    payload=a.payload.resolve();plan=load(payload/'plan.json');binary=payload/'matched'
    if sha(binary)!=plan['binary_sha256']:raise ValueError('配对二进制身份不同。')
    inv=payload/'inventory/inventory.json';function=load(inv)['functions'][0]
    flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','glib-2.0'],text=True))
    argv=['cc','-std=c11','-O2','-shared','-fPIC','-fvisibility=hidden','-Wall','-Wextra','-Werror',
        '-I'+str(a.header.resolve().parent),str(HERE/'trace.c'),'-o',str(out/'trace.so'),*flags]
    write(out/'build-command.json',argv)
    with (out/'build.log').open('w') as log:subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,check=True)
    results=[];start=time.perf_counter()
    for case in plan['cases']:
        digests=[]
        for arm in (0,1):
            target=out/(case['id']+f'-arm{arm}');target.mkdir()
            trace=target/'trace';dump=target/'complete.bin'
            first=function['start'];end=first+function['size_bytes']
            argv=[str(a.qemu.resolve()),'-R','4G','-cpu','rv64,v=true,vlen=256,elen=64,zfh=true,zvfh=true',
                  '-plugin',f'{out}/trace.so,start={first},end={end},out={trace},max=4000000',
                  str(binary),'trace',str(case['channels']),str(case['tokens']),str(arm),str(dump)]
            write(target/'command.json',argv);begin=time.perf_counter()
            with (target/'qemu.log').open('w') as log:subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
            elapsed=time.perf_counter()-begin;digests.append(sha(dump))
            program=target/'program';program.mkdir();meta=compile_program(target,inv,program)
            if not meta['complete'] or len(meta['threads'])!=4:raise ValueError('完整四线程轨迹缺失。')
            costdir=target/'cost';costdir.mkdir();begin=time.perf_counter();cost=predict(program,a.profiles,costdir)
            results.append(dict(id=case['id'],arm=arm,binary_sha256=sha(binary),dump_sha256=sha(dump),
                trace_seconds=elapsed,cost_seconds=time.perf_counter()-begin,program=meta,cost=cost))
            write(out/'results.json',dict(schema=3,records=results,status='running'))
        if len(set(digests))!=1:raise ValueError('两臂完整转储不同。')
    write(out/'results.json',dict(schema=3,records=results,status='complete',elapsed_seconds=time.perf_counter()-start,
        identities=dict(binary=sha(binary),inventory=sha(inv),qemu=sha(a.qemu),plugin=sha(out/'trace.so')),
        scope='same operator binary; ROI excludes callees; native comparison must state this gap'))
    seal(out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('payload',type=Path)
    p.add_argument('--qemu',type=Path,required=True);p.add_argument('--header',type=Path,required=True)
    p.add_argument('--profiles',type=Path,nargs='+',required=True);p.add_argument('--output',type=Path,required=True)
    main(p.parse_args())
