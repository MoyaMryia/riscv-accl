#!/usr/bin/env python3
"""生成第一轮单核状态模型实验，并预先固定数据划分。"""
import argparse
from collections import Counter
from itertools import combinations
from pathlib import Path
import random
import shutil
import subprocess
from common import digest, seal, write

HERE = Path(__file__).resolve().parent
REGS = ['t0', 't1', 't2', 't3', 't4', 't5', 't6', 'a3']
TYPES = ['add', 'mul', 'load', 'vadd', 'ime', 'vload']


def instruction(kind, lane):
    r = REGS[lane]
    if kind == 'add':
        return dict(kind=kind, asm=f'add {r},{r},a4', reads=[r, 'a4'], writes=[r])
    if kind == 'mul':
        return dict(kind=kind, asm=f'mul {r},{r},a4', reads=[r, 'a4'], writes=[r])
    if kind == 'load':
        return dict(kind=kind, asm=f'ld {r},0(a1)', reads=['a1'], writes=[r])
    if kind == 'vadd':
        v = f'v{8+lane%4}'
        return dict(kind=kind, asm=f'vadd.vv {v},{v},v0', reads=[v, 'v0'], writes=[v])
    if kind == 'vload':
        return dict(kind=kind, asm='vle8.v v0,(a1)', reads=['a1'], writes=['v0'])
    if kind == 'ime':
        v = 16+2*(lane%4)
        word = 0xe200302b | (v << 7) | (1 << 20)
        return dict(kind=kind, asm=f'.word {word:#x}', reads=[f'v{v}', f'v{v+1}', 'v0', 'v1'], writes=[f'v{v}', f'v{v+1}'])
    raise ValueError(kind)


def definitions():
    rows = []
    def add(group, split, kinds, chains, arm):
        # 两臂使用相同操作集合，但改变操作顺序。
        ops = [instruction(k, i % chains) for i in range(16) for k in kinds]
        if arm:
            ops.sort(key=lambda op: kinds.index(op['kind']))
        rows.append(dict(id=f'cpu_{len(rows):03d}', group=group, split=split,
                         kinds=list(kinds), chains=chains, arm=arm, instructions=ops))
    for kind in TYPES:
        for chains in (1, 2, 4):
            add(f'isolated-{kind}-{chains}', 'training', [kind], chains, 0)
    for left, right in combinations(TYPES, 2):
        for arm in (0, 1):
            add(f'pair-{left}-{right}', 'training', [left, right], 2, arm)
    groups = [(kinds, chains) for kinds in combinations(TYPES, 3) for chains in (1, 4)]
    random.Random(2026101215).shuffle(groups)
    for index, (kinds, chains) in enumerate(groups[:28]):
        split = 'calibration' if index < 19 else 'test'
        for arm in (0, 1):
            add(f'triple-{index:02d}', split, kinds, chains, arm)
    return rows


