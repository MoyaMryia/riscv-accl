#!/usr/bin/env python3
"""按冻结假设分歧安排机制探针，并固定重排检查。"""
import argparse
import copy
import importlib.util
import math
from pathlib import Path
import random
import shutil
import subprocess
from common import digest,read,seal,write
from prepare import HERE,REGS,instruction,render
from reorder import by_kind,dependencies
import state3


def scalar(kind,destination,left=None,right='a4'):
    r=REGS[destination]
    if kind=='load':return dict(kind=kind,asm=f'ld {r},0(a1)',reads=['a1'],writes=[r])
    l=REGS[destination if left is None else left]
    right=REGS[right] if isinstance(right,int) else right
    return dict(kind=kind,asm=f'{kind} {r},{l},{right}',reads=[l,right],writes=[r])


def candidates():
    rows=[]
    def add(family,producer,consumer,chains,gap,ops):
        rows.append(dict(candidate_id=f'probe-{len(rows):03d}',family=family,type_order=[producer,consumer],
            chains=chains,gap=gap,unroll=1,arm=0,mode=family,role='mechanism-probe',kinds=list(dict.fromkeys([producer,consumer,'add'])),instructions=ops))
    for family in ('WAW','WAR','RAW'):
        producers=('add','mul','load') if family!='WAR' else ('add','mul')
        consumers=('add','mul','load') if family!='RAW' else ('add','mul')
        for producer in producers:
            for consumer in consumers:
                for chains in ((1,4) if family=='WAW' else (1,3)):
                    for gap in (0,1,2,4,8):
                        ops=[]
                        for packet in range(12):
                            lane=packet%chains
                            if family=='WAW':
                                first=scalar(producer,lane,6);second=scalar(consumer,lane,6)
                                holes=[scalar('add',(4,5,7)[i%3]) for i in range(gap)]
                            elif family=='WAR':
                                source=2*lane;destination=source+1
                                first=scalar(producer,destination,destination,source);second=scalar(consumer,source)
                                holes=[scalar('add',7) for _ in range(gap)]
                            else:
                                source=2*lane;destination=source+1
                                first=scalar(producer,source);second=scalar(consumer,destination,destination,source)
                                holes=[scalar('add',7) for _ in range(gap)]
                            ops += [first]+holes+[second]
                        add(family,producer,consumer,chains,gap,ops)
    for producer,consumer in (('vadd','vload'),('vload','vadd')):
        for chains in (1,4):
            for gap in (0,1,2,4,8):
                ops=[]
                for packet in range(12):
                    ops += [instruction(producer,packet%chains)]+[scalar('add',i%8) for i in range(gap)]+[instruction(consumer,packet%chains)]
                add('vector-gap',producer,consumer,chains,gap,ops)
    return rows


def select(rows,models):
    compiled=[state3.compiled(row) for row in rows]
    all_predictions=[[state3.steady(program,state3.prepare_parameters(p)) for program in compiled] for p in models]
    for index,row in enumerate(rows):
        values=[p[index] for p in all_predictions]
        row.update(prior_cycles=values[0],hypothesis_cycles=values,hypothesis_range=[min(values),max(values)],
            disagreement_factor=max(values)/min(values),selected=False)
    selected=[]
    for family in ('WAW','WAR','RAW','vector-gap'):
        records=sorted([r for r in rows if r['family']==family],key=lambda r:(-r['disagreement_factor'],r['gap'],r['candidate_id']))
        chosen=[];orders=set()
        for row in records:
            order=tuple(row['type_order'])
            if order not in orders:orders.add(order);chosen.append(row)
        for row in records:
            if len(chosen)>=12:break
            if row not in chosen:chosen.append(row)
        for row in chosen:row['selected']=True
        selected+=chosen
    return selected


def validation():
    rows=[]
    for kinds in (('add','mul'),('add','load'),('mul','load')):
        for chains in (1,2,4):
            for packets in (12,20):
                ops=[scalar(kind,4*j+i%chains) for i in range(packets) for j,kind in enumerate(kinds)]
                grouped,order=by_kind(ops,list(kinds))
                for arm,body in enumerate((grouped,ops)):
                    rows.append(dict(group='r4-reorder-'+'-'.join(kinds)+f'-c{chains}-p{packets}',family='reorder',kinds=list(kinds),
                        chains=chains,packets=packets,unroll=1,arm=arm,role='frozen-validation',mode='reorder',instructions=body,
                        original_order=order if arm==0 else list(range(len(ops))),original_dependencies=[sorted(e) for e in dependencies(ops)]))
    return rows


