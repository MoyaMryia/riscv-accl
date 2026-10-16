#!/usr/bin/env python3
"""检查冻结点估计与全部观测，保留误差和方向不一致。"""
import argparse
import json
import math
from pathlib import Path
import statistics
from common import digest,read,write


def positive(value):
    if type(value) not in (int,float) or not math.isfinite(value) or value<=0:
        raise ValueError('周期或比值必须为正的有限数。')
    return value


def observed_costs(plan,observations):
    """从全部配对斜率重算周期、比值与重复范围。"""
    cases={row['id']:row for row in plan['cases']}
    kernels={row['id'] for row in plan['kernels']}
    baseline=plan['baseline']
    rows=observations['cases']
    if len(rows)!=len(cases) or {row['configuration']['id'] for row in rows}!=set(cases):
        raise ValueError('观测配置缺失或重复。')
    slopes={}
    for row in observations['slopes']:
        key=(row['case'],row['session'],row['repeat'],row['kernel'])
        if key in slopes:raise ValueError('原生斜率身份重复。')
        slopes[key]=positive(row['fields']['cycles']['slope'])
    expected={(case,session,repeat,kernel) for case in cases for session in (0,1)
              for repeat in range(5) for kernel in kernels}
    if set(slopes)!=expected:raise ValueError('原生配对斜率缺失或未知。')
    costs={};comparisons={}
    for row in rows:
        case=row['configuration']['id']
        if row['configuration']!=cases[case] or set(row['median_cost_per_call'])!=kernels:
            raise ValueError('观测配置或实现身份不同。')
        for kernel in kernels:
            value=statistics.median(slopes[(case,s,r,kernel)] for s in (0,1) for r in range(5))
            if positive(row['median_cost_per_call'][kernel]['cycles'])!=value:
                raise ValueError('观测周期与原生斜率不同。')
            costs[(case,kernel)]=value
        supplied=row['comparisons']
        if len(supplied)!=len(kernels)-1 or {item['candidate'] for item in supplied}!=kernels-{baseline}:
            raise ValueError('观测比较缺失或重复。')
        for item in supplied:
            kernel=item['candidate'];metric=item['metrics']['cycles']
            ratio=costs[(case,kernel)]/costs[(case,baseline)]
            paired=[slopes[(case,s,r,kernel)]/slopes[(case,s,r,baseline)] for s in (0,1) for r in range(5)]
            bounds=[min(paired),max(paired)]
            if positive(metric['candidate_over_baseline'])!=ratio or metric['observed_paired_ratio_range']!=bounds:
                raise ValueError('观测比值或重复范围与原生斜率不同。')
            comparisons[(case,kernel)]=(ratio,bounds)
    return costs,comparisons


def evaluate(plan,prediction,observations):
    configurations={row['id']:row for row in plan['cases']}
    kernels={row['id'] for row in plan['kernels']}
    if len(configurations)!=len(plan['cases']) or len(kernels)!=len(plan['kernels']) or plan['baseline'] not in kernels:
        raise ValueError('计划配置、实现或基线身份无效。')
    expected={(case,k['id']) for case in configurations for k in plan['kernels']}
    predicted={(r['case'],r['kernel']):r['cycles_per_call'] for r in prediction['records']}
    if len(predicted)!=len(prediction['records']) or set(predicted)!=expected:
        raise ValueError('预测单元缺失或重复。')
    if observations['status']!='paired-observations-verified' or observations['nonpositive_slopes']:
        raise ValueError('原生观测未通过完整配对核验。')
    actual,observed=observed_costs(plan,observations)
    records=[];comparisons=[]
    sign=lambda value:1 if value>1 else -1 if value<1 else 0
    for (case,kernel),value in sorted(predicted.items()):
        positive(value)
        measured=actual[(case,kernel)]
        records.append(dict(case=case,kernel=kernel,split=configurations[case].get('split','undeclared'),
            predicted_cycles=value,observed_cycles=measured,predicted_over_observed=value/measured,
            absolute_relative_error=abs(value/measured-1),retained=True))
    for case in observations['cases']:
        identity=case['configuration']['id']
        for row in case['comparisons']:
            candidate=row['candidate'];measured,bounds=observed[(identity,candidate)]
            ratio=predicted[(identity,candidate)]/predicted[(identity,plan['baseline'])]
            low,high=bounds
            comparisons.append(dict(case=identity,candidate=candidate,split=configurations[identity].get('split','undeclared'),
                predicted_ratio=ratio,observed_ratio=measured,
                observed_repeat_range=[low,high],observed_direction_resolved=high<1 or low>1,
                direction_agrees=sign(ratio)==sign(measured),retained=True))
    summaries={}
    for split in sorted({row['split'] for row in records}):
        cells=[row for row in records if row['split']==split]
        pairs=[row for row in comparisons if row['split']==split]
        summaries[split]=dict(cells=len(cells),median_absolute_relative_error=statistics.median(row['absolute_relative_error'] for row in cells),
            maximum_absolute_relative_error=max(row['absolute_relative_error'] for row in cells),
            mean_squared_log_error=math.fsum(math.log(row['predicted_over_observed'])**2 for row in cells)/len(cells),
            comparisons=len(pairs),direction_agreement=sum(row['direction_agrees'] for row in pairs),
            unresolved_observed_directions=sum(not row['observed_direction_resolved'] for row in pairs))
    return dict(status='frozen-estimates-assessed',records=records,comparisons=comparisons,summary=summaries,
        prediction_confidence=None,automatic_performance_rejection=False,
        limits=['重复范围描述本批观测，不是预测置信区间。','同族配置检查不能证明新算法族精度。',
                '所有误差与方向不一致均保留。'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('plan','prediction','observations','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();prediction=read(a.prediction);observations=read(a.observations)
    if prediction['plan_sha256']!=digest(a.plan) or observations['plan_sha256']!=digest(a.plan):
        raise ValueError('预测与观测计划身份不同。')
    if prediction['binary_sha256']!=observations['binary_sha256']:raise ValueError('预测与观测 ELF 不同。')
    result=evaluate(read(a.plan),prediction,observations)
    result.update(prediction_sha256=digest(a.prediction),observations_sha256=digest(a.observations),model_sha256=prediction['model_sha256'])
    write(a.output,result)
    print(json.dumps(result['summary'],ensure_ascii=False))
