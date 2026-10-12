#!/usr/bin/env python3
"""冻结 IME 加载点积混合循环的独立检查计划。"""
import argparse
from pathlib import Path
import random
import shutil
import subprocess
import sys
from analyze import write, sha, seal

HERE = Path(__file__).resolve().parent
MODEL = 'dd267b9c6d897d0aa025d81d940505a7e34709847eac4fe419f84a4a9ab8b148'


def dot(rd, left, right):
    if rd % 2 or not 16 <= rd <= 22 or not 0 <= left < 16 or not 0 <= right < 16:
        raise ValueError('点积寄存器超出固定布局。')
    return 0xe200302b | (rd << 7) | (left << 15) | (right << 20)


def groups():
    rows = [dict(id=f'ime-mix-c{c}-g{gap}', chains=c, gap=gap) for c in (1, 2, 4) for gap in range(10)]
    random.Random(2026101207).shuffle(rows)
    rows = rows[:28]
    for i, row in enumerate(rows):
        row['split'] = 'calibration' if i < 19 else 'test'
    return rows


def main(a):
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    definitions, blocks = [], []
    for i, group in enumerate(groups()):
        chains, gap = group['chains'], group['gap']
        for arm in (0, 1):
            for count in (8, 32, 128):
                name = f'k1lu_{i}_{arm}_{count}'
                entry = ['mv t5,a0', 'mv t4,a2', 'li t0,0', 'li t2,0',
                    'vsetvli t6,zero,e32,m2,ta,ma']
                entry += [f'vmv.v.i v{16+2*j},0' for j in range(chains)]
                entry += ['vsetvli t6,zero,e8,m1,ta,ma']
                body = []
                for _ in range(count // chains):
                    loads, uses = [], []
                    for j in range(chains):
                        left, right = (8+2*j, j) if arm else (14, 0)
                        load = [f'addi t1,a1,{j*128}', f'vle8.v v{left},(t1)',
                                'addi t1,t1,64', f'vle8.v v{right},(t1)']
                        use = [f'.word {dot(16+2*j,left,right):#x}'] + ['addi t2,t2,1']*gap
                        if arm:
                            loads += load
                            uses += use
                        else:
                            body += load + use
                    if arm:
                        body += loads + uses
                body += ['addi t0,t0,1', 'addi t5,t5,-1', f'bnez t5,.L{name}']
                finish = ['vsetvli t6,zero,e32,m2,ta,ma']
                for j in range(chains):
                    finish += [f'vs2r.v v{16+2*j},(t4)', 'addi t4,t4,64']
                blocks.append(['.balign 64', f'.global {name}', f'.type {name},@function',
                    name+':', *entry, '.balign 64', '.L'+name+':', *body, *finish,
                    'mv a0,t0', 'fence rw,rw', 'ret', f'.size {name},.-{name}'])
                definitions.append(dict(id=name, group=group['id'], arm=arm, operations=count,
                    m=2, vl=16, chains=chains, gap=gap, split=group['split'], body=body))
    random.Random(2026101208).shuffle(blocks)
    (out/'kernels.s').write_text('\n'.join(['.text', '.option norvc']+[s for b in blocks for s in b])+'\n')
    declarations = '\n'.join(f'extern uint64_t {r["id"]}(uint64_t,void *,void *);' for r in definitions)
    table = ',\n'.join('{"%s","%s",%s,%d,%d,2,16,%d,%d}' %
        (r['id'], r['group'], r['id'], r['arm'], r['operations'], r['chains'],
         0 if r['split']=='calibration' else 1) for r in definitions)
    driver = (HERE/'load-use-measure.c').read_text()
    driver = driver.replace('float input[1056]', 'int8_t input[1056]').replace('input[i]=1.0f', 'input[i]=1')
    driver = driver.replace('input+16,', 'input+64,').replace('input[i]==1.0f', 'input[i]==1')
    driver = driver.replace('float actual;', 'int32_t actual;')
    driver = driver.replace('(float)(n*kernels[k].ops/kernels[k].chains)',
        '(int32_t)(8*n*kernels[k].ops/kernels[k].chains)')
    (out/'measure.c').write_text(driver.replace('/* DECLARATIONS */', declarations).replace('/* TABLE */', table))
    compiler = a.compiler.resolve()
    command = [str(compiler), '-O2', '-g', '-static', '-fno-pie', '-no-pie', '-march=rv64gcv',
        '-Wall', '-Wextra', '-Werror', str(out/'measure.c'), str(out/'kernels.s'), '-o', str(out/'measure')]
    write(out/'build-command.json', command)
    with (out/'build.log').open('w') as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
    subprocess.run([sys.executable, HERE.parent/'assembly-inventory.py', out/'measure', out/'inventory',
        '--symbol-regex', '^k1lu_', '--tool-prefix', str(compiler).removesuffix('gcc')], check=True)
    write(out/'plan.json', dict(schema=7, groups=groups(), records=definitions, lengths=[512,2048,8192],
        trace_lengths=[2,16], repetitions=7, binary_sha256=sha(out/'measure'), compiler_sha256=sha(compiler),
        frozen_component_model_sha256=MODEL, group_seed=2026101207, layout_seed=2026101208,
        loop_alignment_bytes=64, scope='CPU 0; fixed hot signed 4x4x8 load-dot loop pair; all input bytes equal one',
        limits=['no complete IME operator or model wall-time prediction',
            'pair changes instruction order and input register reuse together',
            'independent scalar gap operations do not establish pure load latency',
            'nineteen calibration groups and nine reserved groups; three unroll versions form one group',
            'constant input validates this fixture only; no arbitrary-data algorithm equivalence claim',
            'native U-mode loop slope includes loop control; no affine unroll-cost assumption']))
    shutil.copy2(HERE/'run-schedule-family-board.sh', out/'run-load-use-board.sh')
    seal(out)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--compiler', type=Path, required=True)
    main(p.parse_args())
