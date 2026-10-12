#!/usr/bin/env python3
"""用新增分项重放已核验的配对轨迹，并核对示例跨机器结果。"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import sys
import time
from analyze import load,write,seal
from k1cost import predict

HERE=Path(__file__).resolve().parent


def main(a):
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    source=load(a.source/'results.json')
    if source['status']!='complete':raise ValueError('配对轨迹尚未完成。')
    def run(row):
        name=row['id']+f'-arm{row["arm"]}';program=a.source/name/'program';target=out/name;target.mkdir()
        start=time.perf_counter();cost=predict(program,a.profiles,target)
        return dict(id=row['id'],arm=row['arm'],cost=cost,cost_seconds=time.perf_counter()-start)
    start=time.perf_counter()
    with ThreadPoolExecutor(max_workers=4) as pool:records=list(pool.map(run,source['records']))
    write(out/'results.json',dict(records=records,elapsed_seconds=time.perf_counter()-start,
        scope='same binary ROI; external call and wait costs remain unknown'))
    subprocess.run([sys.executable,HERE/'family-demo.py','--output',out/'family-demo'],check=True)
    seal(out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path)
    p.add_argument('--profiles',type=Path,nargs='+',required=True);p.add_argument('--output',type=Path,required=True)
    main(p.parse_args())
