#!/usr/bin/env python3
"""标定轨迹中常见的标量地址操作和压缩指令。"""
import argparse
from pathlib import Path
import subprocess
from analyze import write,sha,seal

HERE=Path(__file__).resolve().parent


def prepare(out,compiler):
    out=out.resolve();out.mkdir(parents=True,exist_ok=False)
    definitions={
        'add':('add {r},{r},a4','1+3*steps'),
        'addw':('addw {r},{r},a4','(uint64_t)(int64_t)(int32_t)(1+3*steps)'),
        'addiw':('addiw {r},{r},1','(uint64_t)(int64_t)(int32_t)(1+steps)'),
        'sub':('sub {r},{r},a4','1-3*steps'),
        'subw':('subw {r},{r},a4','(uint64_t)(int64_t)(int32_t)(1-3*steps)'),
        'mulw':('mulw {r},{r},a4','(uint64_t)(int64_t)(int32_t)power(3,steps)'),
        'slli':('slli {r},{r},1','steps>=64?0:UINT64_C(1)<<steps'),
        'slliw':('slliw {r},{r},1','steps>=32?0:(uint64_t)(int64_t)(int32_t)(UINT32_C(1)<<steps)'),
        'srli':('srli {r},{r},1','0'),
        'srliw':('srliw {r},{r},1','0'),
        'sraiw':('sraiw {r},{r},1','0'),
        'or':('or {r},{r},a4','3'),
        'and':('and {r},{r},a4','1'),
        'sltu':('sltu {r},{r},a4','1'),
        'sltiu':('sltiu {r},{r},3','1'),
        'c.add':('c.add {r},a4','1+3*steps'),
        'c.addw':('c.addw {r},a4','(uint64_t)(int64_t)(int32_t)(1+3*steps)'),
        'c.addi':('c.addi {r},1','1+steps'),
        'c.addiw':('c.addiw {r},1','(uint64_t)(int64_t)(int32_t)(1+steps)'),
        'c.slli':('c.slli {r},1','steps>=64?0:UINT64_C(1)<<steps'),
        'c.srli':('c.srli {r},1','0'),
        'c.sub':('c.sub {r},a4','1-3*steps'),
        'c.subw':('c.subw {r},a4','(uint64_t)(int64_t)(int32_t)(1-3*steps)'),
        'c.or':('c.or {r},a4','3'),
        'c.and':('c.and {r},a4','1')}
    rows=[];assembly=['.text','.option norvc'];checks=[]
    for index,(op,(template,expected)) in enumerate(definitions.items()):
        checks.append(f'case {16+index}:want=({expected});break;')
        for mode,chains in [('dependent',1),('independent',4)]:
            for count in (8,32,128):
                name=f'k1s_{index:03d}_{mode}_{count}';registers=['a0','a1','a2','a3'][:chains]
                entry=['mv t5,a0','mv t4,a2','li t0,0','li a4,3']+[f'li {r},1' for r in registers]
                body=[template.format(r=registers[j%chains]) for j in range(count)]
                control=['addi t0,t0,1','addi t5,t5,-1',f'bnez t5,.L{name}']
                finish=[f'sd {r},{i*8}(t4)' for i,r in enumerate(registers)]+['mv a0,t0','fence rw,rw','ret']
                assembly += [f'.global {name}',f'.type {name},@function',name+':',*entry,'.L'+name+':',
                             '.option rvc' if op.startswith('c.') else '.option norvc',*body,'.option norvc',
                             *control,*finish,f'.size {name},.-{name}']
                rows.append(dict(id=name,key=dict(op=op,sew=0,lmul=0,vl=0,stride=0,footprint=0),
                    mode=mode,chains=chains,operations=count,body=body+control,kind_code=16+index,output_bytes=8*chains))
    (out/'kernels.s').write_text('\n'.join(assembly)+'\n')
    declarations='\n'.join(f'extern uint64_t {r["id"]}(uint64_t,void *,void *);' for r in rows)
    table=',\n'.join('{"%s",%s,%d,%d,%d,0,0,0,0,%d}'%(r['id'],r['id'],r['kind_code'],r['chains'],r['operations'],r['output_bytes']) for r in rows)
    template=(HERE/'profile-measure.c').read_text()
    checker='''}else if(kind>=16){
                for(int c=0;c<chains;++c){uint64_t actual;memcpy(&actual,output+64+c*8,8);
                    uint64_t steps=n*ops/chains,want=0;
                    switch(kind){ CHECKS default:valid=0; }
                    valid&=actual==want;
                }
            }else if(kind>=10){'''.replace('CHECKS',' '.join(checks))
    template=template.replace('}else if(kind>=10){',checker)
    (out/'measure.c').write_text(template.replace('/* DECLARATIONS */',declarations).replace('/* TABLE */',table))
    argv=[str(compiler.resolve()),'-O2','-static','-march=rv64gcv','-Wall','-Wextra','-Werror',str(out/'measure.c'),str(out/'kernels.s'),'-o',str(out/'measure')]
    write(out/'build-command.json',argv)
    with (out/'build.log').open('w') as log:subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,check=True)
    (out/'compiler-version.log').write_text(subprocess.check_output([compiler,'--version'],text=True))
    write(out/'plan.json',dict(schema=3,records=rows,lengths=[512,2048,8192],repetitions=7,cpu=0,
        counter=dict(type='PERF_TYPE_RAW',config='0x22',scope='K1 U-mode cycle event; run counter-audit first'),
        binary_sha256=sha(out/'measure'),compiler_sha256=sha(compiler),key_count=len(definitions),
        protocol=dict(purpose='measure frequent scalar and compressed instruction costs',
                      selection='dynamic gap frequency; no candidate outcome threshold',
                      scope='CPU 0; fixed operands; dependent chain and four independent streams',
                      output_checks='every scalar accumulator, counter and guards; all samples retained',
                      intervals='measurement ranges; not algorithm prediction confidence')))
    (out/'BINARY-SHA256SUMS').write_text(sha(out/'measure')+'  measure\n')
    (out/'run-board-calibration.sh').write_text((HERE/'run-board-calibration.sh').read_text().replace('timeout 60 ./measure','timeout 300 ./measure'))
    seal(out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path)
    p.add_argument('--compiler',type=Path,required=True);a=p.parse_args();prepare(a.output,a.compiler)
