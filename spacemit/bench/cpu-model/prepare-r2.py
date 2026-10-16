#!/usr/bin/env python3
"""生成保留语义的 CPU 重排对照与类型传递实验。"""
import argparse
from itertools import combinations
from pathlib import Path
import random
import shutil
import subprocess
from common import digest,seal,write
from prepare import HERE,TYPES,instruction,render
from reorder import by_kind,dependencies


def definitions():
    rows=[]
    def add(group,split,kinds,chains,unroll=1,arm=0,gap=0):
        ops=[]
        for _ in range(unroll):
            for packet in range(16):
                for index,kind in enumerate(kinds):
                    ops.append(instruction(kind,packet%chains))
                    if index==0:
                        ops.extend(instruction('add',7) for _ in range(gap))
        original=ops
        priority=list(kinds)+(['add'] if 'add' not in kinds else [])
        if arm:
            ops,order=by_kind(ops,priority)
        else:
            order=list(range(len(ops)))
        rows.append(dict(id=f'cpu_{len(rows):03d}',group=group,split=split,kinds=list(kinds),chains=chains,
            unroll=unroll,arm=arm,gap=gap,instructions=ops,original_order=order,
            original_dependencies=[sorted(e) for e in dependencies(original)]))
    for kind in TYPES:
        for chains in (1,2,4):
            for unroll in (1,4):
                add(f'r2-isolated-{kind}-{chains}','training',[kind],chains,unroll)
    for kinds in combinations(TYPES,2):
        for unroll in (1,4):
            for arm in (0,1):
                add('r2-pair-'+'-'.join(kinds),'training',kinds,2,unroll,arm)
    for kinds in combinations(TYPES[:3],2):
        for order in (kinds,kinds[::-1]):
            for chains in (1,2,4):
                for gap in (0,2,6):
                    add('r2-typed-'+'-'.join(order)+f'-c{chains}-g{gap}','training',order,chains,gap=gap)
    for kinds in (('ime','vload'),('ime','vadd')):
        for order in (kinds,kinds[::-1]):
            for chains in (1,4):
                for gap in (0,2,6):
                    add('r2-vector-'+'-'.join(order)+f'-c{chains}-g{gap}','training',order,chains,gap=gap)
    groups=[(kinds,chains) for kinds in combinations(TYPES,4) for chains in (2,4)]
    random.Random(2026101217).shuffle(groups)
    for index,(kinds,chains) in enumerate(groups[:28]):
        split='calibration' if index<19 else 'test'
        for unroll in (1,4):
            for arm in (0,1):
                add(f'r2-hold-{index:02d}',split,kinds,chains,unroll,arm)
    return rows


def main(a):
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    rows=definitions();blocks=[];refs=[]
    for row in rows:
        asm,ref=render(row);blocks.append(asm);refs+=ref
    random.Random(2026101218).shuffle(blocks)
    (out/'kernels.s').write_text('\n'.join(['.text','.option norvc']+[line for block in blocks for line in block])+'\n')
    declarations='\n'.join(f'extern uint64_t {r["id"]}(uint64_t,void *,void *);' for r in rows)
    table=',\n'.join('{"%s","%s","%s",%s,ref_%s}' % (r['id'],r['group'],r['split'],r['id'],r['id']) for r in rows)
    driver=(HERE/'measure.c').read_text().replace('/* DECLARATIONS */',declarations).replace('/* REFERENCES */','\n'.join(refs)).replace('/* TABLE */',table)
    driver=driver.replace('8192,32768,131072','65536,262144,1048576').replace('rep<9','rep<7')
    (out/'measure.c').write_text(driver)
    compiler=a.compiler.resolve()
    argv=[str(compiler),'-O2','-g','-static','-fno-pie','-no-pie','-march=rv64gcv','-Wall','-Wextra','-Werror',str(out/'measure.c'),str(out/'kernels.s'),'-o',str(out/'measure')]
    write(out/'build-command.json',argv)
    with (out/'build.log').open('w') as stream:
        subprocess.run(argv,stdout=stream,stderr=subprocess.STDOUT,check=True)
    with (out/'disassembly.txt').open('w') as stream:
        subprocess.run([str(compiler).removesuffix('gcc')+'objdump','-d',str(out/'measure')],stdout=stream,check=True)
    audit=HERE.parent/'qemu-screen/predictor/counter-audit.c'
    shutil.copy2(audit,out/'counter-audit.c')
    subprocess.run([str(compiler),'-O2','-static','-march=rv64gcv',str(audit),'-o',str(out/'counter-audit')],check=True)
    shutil.copy2(HERE/'run-board.sh',out/'run-board.sh')
    shutil.copy2(a.protocol,out/'protocol.md')
    write(out/'plan.json',dict(schema=2,batch='k1-cpu-model-20261012-r2',records=rows,lengths=[65536,262144,1048576],
        repetitions=7,dump_lengths=[3,17],cpu=0,compiler_sha256=digest(compiler),binary_sha256=digest(out/'measure'),
        group_seed=2026101217,layout_seed=2026101218,protocol_sha256=digest(a.protocol),
        scope='CPU 0; hot fixed input; e8 m1 VL32; signed 4x4x8 IME; valid register-dependency reorder; unroll 1 and 4',
        limits=['four-class combination holdout is not arbitrary-algorithm validation',
                'no cache capacity, branch predictor, TLB, synchronization or wall-time calibration',
                'register dependence order establishes fixture equivalence; arbitrary memory aliasing is not supported']))
    seal(out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--compiler',type=Path,required=True)
    p.add_argument('--protocol',type=Path,required=True)
    main(p.parse_args())