def render(row):
    name = row['id']
    ops = row['instructions']
    start = ['mv a6,a0', 'li a4,3'] + [f'li {r},{i+1}' for i,r in enumerate(REGS)]
    start += ['vsetvli a5,zero,e32,m2,ta,ma'] + [f'vmv.v.i v{v},0' for v in (16,18,20,22)]
    start += ['vsetvli a5,zero,e8,m1,ta,ma'] + [f'vmv.v.i v{v},0' for v in (8,9,10,11)]
    start += ['vle8.v v0,(a1)', 'addi a5,a1,32', 'vle8.v v1,(a5)']
    finish = [f'sd {r},{i*8}(a2)' for i,r in enumerate(REGS)] + ['addi a7,a2,64']
    for v in (8,9,10,11):
        finish += [f'vs1r.v v{v},(a7)', 'addi a7,a7,32']
    finish += ['vsetvli a5,zero,e32,m2,ta,ma']
    for v in (16,18,20,22):
        finish += [f'vs2r.v v{v},(a7)', 'addi a7,a7,64']
    lines = ['.balign 64',f'.global {name}',f'.type {name},@function',name+':',*start,
             '.balign 64', '.L'+name+':',*[op['asm'] for op in ops],
             'addi a0,a0,-1',f'bnez a0,.L{name}',*finish,'mv a0,a6','ret',f'.size {name},.-{name}']
    c = [f'static void ref_{name}(uint64_t n,unsigned char *out) {{',
         'uint64_t r[8]={1,2,3,4,5,6,7,8};', 'for(uint64_t k=0;k<n;++k){']
    for op in ops:
        kind = op['kind']
        if kind not in ('add','mul','load'):
            continue
        lane = REGS.index(op['writes'][0])
        c.append(f'r[{lane}] += 3;' if kind=='add' else f'r[{lane}] *= 3;' if kind=='mul' else f'r[{lane}] = UINT64_C(0x0101010101010101);')
    c += ['}', 'memcpy(out,r,64);']
    counts = Counter((op['kind'],op['writes'][0]) for op in ops)
    for j in range(4):
        c.append(f'memset(out+64+{32*j},(unsigned char)(n*{counts["vadd",f"v{8+j}"]}),32);')
        c.append(f'for(int i=0;i<16;++i){{uint32_t x=(uint32_t)(8*n*{counts["ime",f"v{16+2*j}"]}); memcpy(out+192+{64*j}+4*i,&x,4);}}')
    c += ['}']
    return lines, c


def main(a):
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    rows = definitions()
    blocks, refs = [], []
    for row in rows:
        asm, ref = render(row)
        blocks.append(asm)
        refs += ref
    random.Random(2026101216).shuffle(blocks)
    (out/'kernels.s').write_text('\n'.join(['.text','.option norvc']+[line for block in blocks for line in block])+'\n')
    declarations = '\n'.join(f'extern uint64_t {r["id"]}(uint64_t,void *,void *);' for r in rows)
    table = ',\n'.join('{"%s","%s","%s",%s,ref_%s}' % (r['id'],r['group'],r['split'],r['id'],r['id']) for r in rows)
    driver = (HERE/'measure.c').read_text().replace('/* DECLARATIONS */',declarations).replace('/* REFERENCES */','\n'.join(refs)).replace('/* TABLE */',table)
    (out/'measure.c').write_text(driver)
    compiler = a.compiler.resolve()
    argv = [str(compiler),'-O2','-g','-static','-fno-pie','-no-pie','-march=rv64gcv','-Wall','-Wextra','-Werror',str(out/'measure.c'),str(out/'kernels.s'),'-o',str(out/'measure')]
    write(out/'build-command.json', argv)
    with (out/'build.log').open('w') as stream:
        subprocess.run(argv,stdout=stream,stderr=subprocess.STDOUT,check=True)
    subprocess.run([str(compiler).removesuffix('gcc')+'objdump','-d',str(out/'measure')],stdout=(out/'disassembly.txt').open('w'),check=True)
    shutil.copy2(HERE/'run-board.sh',out/'run-board.sh')
    audit = HERE.parent/'qemu-screen/predictor/counter-audit.c'
    shutil.copy2(audit,out/'counter-audit.c')
    subprocess.run([str(compiler),'-O2','-static','-march=rv64gcv',str(audit),'-o',str(out/'counter-audit')],check=True)
    write(out/'plan.json', dict(schema=1, batch='k1-cpu-model-20261012-r1', records=rows,
        lengths=[8192,32768,131072],repetitions=9,dump_lengths=[3,17],cpu=0,
        compiler_sha256=digest(compiler),binary_sha256=digest(out/'measure'),
        group_seed=2026101215,layout_seed=2026101216,
        counter=dict(type='raw',config='0x22',scope='U-mode; re-audit this batch'),
        scope='CPU 0; e8 m1 VL=32; signed 4x4x8 IME; hot fixed input; 64-byte loop alignment',
        limits=['no cache capacity, branch prediction, shared-memory or wall-time model',
                'triple-operation groups are reserved; this is not arbitrary-algorithm validation',
                'register chains and instruction order vary; isolated instruction counts do not define cost',
                'repeated measurement variation is not a prediction interval']))
    seal(out)


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--compiler',type=Path,required=True)
    main(p.parse_args())
