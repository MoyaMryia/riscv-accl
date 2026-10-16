#!/usr/bin/env python3
"""生成标量传递、独立发射与新组合检查。"""
import argparse
from itertools import combinations
from pathlib import Path
import random
import shutil
import subprocess
from common import digest,seal,write
from prepare import HERE,TYPES,REGS,instruction,render
from reorder import by_kind,dependencies


def scalar(kind,destination,source=None):
    r=REGS[destination]
    if kind=='load':
        return dict(kind=kind,asm=f'ld {r},0(a1)',reads=['a1'],writes=[r])
    source=destination if source is None else source
    s=REGS[source]
    return dict(kind=kind,asm=f'{kind} {r},{s},a4',reads=[s,'a4'],writes=[r])


def definitions():
    rows=[]
    def add(group,split,kinds,chains,ops,unroll=1,arm=0,mode='fixture'):
        original=ops
        priority=list(kinds)+(['add'] if 'add' not in kinds else [])
        if arm:
            ops,order=by_kind(ops,priority if arm==1 else priority[::-1])
        else:order=list(range(len(ops)))
        rows.append(dict(id=f'cpu_{len(rows):03d}',group=group,split=split,kinds=list(kinds),chains=chains,
            unroll=unroll,arm=arm,mode=mode,instructions=ops,original_order=order,
            original_dependencies=[sorted(e) for e in dependencies(original)]))
    for kind in TYPES[:3]:
        for chains in (1,2,4,8):
            for unroll in (1,4):
                add(f'r3-isolated-{kind}-c{chains}','training',[kind],chains,
                    [scalar(kind,i%chains) for i in range(16*unroll)],unroll)
    for producer in TYPES[:3]:
        for consumer in TYPES[:2]:
            for gap in (0,1,2,3,4,6,8):
                ops=[]
                for packet in range(8):
                    # 生产者与消费者形成实际循环相关链。
                    ops.append(scalar(producer,0,1))
                    ops.extend(scalar('add',2+i%6) for i in range(gap))
                    ops.append(scalar(consumer,1,0))
                add(f'r3-transfer-{producer}-{consumer}-g{gap}','training',
                    list(dict.fromkeys([producer,consumer,'add'])),1,ops,mode='transfer')
    for kinds in combinations(TYPES[:3],2):
        for chains in (1,2,4):
            for unroll in (1,4):
                ops=[scalar(kind,4*j+i%chains) for i in range(8*unroll) for j,kind in enumerate(kinds)]
                for arm in (0,1,2):
                    add('r3-independent-'+'-'.join(kinds)+f'-c{chains}','training',kinds,chains,ops,unroll,arm,'independent')
    for kind in TYPES[3:]:
        for chains in (1,2,4):
            for unroll in (1,4):
                add(f'r3-isolated-{kind}-c{chains}','training',[kind],chains,
                    [instruction(kind,i%chains) for i in range(16*unroll)],unroll)
    for kinds in (('ime','vadd'),('vadd','ime'),('ime','vload'),('vload','ime')):
        for chains in (1,4):
            for gap in (0,1,4,12,24):
                ops=[]
                for packet in range(8):
                    ops.append(instruction(kinds[0],packet%chains))
                    ops.extend(scalar('add',i%8) for i in range(gap))
                    ops.append(instruction(kinds[1],packet%chains))
                add('r3-vector-'+'-'.join(kinds)+f'-c{chains}-g{gap}','training',list(kinds)+['add'],chains,ops,mode='vector-gap')
    groups=[(kinds,chains) for kinds in combinations(TYPES,3) for chains in (1,3)]
    random.Random(2026101221).shuffle(groups)
    for index,(kinds,chains) in enumerate(groups[:32]):
        for unroll in (2,3):
            ops=[instruction(kind,i%chains) for i in range(8*unroll) for kind in kinds]
            for arm in (0,1):
                add(f'r3-hold-{index:02d}','calibration' if index<19 else 'test',kinds,chains,ops,unroll,arm,'holdout')
    return rows


def render3(row):
    lines,reference=render(row)
    start=reference.index('for(uint64_t k=0;k<n;++k){')+1
    end=reference.index('}',start)
    body=[]
    for op in row['instructions']:
        kind=op['kind']
        if kind not in TYPES[:3]:continue
        destination=REGS.index(op['writes'][0])
        if kind=='load':body.append(f'r[{destination}] = UINT64_C(0x0101010101010101);')
        else:
            source=REGS.index(op['reads'][0])
            symbol='+' if kind=='add' else '*'
            body.append(f'r[{destination}] = r[{source}] {symbol} 3;')
    reference[start:end]=body
    return lines,reference


def main(a):
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    rows=definitions();blocks=[];refs=[]
    for row in rows:
        asm,ref=render3(row);blocks.append(asm);refs+=ref
    random.Random(2026101222).shuffle(blocks)
    (out/'kernels.s').write_text('\n'.join(['.text','.option norvc']+[line for block in blocks for line in block])+'\n')
    declarations='\n'.join(f'extern uint64_t {r["id"]}(uint64_t,void *,void *);' for r in rows)
    table=',\n'.join('{"%s","%s","%s",%s,ref_%s}' % (r['id'],r['group'],r['split'],r['id'],r['id']) for r in rows)
    driver=(HERE/'measure.c').read_text().replace('/* DECLARATIONS */',declarations).replace('/* REFERENCES */','\n'.join(refs)).replace('/* TABLE */',table)
    driver=driver.replace('8192,32768,131072','65536,262144,1048576').replace('rep<9','rep<5')
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
    shutil.copy2(HERE/'run-board.sh',out/'run-board.sh');shutil.copy2(a.protocol,out/'protocol.md')
    write(out/'plan.json',dict(schema=3,batch='k1-cpu-model-20261012-r3',records=rows,lengths=[65536,262144,1048576],
        repetitions=5,dump_lengths=[3,17],cpu=0,compiler_sha256=digest(compiler),binary_sha256=digest(out/'measure'),
        group_seed=2026101221,layout_seed=2026101222,protocol_sha256=digest(a.protocol),
        scope='CPU 0; hot fixed input; e8 m1 VL32; signed 4x4x8 IME; register-dependency reorder; holdout unroll 2 and 3',
        limits=['fixed three-class groups are not arbitrary-algorithm validation','no cache miss, branch recovery, TLB, synchronization or wall-time calibration']))
    seal(out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--compiler',type=Path,required=True)
    p.add_argument('--protocol',type=Path,required=True)
    main(p.parse_args())
