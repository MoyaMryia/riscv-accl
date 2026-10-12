#!/usr/bin/env python3
"""冻结单核与四核访存模式的板端载荷。"""
import argparse
from pathlib import Path
import shutil
import subprocess
from analyze import sha,write,seal

HERE=Path(__file__).resolve().parent


def main(a):
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    shutil.copy2(HERE/'memory-profile.cpp',out/'measure.cpp')
    shutil.copy2(HERE.parents[1]/'quick-screen/common.h',out/'common.h')
    compiler=a.compiler.resolve();argv=list(map(str,[compiler,'-O3','-g','-static','-march=rv64gcv',
        '-std=c++17','-pthread',out/'measure.cpp','-o',out/'measure']))
    write(out/'build-command.json',argv)
    with (out/'build.log').open('w') as log:subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,check=True)
    write(out/'plan.json',dict(schema=3,binary_sha256=sha(out/'measure'),threads=[1,4],repetitions=7,
        counter=dict(type='PERF_TYPE_RAW',config='0x22',scope='K1 U-mode cycle event; run counter-audit first'),
        instruction_counter_scope='generic instruction event; user-only filtering is not established',
        spans_bytes=[4096,32768,131072,524288,2097152,8388608],
        modes={'0':'unit vector read','1':'unit vector write','2':'unit vector copy',
               '3':'stride-16 vector read','4':'unit input and stride-16 weight multiply to unit output'},
        scope='e32 m1 VL8; CPUs 0 to 3; separate per-worker arrays; warm repeated passes',
        limits=['payload bytes are architectural data bytes, not physical memory traffic',
                'stride-16 arrays span four times the payload size',
                'mixed multiply arrays span six times the base size per worker',
                'patterns include loop and fence costs; no pure memory controller bandwidth claim',
                'frequency snapshots do not prove a constant clock',
                'no unseen-algorithm confidence from these measurements alone']))
    (out/'BINARY-SHA256SUMS').write_text(sha(out/'measure')+'  measure\n')
    runner=(HERE/'run-board-calibration.sh').read_text().replace('timeout 60 ./measure','timeout 180 ./measure')
    (out/'run-board-calibration.sh').write_text(runner);seal(out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path)
    p.add_argument('--compiler',type=Path,required=True);main(p.parse_args())
