#!/usr/bin/env python3
"""固定新机制组合的校准与后测，并生成实际二进制。"""
import argparse
import copy
import importlib.util
from pathlib import Path
import random
import shutil
import subprocess
from common import digest,read,seal,write
from prepare import HERE
from reorder import by_kind,dependencies
import state3
import state6

spec=importlib.util.spec_from_file_location('probes4',HERE/'prepare-probes-r4.py')
r4=importlib.util.module_from_spec(spec);spec.loader.exec_module(r4)
scalar=r4.scalar


def pool():
    result=[]
    for family in ('RAW','WAR','WAW'):
        producers=('add','mul') if family=='WAR' else ('add','mul','load')
        consumers=('add','mul') if family=='RAW' else ('add','mul','load')
        for producer in producers:
            for consumer in consumers:
                for chains in ((2,4) if family=='WAW' else (2,3)):
                    for gap in (1,3,5):result.append(dict(family=family,type_order=[producer,consumer],chains=chains,gap=gap))
    return result


def body(config,packets):
    ops=[];producer,consumer=config['type_order']
    for packet in range(packets):
        lane=packet%config['chains'];source=2*lane;destination=source+1
        if config['family']=='RAW':first=scalar(producer,source);second=scalar(consumer,destination,destination,source)
        elif config['family']=='WAR':first=scalar(producer,destination,destination,source);second=scalar(consumer,source)
        else:first=scalar(producer,lane,6);second=scalar(consumer,lane,6)
        ops += [first]+[scalar('add',7) for _ in range(config['gap'])]+[second]
    return ops


def definitions():
    candidates=pool();random.Random(2026101261).shuffle(candidates);rows=[]
    for index,config in enumerate(candidates):
        config.update(group=f'r6-group-{index:03d}',split='calibration' if index<19 else 'test' if index<28 else 'unmeasured')
        if index>=28:continue
        for packets in (8,16):
            original=body(config,packets);priority=list(dict.fromkeys(config['type_order'][::-1]+['add']))
            reordered,order=by_kind(original,priority)
            for arm,ops in enumerate((original,reordered)):
                rows.append(dict(**config,packets=packets,unroll=packets,arm=arm,mode='queue-holdout',role='frozen-holdout',
                    kinds=list(dict.fromkeys(config['type_order']+['add'])),instructions=ops,
                    original_order=list(range(len(original))) if arm==0 else order,original_dependencies=[sorted(e) for e in dependencies(original)]))
    for index,config in enumerate(candidates[:6]):
        config=copy.deepcopy(config);config.update(group=f'r6-control-{index}',split='training',gap=0)
        rows.append(dict(**config,packets=6,unroll=6,arm=0,mode='control',role='frozen-control',
            kinds=list(dict.fromkeys(config['type_order']+['add'])),instructions=body(config,6)))
    for i,row in enumerate(rows):row['id']=f'cpu_{i:03d}'
    return candidates,rows


def main(a):
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);new=read(a.model);old=read(a.prior)
    if digest(HERE/'state6.py')!=new['engine_files']['state6.py']:raise ValueError('新引擎身份不同。')
    candidates,rows=definitions();blocks=[];refs=[]
    for row in rows:
        row['predicted_cycles']=state6.steady(state6.compiled(row),state6.prepare_parameters(new['parameters']))
        row['old_predicted_cycles']=state3.steady(state3.compiled(row),state3.prepare_parameters(old['parameters']))
        asm,ref=r4.render4(row);blocks.append(asm);refs+=ref
    random.Random(2026101262).shuffle(blocks)
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
    for source,name in ((HERE/'run-board.sh','run-board.sh'),(a.protocol,'protocol.md'),(a.model,'frozen-model.json'),(a.prior,'prior-model.json')):shutil.copy2(source,out/name)
    write(out/'candidate-groups.json',dict(groups=candidates,unmeasured=98,retained=True))
    write(out/'plan.json',dict(schema=6,batch='k1-cpu-queue-model-20261012-r6',records=rows,lengths=[65536,262144,1048576],repetitions=5,dump_lengths=[3,17],cpu=0,
        compiler_sha256=digest(compiler),binary_sha256=digest(out/'measure'),model_sha256=digest(a.model),prior_model_sha256=digest(a.prior),protocol_sha256=digest(a.protocol),
        scope='CPU 0; fixed scalar mechanisms; hot read-only input; fixed code family',limits=['本轮新数据不参与拟合。','名义覆盖依赖固定范围内组可交换性。','不是独立真实算法族。']))
    seal(out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('output','compiler','model','prior','protocol'):p.add_argument('--'+name,type=Path,required=True)
    main(p.parse_args())
