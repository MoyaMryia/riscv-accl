#!/usr/bin/env python3
"""冻结 K1 分项标定矩阵、实际汇编与板端载荷。"""
import argparse
import json
from pathlib import Path
import subprocess
from analyze import sha, seal, write

HERE = Path(__file__).resolve().parent


def prepare(out, compiler, operations=None):
    out.mkdir(parents=True, exist_ok=False)
    rows, assembly = [], ['.text', '.option norvc']
    counts = [8, 32, 128]
    keys = []
    for op in ('vfmacc.vv', 'vfadd.vv', 'vfmul.vv', 'vfredosum.vs', 'vfredusum.vs'):
        for m in (1, 2, 4, 8):
            full = 8*m
            for vl in sorted({1, full//2, full}):
                keys.append(dict(op=op, sew=32, lmul=m, vl=vl, stride=0, footprint=0))
    for op in ('vadd.vi', 'vand.vi', 'vsrl.vi'):
        for sew in (8, 16, 32):
            for m in (1, 2, 4, 8):
                full = 256*m//sew
                for vl in sorted({1, full//2, full}):
                    keys.append(dict(op=op, sew=sew, lmul=m, vl=vl, stride=0, footprint=0))
    for stride in (0, 12, 16):
        for m in (1, 2, 4, 8):
            for vl in sorted({1, 4*m, 8*m}):
                keys.append(dict(op='vle32.v' if not stride else 'vlse32.v', sew=32,
                                 lmul=m, vl=vl, stride=stride, footprint=4096))
    for op in ('addi', 'xor', 'mul'):
        keys.append(dict(op=op, sew=0, lmul=0, vl=0, stride=0, footprint=0))
    for footprint in (4096, 32768, 131072, 524288, 2097152, 8388608):
        keys.append(dict(op='ld', sew=0, lmul=0, vl=0, stride=64, footprint=footprint))
    if operations: keys=[k for k in keys if k["op"] in operations]
    if not keys: raise ValueError("操作列表没有可标定的指令。")
    for index, key in enumerate(keys):
        vector = key['sew'] != 0
        modes = [('dependent', 1), ('independent', 8 if key['lmul'] <= 2 else 4 if key['lmul'] == 4 else 2)] if vector or key['op'] != 'ld' else [('dependent', 1)]
        if not vector and key['op'] != 'ld': modes = [('dependent', 1), ('independent', 4)]
        for mode, chains in modes:
            for count in counts:
                name = f'k1p_{index:03d}_{mode}_{count}'
                entry = ['mv t5,a0', 'li t0,0', 'mv t4,a1', 'li t1,1', 'li t2,1', 'li t3,1', 'li a3,1', 'li a4,3']
                body = []
                finish = ['mv a0,t0']
                kind = 'counter'
                if vector:
                    m, sew, vl, op = key['lmul'], key['sew'], key['vl'], key['op']
                    registers = [j*m for j in range(chains)]
                    source_a, source_b = (16,24) if m == 8 else (24,28)
                    initial = 1 if op == 'vfmul.vv' else 15 if op == 'vand.vi' else 0
                    entry += [f'vsetvli t6,zero,e{sew},m{m},tu,mu']
                    for v in registers: entry.append(f'vmv.v.i v{v},{initial if op != "vfmul.vv" else 0}')
                    if op.startswith('vf'):
                        entry += ['lui t6,0x3f800', 'fmv.w.x ft0,t6', f'vfmv.v.f v{source_a},ft0', f'vfmv.v.f v{source_b},ft0']
                        if op == 'vfmul.vv':
                            for v in registers: entry.append(f'vfmv.v.f v{v},ft0')
                    entry += [f'li t6,{vl}', f'vsetvli zero,t6,e{sew},m{m},ta,ma', f'li t6,{key["stride"]}']
                    for j in range(count):
                        v = registers[j % chains]
                        if op == 'vfmacc.vv': body.append(f'{op} v{v},v{source_a},v{source_b}')
                        elif op in ('vfadd.vv', 'vfmul.vv'): body.append(f'{op} v{v},v{v},v{source_a}')
                        elif op.startswith('vfred'): body.append(f'{op} v{v},v{source_a},v{v}')
                        elif op.endswith('.vi'): body.append(f'{op} v{v},v{v},{15 if op == "vand.vi" else 1}')
                        elif op == 'vle32.v': body.append(f'{op} v{v},(a1)')
                        else: body.append(f'{op} v{v},(a1),t6')
                    for v in registers:
                        finish += [f'vs{m}r.v v{v},(a2)', f'addi a2,a2,{32*m}']
                    kind = op
                elif key['op'] == 'ld':
                    body = ['ld t4,0(t4)']*count
                    finish = ['mv a0,t4']
                    kind = 'pointer'
                else:
                    registers = ['t1', 't2', 't3', 'a3'][:chains]
                    for j in range(count):
                        r = registers[j % chains]
                        body.append(f'addi {r},{r},1' if key['op']=='addi' else f'{key["op"]} {r},{r},a4')
                    finish += [f'sd {r},{i*8}(a2)' for i,r in enumerate(registers)]
                    kind = key['op']
                body += ['addi t0,t0,1', 'addi t5,t5,-1', f'bnez t5,.L{name}']
                assembly += [f'.global {name}', f'.type {name},@function', name+':', *entry,
                             '.L'+name+':', *body, *finish, 'fence rw,rw', 'ret', f'.size {name},.-{name}']
                rows.append(dict(id=name, key=key, mode=mode, chains=chains, operations=count,
                                 kind=kind, body=body, output_bytes=chains*32*key['lmul'] if vector else chains*8))
    (out/'kernels.s').write_text('\n'.join(assembly)+'\n')
    declarations = '\n'.join(f'extern uint64_t {r["id"]}(uint64_t,void *,void *);' for r in rows)
    kinds = {op:i for i,op in enumerate(('counter','vfmacc.vv','vfadd.vv','vfmul.vv','vadd.vi','vand.vi','vsrl.vi','vle32.v','vlse32.v','pointer','addi','xor','mul','vmadot.s8','vfredosum.vs','vfredusum.vs'))}
    table = ',\n'.join('{"%s",%s,%d,%d,%d,%d,%d,%d,%d,%d}' % (r['id'],r['id'],kinds[r['kind']],r['chains'],r['operations'],r['key']['sew'],r['key']['lmul'],r['key']['vl'],r['key']['footprint'],r['output_bytes']) for r in rows)
    template = (HERE/'profile-measure.c').read_text()
    lengths = [128,512,2048] if any(k['op'].startswith('vfred') for k in keys) else [512,2048,8192]
    template = template.replace('const uint64_t lengths[]={512,2048,8192};',
                                'const uint64_t lengths[]={'+','.join(map(str,lengths))+'};')
    (out/'measure.c').write_text(template.replace('/* DECLARATIONS */',declarations).replace('/* TABLE */',table))
    plan = dict(schema=3, records=rows, lengths=lengths, repetitions=7, cpu=0,
                counter=dict(type='PERF_TYPE_RAW',config='0x22',scope='K1 U-mode cycle event; run counter-audit first'),
                instruction_counts=counts, key_count=len(keys), protocol=dict(
                purpose='portable K1 cost model and investment priority; no elimination rule',
                output_checks='active vector lanes, scalar state, pointer endpoint and guards',
                tail_limit='inactive agnostic vector lanes are not numerical outputs',
                memory='random pointer cycle at 64-byte spacing; no inferred physical cache level',
                profile_scope='CPU 0; warm steady state; vector dependency and independent streams',
                intervals='replicate variability; not unseen-algorithm prediction confidence'))
    write(out/'plan.json',plan)
    argv = [str(compiler.resolve()),'-O2','-static','-march=rv64gcv','-Wall','-Wextra','-Werror',
            str((out/'measure.c').resolve()),str((out/'kernels.s').resolve()),'-o',str((out/'measure').resolve())]
    write(out/'build-command.json',argv)
    (out/'compiler-version.log').write_text(subprocess.check_output([compiler,'--version'],text=True))
    with (out/'build.log').open('w') as stream: subprocess.run(argv,stdout=stream,stderr=subprocess.STDOUT,check=True)
    plan.update(binary_sha256=sha(out/'measure'),compiler_sha256=sha(compiler))
    write(out/'plan.json',plan)
    (out/'BINARY-SHA256SUMS').write_text(sha(out/'measure')+'  measure\n')
    (out/'run-board-calibration.sh').write_text((HERE/'run-board-calibration.sh').read_text().replace('timeout 60 ./measure', 'timeout 300 ./measure'))
    seal(out)
    print(json.dumps(dict(keys=len(keys),kernels=len(rows),samples=len(rows)*21)))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('output',type=Path)
    p.add_argument('--compiler',type=Path,required=True)
    p.add_argument('--operations',nargs='+')
    a=p.parse_args();prepare(a.output,a.compiler,a.operations)
