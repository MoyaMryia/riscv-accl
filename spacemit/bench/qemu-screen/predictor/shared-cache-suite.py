#!/usr/bin/env python3
"""比较配对轨迹在两个线程交错假设下的共享缓存流量。"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import sys
import time
from analyze import load,write,seal

HERE=Path(__file__).resolve().parent


def main(a):
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    source=load(a.source/'results.json')
    if source['status']!='complete':raise ValueError('配对轨迹没有完成。')
    tasks=[(r,q) for r in source['records'] for q in (32,256)]
    def run(task):
        row,q=task;name=row['id']+f'-arm{row["arm"]}';target=out/(name+f'-q{q}')
        argv=[sys.executable,HERE/'shared-cache.py',a.source/name/'program',
            '--quantum',str(q),'--passes','2','--segment-barriers','--output',target]
        with (out/(target.name+'.log')).open('w') as log:subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,check=True)
        print(target.name,flush=True)
        return dict(id=row['id'],arm=row['arm'],quantum=q,result=load(target/'shared-cache.json'))
    start=time.perf_counter()
    with ThreadPoolExecutor(max_workers=4) as pool:records=list(pool.map(run,tasks))
    write(out/'results.json',dict(schema=3,records=records,elapsed_seconds=time.perf_counter()-start,
        scope='same verified binary and complete ROI; declared four-core shared cache; no timing confidence'))
    seal(out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path)
    p.add_argument('--output',type=Path,required=True);main(p.parse_args())
