#!/usr/bin/env python3
"""预先冻结卷积形状、数据分组和配对二进制。"""
import argparse
from pathlib import Path
import random
import shutil
from analyze import load,sha,write,seal

HERE=Path(__file__).resolve().parent


def main(a):
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    old=load(a.payload/'plan.json')
    if sha(a.payload/'matched')!=old['binary_sha256']:raise ValueError('配对二进制身份不同。')
    for name in ('matched','conv-matched.cpp','conv-kernel.cpp','common.h','matched-common.h'):
        shutil.copy2(a.payload/name,out/name)
    shutil.copytree(a.payload/'inventory',out/'inventory')
    # Exclude the four shapes that already have native samples.
    pool=[(c,t) for c in (256,512,768,1024,1536,2048,3072,4096,5120,7168,10240)
          for t in (1,2,3,4,6,12,16,24,48,64)]
    random.Random(20261012).shuffle(pool)
    cases=[]
    for j,(c,t) in enumerate(pool[:44]):
        split='training' if j<16 else 'calibration' if j<35 else 'test'
        cases.append(dict(id=f'conv-C{c}-T{t}',channels=c,tokens=t,split=split))
    write(out/'plan.json',dict(schema=3,binary_sha256=old['binary_sha256'],symbol=old['symbol'],
        cases=cases,repeats=7,threads=[0,1,2,3],seed=20261012,
        domain='fixed-conv-binary-seed42-four-K1-cores-shape-interpolation-v3',
        split_counts=dict(training=16,calibration=19,test=9),
        features=['constant','max thread ROI instructions','max thread strided vector load bytes',
                  'sum thread ROI memory bytes','barriers per call'],
        protocol=['Freeze coefficients with training groups only.',
                  'Freeze the model identity before the calibration and test stages.',
                  'Use one paired log ratio per shape group.',
                  'Do not use test results to change this model.',
                  'Retain all candidates and all valid samples.'],
        limits=['one compiler binary, one algorithm pair, one seed and four pinned cores',
                'a shape interpolation interval does not establish new-algorithm coverage',
                'ROI census excludes callees; the fitted wall target includes calls and waits',
                'fitted coefficients are not causal hardware instruction costs']))
    (out/'workloads.tsv').write_text(''.join(f'{x["channels"]}\t{x["tokens"]}\t{x["split"]}\n' for x in cases))
    shutil.copy2(HERE/'run-domain-board.sh',out/'run-domain-board.sh')
    seal(out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('payload',type=Path)
    p.add_argument('--output',type=Path,required=True);main(p.parse_args())
