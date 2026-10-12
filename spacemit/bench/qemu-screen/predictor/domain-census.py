#!/usr/bin/env python3
"""核验动态计数的实际指令字节，并采集完整算子特征。"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import shlex
import subprocess
import time
from analyze import load,write,sha,seal

HERE=Path(__file__).resolve().parent


def features(census,inventory,arm):
    if census['failure'] or len(census['threads'])!=4:raise ValueError('动态计数必须包含四个有效线程。')
    index={x['address']:x for x in inventory['functions'][0]['instructions']}
    instruction_counts=[];strided=[];total_bytes=0
    for thread in census['threads']:
        count=0;stride_bytes=0;seen=set()
        for site in thread['sites']:
            item=index.get(site['pc'])
            if item is None or int(site['encoding'],16)!=int(item['encoding'],16) or site['size']!=item['bytes']:
                raise ValueError('动态计数的实际指令字节不同。')
            if site['pc'] in seen or site['count']<=0:raise ValueError('动态计数地址重复或计数无效。')
            seen.add(site['pc']);count+=site['count']
            total_bytes+=site['load_bytes']+site['store_bytes']
            if item['mnemonic']=='vlse32.v':stride_bytes+=site['load_bytes']
        if count!=thread['instructions']:raise ValueError('线程动态计数不同。')
        instruction_counts.append(count);strided.append(stride_bytes)
    return [1.0,max(instruction_counts)/1e6,max(strided)/1e6,total_bytes/1e6,float(2 if arm==0 else 1)]


def main(a):
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    payload=a.payload.resolve();plan=load(payload/'plan.json');binary=payload/'matched'
    inv=load(payload/'inventory/inventory.json');f=inv['functions'][0]
    if sha(binary)!=plan['binary_sha256'] or inv['elf_sha256']!=sha(binary):raise ValueError('动态计数二进制身份不同。')
    flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','glib-2.0'],text=True))
    argv=['cc','-std=c11','-O2','-shared','-fPIC','-fvisibility=hidden','-Wall','-Wextra','-Werror',
        '-I'+str(a.header.resolve().parent),str(HERE/'census.c'),'-o',str(out/'census.so'),*flags]
    write(out/'build-command.json',argv)
    with (out/'build.log').open('w') as log:subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,check=True)
    def run(case):
        records=[];digests=[]
        for arm in (0,1):
            target=out/(case['id']+f'-arm{arm}');target.mkdir()
            dump=target/'complete.bin';counts=target/'census.json'
            argv=[str(a.qemu.resolve()),'-R','4G','-cpu','rv64,v=true,vlen=256,elen=64,zfh=true,zvfh=true',
                '-plugin',f'{out}/census.so,start={f["start"]},end={f["start"]+f["size_bytes"]},out={counts}',
                str(binary),'trace',str(case['channels']),str(case['tokens']),str(arm),str(dump)]
            write(target/'command.json',argv);start=time.perf_counter()
            with (target/'qemu.log').open('w') as log:subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
            value=features(load(counts),inv,arm);digests.append(sha(dump))
            records.append(dict(id=case['id'],arm=arm,split=case['split'],features=value,
                elapsed_seconds=time.perf_counter()-start,census_sha256=sha(counts),dump_sha256=sha(dump)))
        if len(set(digests))!=1:raise ValueError('两臂完整转储不同。')
        return records
    start=time.perf_counter()
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:records=[r for rows in pool.map(run,plan['cases']) for r in rows]
    write(out/'features.json',dict(schema=3,domain=plan['domain'],binary_sha256=sha(binary),
        plan_sha256=sha(payload/'plan.json'),feature_names=plan['features'],records=records,
        elapsed_seconds=time.perf_counter()-start,extractor_sha256=sha(Path(__file__)),
        identities=dict(qemu=sha(a.qemu),header=sha(a.header),plugin=sha(out/'census.so'),inventory=sha(payload/'inventory/inventory.json'))))
    seal(out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('payload',type=Path)
    p.add_argument('--qemu',type=Path,required=True);p.add_argument('--header',type=Path,required=True)
    p.add_argument('--jobs',type=int,default=4);p.add_argument('--output',type=Path,required=True);main(p.parse_args())
