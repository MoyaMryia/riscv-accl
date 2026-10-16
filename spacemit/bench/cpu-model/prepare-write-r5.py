#!/usr/bin/env python3
"""生成源操作数交换与重复写入模型的冻结检查。"""
import argparse
import copy
import importlib.util
from pathlib import Path
import random
import shutil
import subprocess
from common import digest,read,seal,write
from prepare import HERE
import state3
import state5

spec=importlib.util.spec_from_file_location('probes4',HERE/'prepare-probes-r4.py')
r4=importlib.util.module_from_spec(spec);spec.loader.exec_module(r4)
scalar=r4.scalar


def definitions():
    rows=[]
    for family in ('RAW','WAR','WAW'):
        producers=('add','mul') if family=='WAR' else ('add','mul','load')
        consumers=('add','mul') if family=='RAW' else ('add','mul','load')
        for producer in producers:
            for consumer in consumers:
                for chains in ((1,2,3) if family=='RAW' else (1,3)):
                    for gap in ((0,) if family=='WAR' else (0,2)):
                        group=f'r5-{family}-{producer}-{consumer}-c{chains}-g{gap}'
                        for position in ((0,1) if family!='WAW' else (0,)):
                            ops=[]
                            for packet in range(12):
                                lane=packet%chains;source=2*lane;destination=source+1
                                if family=='RAW':
                                    first=scalar(producer,source)
                                    second=scalar(consumer,destination,source if position else destination,destination if position else source)
                                elif family=='WAR':
                                    first=scalar(producer,destination,source if position else destination,destination if position else source)
                                    second=scalar(consumer,source)
                                else:first=scalar(producer,lane,6);second=scalar(consumer,lane,6)
                                ops += [first]+[scalar('add',7) for _ in range(gap)]+[second]
                            rows.append(dict(group=group,family=family,type_order=[producer,consumer],chains=chains,gap=gap,
                                operand_position=position,unroll=1,arm=position,mode=family,role='frozen-mechanism-check',
                                kinds=list(dict.fromkeys([producer,consumer,'add'])),instructions=ops))
    for row in r4.validation():
        old=row['packets'];new={12:16,20:28}[old]
        kinds=row['kinds'];chains=row['chains']
        original=[scalar(kind,4*j+i%chains) for i in range(new) for j,kind in enumerate(kinds)]
        grouped,order=r4.by_kind(original,kinds)
        row.update(group=row['group'].replace('r4-','r5-').replace(f'-p{old}',f'-p{new}'),packets=new,
            instructions=grouped if row['arm']==0 else original,original_order=order if row['arm']==0 else list(range(len(original))),
            original_dependencies=[sorted(e) for e in r4.dependencies(original)])
        rows.append(row)
    for i,row in enumerate(rows):row.update(id=f'cpu_{i:03d}',split='training')
    return rows


def main(a):
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    new=read(a.model);old=read(a.prior)
    if digest(HERE/'state5.py')!=new['engine_files']['state5.py']:raise ValueError('新模型引擎身份不同。')
    if digest(HERE/'state3.py')!=old['engine_files']['state3.py']:raise ValueError('第三轮引擎身份不同。')
    rows=definitions();blocks=[];refs=[]
    for row in rows:
        row['predicted_cycles']=state5.steady(state5.compiled(row),state5.prepare_parameters(new['parameters']))
        row['old_predicted_cycles']=state3.steady(state3.compiled(row),state3.prepare_parameters(old['parameters']))
        asm,ref=r4.render4(row);blocks.append(asm);refs+=ref
    random.Random(2026101251).shuffle(blocks)
    (out/'kernels.s').write_text('\n'.join(['.text','.option norvc']+[line for block in blocks for line in block])+'\n')
    declarations='\n'.join(f'extern uint64_t {r["id"]}(uint64_t,void *,void *);' for r in rows)
    table=',\n'.join('{"%s","%s","%s",%s,ref_%s}' % (r['id'],r['group'],r['split'],r['id'],r['id']) for r in rows)
    driver=(HERE/'measure.c').read_text().replace('/* DECLARATIONS */',declarations).replace('/* REFERENCES */','\n'.join(refs)).replace('/* TABLE */',table)
    (out/'measure.c').write_text(driver.replace('8192,32768,131072','65536,262144,1048576').replace('rep<9','rep<5'))
    compiler=a.compiler.resolve();argv=[str(compiler),'-O2','-g','-static','-fno-pie','-no-pie','-march=rv64gcv','-Wall','-Wextra','-Werror',str(out/'measure.c'),str(out/'kernels.s'),'-o',str(out/'measure')]
    write(out/'build-command.json',argv)
    with (out/'build.log').open('w') as log:subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,check=True)
    with (out/'disassembly.txt').open('w') as log:subprocess.run([str(compiler).removesuffix('gcc')+'objdump','-d',str(out/'measure')],stdout=log,check=True)
    audit=HERE.parent/'qemu-screen/predictor/counter-audit.c';shutil.copy2(audit,out/'counter-audit.c')
    subprocess.run([str(compiler),'-O2','-static','-march=rv64gcv',str(audit),'-o',str(out/'counter-audit')],check=True)
    for source,name in ((HERE/'run-board.sh','run-board.sh'),(a.protocol,'protocol.md'),(a.model,'frozen-write-model.json'),(a.prior,'prior-model.json')):shutil.copy2(source,out/name)
    write(out/'plan.json',dict(schema=5,batch='k1-cpu-write-model-20261012-r5',records=rows,lengths=[65536,262144,1048576],repetitions=5,dump_lengths=[3,17],cpu=0,
        compiler_sha256=digest(compiler),binary_sha256=digest(out/'measure'),model_sha256=digest(a.model),prior_model_sha256=digest(a.prior),protocol_sha256=digest(a.protocol),
        scope='CPU 0; fixed scalar loops; hot read-only input; fixed register and operand choices',prediction_confidence=None,
        limits=['本批未参与本轮模型拟合。','不转用旧校准界限。','不是独立真实算法族验证。','全部候选继续保留。']))
    seal(out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('output','compiler','model','prior','protocol'):p.add_argument('--'+name,type=Path,required=True)
    main(p.parse_args())