def render4(row):
    lines,reference=render(row)
    start=reference.index('for(uint64_t k=0;k<n;++k){')+1;end=reference.index('}',start);body=[]
    for op in row['instructions']:
        kind=op['kind']
        if kind not in ('add','mul','load'):continue
        destination=REGS.index(op['writes'][0])
        if kind=='load':body.append(f'r[{destination}] = UINT64_C(0x0101010101010101);')
        else:
            terms=['3' if name=='a4' else f'r[{REGS.index(name)}]' for name in op['reads']]
            body.append(f'r[{destination}] = {terms[0]} {"+" if kind=="add" else "*"} {terms[1]};')
    reference[start:end]=body
    return lines,reference


def main(a):
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    prior=read(a.model)
    if digest(HERE/'state3.py')!=prior['engine_files']['state3.py']:raise ValueError('冻结状态引擎不同。')
    pool=candidates();models=[prior['parameters']]+[r['parameters'] for r in prior['training_equivalent_single_parameter_variants']]
    selected=select(pool,models);rows=[copy.deepcopy(row) for row in selected]+validation()
    for index,row in enumerate(rows):
        row.update(id=f'cpu_{index:03d}',split='training')
        row.setdefault('group',row.get('candidate_id'))
        row.setdefault('prior_cycles',state3.steady(state3.compiled(row),state3.prepare_parameters(prior['parameters'])))
    blocks=[];refs=[]
    for row in rows:
        asm,ref=render4(row);blocks.append(asm);refs+=ref
    random.Random(2026101224).shuffle(blocks)
    (out/'kernels.s').write_text('\n'.join(['.text','.option norvc']+[line for block in blocks for line in block])+'\n')
    declarations='\n'.join(f'extern uint64_t {r["id"]}(uint64_t,void *,void *);' for r in rows)
    table=',\n'.join('{"%s","%s","%s",%s,ref_%s}' % (r['id'],r['group'],r['split'],r['id'],r['id']) for r in rows)
    driver=(HERE/'measure.c').read_text().replace('/* DECLARATIONS */',declarations).replace('/* REFERENCES */','\n'.join(refs)).replace('/* TABLE */',table)
    driver=driver.replace('8192,32768,131072','65536,262144,1048576').replace('rep<9','rep<5');(out/'measure.c').write_text(driver)
    compiler=a.compiler.resolve();argv=[str(compiler),'-O2','-g','-static','-fno-pie','-no-pie','-march=rv64gcv','-Wall','-Wextra','-Werror',str(out/'measure.c'),str(out/'kernels.s'),'-o',str(out/'measure')]
    write(out/'build-command.json',argv)
    with (out/'build.log').open('w') as stream:subprocess.run(argv,stdout=stream,stderr=subprocess.STDOUT,check=True)
    with (out/'disassembly.txt').open('w') as stream:subprocess.run([str(compiler).removesuffix('gcc')+'objdump','-d',str(out/'measure')],stdout=stream,check=True)
    audit=HERE.parent/'qemu-screen/predictor/counter-audit.c';shutil.copy2(audit,out/'counter-audit.c')
    subprocess.run([str(compiler),'-O2','-static','-march=rv64gcv',str(audit),'-o',str(out/'counter-audit')],check=True)
    shutil.copy2(HERE/'run-board.sh',out/'run-board.sh');shutil.copy2(a.protocol,out/'protocol.md');shutil.copy2(a.model,out/'prior-model.json')
    write(out/'probe-candidates.json',dict(candidates=pool,model_count=len(models),limits=['假设分歧不是预测置信区间。','未测候选继续保留。']))
    write(out/'plan.json',dict(schema=4,batch='k1-cpu-mechanism-probes-20261012-r4',records=rows,lengths=[65536,262144,1048576],
        repetitions=5,dump_lengths=[3,17],cpu=0,compiler_sha256=digest(compiler),binary_sha256=digest(out/'measure'),
        prior_model_sha256=digest(a.model),protocol_sha256=digest(a.protocol),candidate_count=len(pool),selected_probe_count=len(selected),
        scope='CPU 0; fixed scalar dependencies and e8 m1 VL32 vector probes; declared hot read-only input',
        limits=['all data use collection stage training; role separates diagnostics and frozen-model validation','no new confidence interval; old calibration is not transferred','not real-algorithm validation']))
    seal(out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--compiler',type=Path,required=True)
    p.add_argument('--model',type=Path,required=True);p.add_argument('--protocol',type=Path,required=True)
    main(p.parse_args())
