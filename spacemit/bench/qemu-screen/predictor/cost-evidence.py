#!/usr/bin/env python3
"""复用已核验的完整轨迹，测量宿主分析时间并生成优先级输入。"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import sys
import time
from analyze import load,write,seal,sha

HERE=Path(__file__).resolve().parent


def pair_record(control,candidate,identity,workload,baseline):
    if control['model_sha256']!=candidate['model_sha256']:raise ValueError('对照与候选使用了不同模型。')
    a={s['name']:s for s in control['scenarios']};b={s['name']:s for s in candidate['scenarios']}
    if set(a)!=set(b):raise ValueError('声明场景不同。')
    scenarios=[dict(name=name+'/'+aggregate,control_cycles=a[name][aggregate],candidate_cycles=b[name][aggregate])
               for name in a for aggregate in ('cohort_cycles','serial_cycles')]
    ca,cb=control['coverage'],candidate['coverage']
    coverage=dict(trace_complete=ca['trace_complete'] and cb['trace_complete'],scope_matched=False,
                  calibrated_instruction_fraction=min(ca['calibrated_instruction_fraction'],cb['calibrated_instruction_fraction']),
                  gaps=sorted(set(ca['gaps']+cb['gaps'])))
    return dict(id=identity,workload=workload,baseline_id=baseline,kind='predicted',
                group=workload,domain='K1-CPU0-component-model-ROI',model_sha256=control['model_sha256'],
                coverage=coverage,scenarios=scenarios)


def main(args):
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    cases=[]
    for shape in ('C6144-T8','C8192-T8','C6144-T32','C8192-T32'):
        for arm in ('control','candidate'):
            source=args.frozen/'conv'/('conv-'+shape+'-'+arm)
            cases.append(('conv-'+shape+'-'+arm,source,source/'inventory/inventory.json'))
    for arm in ('control','candidate'):
        source=args.frozen/'ime-r2'/('ime-load-isolated-'+arm)
        cases.append(('ime-'+arm,source,source/'supplied-inventory.json'))
    def run(row):
        identity,source,inventory=row;times={}
        for action,inputs in [('compile-cost',[source,inventory]),('cost',[out/(identity+'-program'),'--profiles',*args.profiles])]:
            if args.program_root:
                if action=='compile-cost':
                    times['compile-cost_seconds']=0.0
                    times['reused_program_sha256']=sha(args.program_root/(identity+'-program/program.json'))
                    continue
                inputs=[args.program_root/(identity+'-program'),'--profiles',*args.profiles]
            target=out/(identity+('-program' if action=='compile-cost' else '-cost'))
            start=time.perf_counter()
            with (out/(identity+'-'+action+'.log')).open('w') as log:
                subprocess.run([sys.executable,HERE/'analyze.py',action,*map(str,inputs),'--output',target],
                               stdout=log,stderr=subprocess.STDOUT,check=True)
            times[action+'_seconds']=time.perf_counter()-start
        return dict(id=identity,source=str(source),inventory_sha256=sha(inventory),**times,
                    cost=load(out/(identity+'-cost/cost.json')))
    start=time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:results=list(pool.map(run,cases))
    write(out/'host-results.json',dict(records=results,elapsed_seconds=time.perf_counter()-start,jobs=args.jobs))
    costs={r['id']:r['cost'] for r in results};records=[]
    for shape in ('C6144-T8','C8192-T8','C6144-T32','C8192-T32'):
        prefix='conv-'+shape
        records.append(pair_record(costs[prefix+'-control'],costs[prefix+'-candidate'],prefix+'-predicted',
                                   prefix,'frozen-conv-original-ROI'))
    records.append(pair_record(costs['ime-control'],costs['ime-candidate'],'ime-load-predicted',
                               'ime-load-64-case-ROI','frozen-ime-load-control'))
    write(out/'priority-plan.json',dict(schema=2,interval_coverage=.9,records=records))
    subprocess.run([sys.executable,HERE/'analyze.py','rank',out/'priority-plan.json','--output',out/'priority'],check=True)
    seal(out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--frozen',type=Path,required=True)
    p.add_argument('--profiles',type=Path,nargs='+',required=True);p.add_argument('--jobs',type=int,default=4)
    p.add_argument('--program-root',type=Path)
    p.add_argument('--output',type=Path,required=True);main(p.parse_args())
