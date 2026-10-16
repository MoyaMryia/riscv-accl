#!/usr/bin/env python3
"""核验片段原生配对数据，并报告限定配置下的实测收益。"""
import argparse
from collections import defaultdict
import importlib.util
import json
import math
from pathlib import Path
import statistics
from common import digest,read,write

spec=importlib.util.spec_from_file_location('source_fragment_check',Path(__file__).with_name('fragment-check.py'))
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)


def fit(rows,field):
    rows=sorted(rows,key=lambda row:row['calls'])
    if len(rows)!=3 or len({row['calls'] for row in rows})!=3:
        raise ValueError('斜率必须包含三个不同调用次数。')
    x=[row['calls'] for row in rows];y=[row[field] for row in rows]
    if x!=[x[0],2*x[0],4*x[0]]:raise ValueError('调用次数比例不同。')
    if any(type(value) is not int for value in x+y):raise ValueError('斜率输入必须为整数观测。')
    denominator=3*sum(value*value for value in x)-sum(x)**2
    numerator=3*sum(a*b for a,b in zip(x,y))-sum(x)*sum(y)
    slope=numerator/denominator
    intercept=(sum(y)*denominator-numerator*sum(x))/(3*denominator)
    return dict(slope=slope,intercept=intercept,
                residuals=[value-(slope*count+intercept) for count,value in zip(x,y)])


def summarize(plan,sessions):
    case_by_id={row['id']:row for row in plan['cases']}
    kernels={row['id'] for row in plan['kernels']}
    groups=defaultdict(list);all_rows=[]
    expected=len(case_by_id)*len(kernels)*5*3
    if len(sessions)!=2:raise ValueError('必须提供两个独立进程。')
    for session,rows in enumerate(sessions):
        if len(rows)!=expected:raise ValueError('正式观测数量不同。')
        for row in rows:
            if row['case'] not in case_by_id or row['kernel'] not in kernels or row['repeat'] not in range(5):
                raise ValueError('未知配置、实现或重复身份。')
            if row['work_units']!=case_by_id[row['case']]['work_units'] or row['cpu']!=0:
                raise ValueError('工作量或核编号不同。')
            if not 0<row['calls']<=4*1048576 or row['enabled']<=0 or row['enabled']!=row['running']:
                raise ValueError('调用次数或计数器覆盖无效。')
            for field in ('cycles','wall_ns','thread_cpu_ns'):
                if type(row[field]) is not int or row[field]<=0:raise ValueError('性能观测必须为正整数。')
            groups[(row['case'],session,row['repeat'],row['kernel'])].append(row)
            all_rows.append(row)
    slopes={key:{field:fit(rows,field) for field in ('cycles','wall_ns','thread_cpu_ns')} for key,rows in groups.items()}
    if len(slopes)!=len(case_by_id)*len(kernels)*10:raise ValueError('配置重复或缺失。')
    for case in case_by_id:
        for session in (0,1):
            for repeat in range(5):
                counts={tuple(sorted(row['calls'] for row in groups[(case,session,repeat,kernel)])) for kernel in kernels}
                if len(counts)!=1:raise ValueError('两臂调用次数不配对。')
    failures=[dict(case=key[0],session=key[1],repeat=key[2],kernel=key[3],field=field)
              for key,fields in slopes.items() for field,value in fields.items() if value['slope']<=0]
    cases=[]
    for case,configuration in case_by_id.items():
        costs={kernel:{field:statistics.median(slopes[(case,s,r,kernel)][field]['slope'] for s in (0,1) for r in range(5))
                       for field in ('cycles','wall_ns','thread_cpu_ns')} for kernel in kernels}
        comparisons=[]
        for kernel in sorted(kernels-{plan['baseline']}):
            ratios={}
            if not failures:
                for field in ('cycles','wall_ns','thread_cpu_ns'):
                    paired=[slopes[(case,s,r,kernel)][field]['slope']/slopes[(case,s,r,plan['baseline'])][field]['slope']
                            for s in (0,1) for r in range(5)]
                    central=costs[kernel][field]/costs[plan['baseline']][field]
                    ratios[field]=dict(candidate_over_baseline=central,gain_percent=100*(1-central),
                        observed_paired_ratio_range=[min(paired),max(paired)],
                        process_median_ratios=[statistics.median(paired[:5]),statistics.median(paired[5:])])
            comparisons.append(dict(candidate=kernel,metrics=ratios,retained=True,prediction_confidence=None))
        cases.append(dict(configuration=configuration,median_cost_per_call=costs,comparisons=comparisons))
    return dict(status='paired-observations-verified' if not failures else 'nonpositive-slopes',
                observations=len(all_rows),cases=cases,nonpositive_slopes=failures,
                slopes=[dict(case=k[0],session=k[1],repeat=k[2],kernel=k[3],fields=v) for k,v in sorted(slopes.items())],
                shortest_wall_ns=min(row['wall_ns'] for row in all_rows),
                frequency_snapshots_khz=sorted({row[key] for row in all_rows for key in ('frequency_before_khz','frequency_after_khz')}),
                context_switches=sum(row['voluntary_switches']+row['involuntary_switches'] for row in all_rows),
                prediction_confidence=None,automatic_full_test=False,automatic_performance_rejection=False,
                limits=['本轮是所选夹具与运行条件下的配对实测，不是新算法预测精度。',
                        '重复观测范围不是预测置信区间。','热输入重复调用包含真实调用与调用循环开销。',
                        '频率快照不能证明测量期间频率固定。','片段收益不能直接转换为完整模型收益。'])


def assess(payload,qemu,native):
    payload,qemu,native=map(Path,(payload,qemu,native))
    checker.receipts(payload);checker.receipts(qemu);checker.receipts(native)
    if (native/'exit-status').read_text().strip()!='0':raise ValueError('原生批次没有成功结束。')
    plan=read(payload/'input-plan.json');q=read(qemu/'result.json')
    if digest(payload/'fragment')!=q['binary_sha256']:raise ValueError('同一 ELF 身份不同。')
    expected={p.name for p in (qemu/'dumps').iterdir()}
    if {p.name for p in (native/'dumps').iterdir()}!=expected:raise ValueError('原生完整转储缺失。')
    for name in expected:
        if (native/'dumps'/name).read_bytes()!=(qemu/'dumps'/name).read_bytes():
            raise ValueError('原生与 QEMU 完整数值转储不同。')
    sessions=[[json.loads(line) for line in (native/f'samples-{i}.jsonl').read_text().splitlines()] for i in (0,1)]
    result=summarize(plan,sessions)
    result.update(binary_sha256=q['binary_sha256'],numerical_dumps=len(expected),
                  plan_sha256=digest(payload/'input-plan.json'),native_receipt_sha256=digest(native/'SHA256SUMS'),
                  qemu_receipt_sha256=digest(qemu/'SHA256SUMS'))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('payload','qemu','native','output'):parser.add_argument('--'+key,type=Path,required=True)
    a=parser.parse_args();result=assess(a.payload,a.qemu,a.native);write(a.output,result)
    print(json.dumps(dict(status=result['status'],observations=result['observations'],numerical_dumps=result['numerical_dumps'])))
