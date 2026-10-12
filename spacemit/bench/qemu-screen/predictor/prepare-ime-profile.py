#!/usr/bin/env python3
"""冻结已验证有符号 IME 4×4×8 点积的成本标定。"""
import argparse
from pathlib import Path
import subprocess
from analyze import write,sha,seal
HERE=Path(__file__).resolve().parent


def prepare(out,compiler):
    out.mkdir(parents=True,exist_ok=False);rows=[];assembly=['.text','.option norvc']
    for mode,chains in [('dependent',1),('independent',4)]:
        for count in (8,32,128):
            name=f'k1p_ime_{mode}_{count}'
            entry=['mv t5,a0','li t0,0','vsetvli t6,zero,e32,m2,ta,ma']
            for j in range(chains):entry.append(f'vmv.v.i v{16+2*j},0')
            entry+=['vsetvli t6,zero,e8,m1,ta,ma','vle8.v v14,(a1)','vle8.v v0,(a1)']
            body=[f'.word {((0xe207382b & ~(31<<7)) | ((16+2*(j%chains))<<7)):#x}' for j in range(count)]
            body+=['addi t0,t0,1','addi t5,t5,-1',f'bnez t5,.L{name}']
            finish=['mv a0,t0','vsetvli t6,zero,e32,m2,ta,ma']
            for j in range(chains):finish+=[f'vs2r.v v{16+2*j},(a2)','addi a2,a2,64']
            assembly += [f'.global {name}',f'.type {name},@function',name+':',*entry,'.L'+name+':',*body,*finish,'fence rw,rw','ret',f'.size {name},.-{name}']
            rows.append(dict(id=name,key=dict(op='vmadot.s8',sew=8,lmul=1,vl=32,stride=0,footprint=0),
                             mode=mode,chains=chains,operations=count,body=body,kind='ime',output_bytes=chains*64))
    (out/'kernels.s').write_text('\n'.join(assembly)+'\n')
    decl='\n'.join(f'extern uint64_t {r["id"]}(uint64_t,void *,void *);' for r in rows)
    table=',\n'.join('{"%s",%s,13,%d,%d,32,2,16,0,%d}'%(r['id'],r['id'],r['chains'],r['operations'],r['output_bytes']) for r in rows)
    (out/'measure.c').write_text((HERE/'profile-measure.c').read_text().replace('/* DECLARATIONS */',decl).replace('/* TABLE */',table))
    plan=dict(schema=3,records=rows,lengths=[512,2048,8192],repetitions=7,cpu=0,instruction_counts=[8,32,128],key_count=1,
        counter=dict(type='PERF_TYPE_RAW',config='0x22',scope='K1 U-mode cycle event; run counter-audit first'),
        protocol=dict(purpose='K1 signed IME component model; no elimination rule',
            output_checks='all sixteen int32 outputs per accumulator and guards',
            profile_scope='CPU 0; fixed signed 4x4x8 tile; e8/m1 VL=32; input bytes equal one',
            intervals='replicate variability; not unseen-algorithm prediction confidence'))
    argv=[str(compiler.resolve()),'-O2','-static','-march=rv64gcv','-Wall','-Wextra','-Werror',str((out/'measure.c').resolve()),str((out/'kernels.s').resolve()),'-o',str((out/'measure').resolve())]
    write(out/'build-command.json',argv)
    with (out/'build.log').open('w') as f:subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,check=True)
    (out/'compiler-version.log').write_text(subprocess.check_output([compiler,'--version'],text=True))
    plan.update(binary_sha256=sha(out/'measure'),compiler_sha256=sha(compiler));write(out/'plan.json',plan)
    (out/'BINARY-SHA256SUMS').write_text(sha(out/'measure')+'  measure\n')
    (out/'run-board-calibration.sh').write_bytes((HERE/'run-board-calibration.sh').read_bytes());seal(out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);p.add_argument('--compiler',type=Path,required=True)
    a=p.parse_args();prepare(a.output,a.compiler)
