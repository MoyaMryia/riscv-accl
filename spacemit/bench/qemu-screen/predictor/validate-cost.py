#!/usr/bin/env python3
"""用旧标定函数的实际轨迹检查新模型，保留全部误差。"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import statistics
import subprocess
import time
from analyze import load,write,sha,seal
from k1cost import compile_program,predict


def slope(points):
    x=statistics.mean(a for a,b in points);y=statistics.mean(b for a,b in points)
    return sum((a-x)*(b-y) for a,b in points)/sum((a-x)**2 for a,b in points)


def main(a):
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    plan=load(a.payload/'plan.json');binary=a.payload/'driver'
    if sha(binary)!=plan['binary_sha256'] or sha(a.samples)!=plan['old_samples_sha256']:
        raise ValueError('独立检查的输入身份不同。')
    inventory=load(a.payload/'inventory/inventory.json')
    functions={f['symbol']:f for f in inventory['functions']}
    samples=[json.loads(line) for line in a.samples.read_text().splitlines()]
    if any(not s['valid'] or s['enabled']!=s['running'] for s in samples):raise ValueError('旧标定样本无效。')
    records=[];model_id=None;start=time.perf_counter()
    for index,row in enumerate(plan['records']):
        f=functions[row['symbol']];folder=out/row['id'];folder.mkdir()
        inv=folder/'inventory.json';write(inv,dict(inventory,functions=[f]))
        values=[];coverage=[]
        for n in plan['lengths']:
            run=folder/str(n);run.mkdir();trace=run/'trace'
            source=a.reuse/row['id']/str(n) if a.reuse else run
            address=f['instructions'][0]['address'];last=f['instructions'][-1]
            end=last['address']+last['bytes']
            argv=[str(a.qemu.resolve()),'-R','4G','-cpu','rv64,v=true,vlen=256,elen=64,zfh=true,zvfh=true',
                  '-plugin',f'{a.plugin.resolve()},start={address},end={end},out={trace.resolve()},max=30000',
                  str(binary.resolve()),str(index),str(n),str((run/'output.bin').resolve())]
            if a.reuse:
                write(run/'reuse.json',dict(source=str(source),output_sha256=sha(source/'output.bin'),
                                          command_sha256=sha(source/'qemu-command.json')))
            else:
                write(run/'qemu-command.json',argv)
                with (run/'qemu.log').open('w') as log:subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=60)
            program=run/'program';program.mkdir();compile_program(source,inv,program)
            target=run/'cost';target.mkdir();cost=predict(program,a.profiles,target)
            if model_id is not None and model_id!=cost['model_sha256']:raise ValueError('模型身份发生变化。')
            model_id=cost['model_sha256'];coverage.append(cost['coverage'])
            values.append((n,cost['scenarios'][1]['serial_cycles']))
        measured=slope([(s['iterations'],s['cycles']) for s in samples if s['id']==row['id']])
        estimated=slope(values)
        if min(measured,estimated)<=0:raise ValueError('周期斜率必须为正数。')
        records.append(dict(id=row['id'],group=row['group'],original_split=row['split'],arm=row['arm'],
            measured_cycles_per_loop=measured,predicted_cycles_per_loop=estimated,
            relative_error=estimated/measured-1,coverage=coverage))
    grouped=defaultdict(dict)
    for row in records:
        if row['original_split']=='test':grouped[row['group']][row['arm']]=row
    pairs=[]
    for group,arms in grouped.items():
        control,candidate=arms['control'],arms['candidate']
        predicted=candidate['predicted_cycles_per_loop']/control['predicted_cycles_per_loop']
        measured=candidate['measured_cycles_per_loop']/control['measured_cycles_per_loop']
        pairs.append(dict(group=group,predicted_ratio=predicted,measured_ratio=measured,
            gain_error_percentage_points=100*(measured-predicted),direction_mismatch=(predicted<1)!=(measured<1),
            scope_matched=False,limit='retrospective microkernel residual; no unseen full-operator calibration'))
    errors=[abs(r['relative_error']) for r in records if r['original_split']=='test']
    result=dict(schema=2,model_sha256=model_id,records=records,pairs=pairs,
        test_cycle_median_absolute_error=statistics.median(errors),test_cycle_maximum_absolute_error=max(errors),
        maximum_gain_error_percentage_points=max(abs(p['gain_error_percentage_points']) for p in pairs),
        direction_mismatches=sum(p['direction_mismatch'] for p in pairs),elapsed_seconds=time.perf_counter()-start,
        input_sha256=dict(plan=sha(a.payload/'plan.json'),samples=sha(a.samples),qemu=sha(a.qemu),plugin=sha(a.plugin)),
        prediction_interval_status='unavailable; five retrospective microkernel groups do not establish full-operator confidence',
        automatic_action='none')
    write(out/'validation.json',result);seal(out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('payload',type=Path)
    p.add_argument('--samples',type=Path,required=True);p.add_argument('--qemu',type=Path,required=True)
    p.add_argument('--plugin',type=Path,required=True);p.add_argument('--profiles',type=Path,nargs='+',required=True)
    p.add_argument('--reuse',type=Path)
    p.add_argument('--output',type=Path,required=True);main(p.parse_args())
