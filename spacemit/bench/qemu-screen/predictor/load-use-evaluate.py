#!/usr/bin/env python3
"""校准固定加载消费调度范围，并保留后测组。"""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import statistics
from analyze import load, write, sha, seal


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def linear(points):
    x=statistics.mean(a for a,b in points);y=statistics.mean(b for a,b in points)
    denominator=sum((a-x)**2 for a,b in points)
    if denominator<=0:raise ValueError('斜率需要不同自变量。')
    slope=sum((a-x)*(b-y) for a,b in points)/denominator
    if not math.isfinite(slope) or slope<=0:raise ValueError('斜率必须为有限正数。')
    return dict(slope=slope,intercept=y-slope*x,residuals=[b-y-slope*(a-x) for a,b in points])


def native(plan,path,split):
    definitions=[r for r in plan['records'] if r['split']==split]
    expected={(r['id'],rep,n) for r in definitions for rep in range(plan['repetitions']) for n in plan['lengths']}
    rows=[json.loads(x) for x in path.read_text().splitlines()]
    keys=[(r['id'],r['repeat'],r['iterations']) for r in rows]
    if len(keys)!=len(expected) or set(keys)!=expected:raise ValueError('原生样本矩阵不同。')
    for r in rows:
        if not r['valid'] or r['cpu']!=0 or min(r['cycles'],r['enabled'])<=0 or r['enabled']!=r['running'] or r['output']!=r['expected']:
            raise ValueError('原生样本无效或计数器复用。')
        if r['frequency_before_khz']!=1600000 or r['frequency_after_khz']!=1600000:
            raise ValueError('频率快照超出范围。')
    indexed={(r['id'],r['repeat'],r['iterations']):r for r in rows}
    points=defaultdict(list);loop_fits=[]
    for definition in definitions:
        for rep in range(plan['repetitions']):
            values=[]
            for n in plan['lengths']:
                r=indexed[definition['id'],rep,n]
                if (r['group'],r['arm'],r['unroll'])!=(definition['group'],definition['arm'],definition['operations']):
                    raise ValueError('原生样本配置身份不同。')
                values.append((n,r['cycles']))
            fitted=linear(values)
            points[definition['group'],definition['arm'],rep].append((definition['operations'],fitted['slope']))
            loop_fits.append(dict(id=definition['id'],repeat=rep,**fitted))
    result={}
    for group in (g for g in plan['groups'] if g['split']==split):
        costs=[];fits=[]
        for arm in (0,1):
            values=[linear(points[group['id'],arm,rep]) for rep in range(plan['repetitions'])]
            costs.append([v['slope'] for v in values]);fits.append(values)
        logs=[math.log(b/a) for a,b in zip(*costs)]
        result[group['id']]=dict(measured_ratio=math.exp(statistics.mean(logs)),repeat_log_ratios=logs,
            control_cycles_per_pair=statistics.geometric_mean(costs[0]),
            candidate_cycles_per_pair=statistics.geometric_mean(costs[1]),native_count_fits=fits)
    return result,dict(samples=len(rows),samples_sha256=sha(path),loop_fits=loop_fits,
        involuntary_switches=sum(r['involuntary_switches'] for r in rows))


def predictions(plan,source,plan_sha):
    if source['status']!='complete' or source['plan_sha256']!=plan_sha or source['binary_sha256']!=plan['binary_sha256']:
        raise ValueError('预测批次未完成或身份不同。')
    expected={(r['id'],n) for r in plan['records'] for n in plan['trace_lengths']}
    rows=source['records'];keys=[(r['id'],r['loops']) for r in rows]
    if len(keys)!=len(expected) or set(keys)!=expected:raise ValueError('预测矩阵不同。')
    indexed={(r['id'],r['loops']):r for r in rows};points=defaultdict(list)
    for definition in plan['records']:
        values=[]
        for n in plan['trace_lengths']:
            row=indexed[definition['id'],n];cost=row['cost']
            if cost['model_sha256']!=plan['frozen_component_model_sha256'] or not cost['coverage']['trace_complete']:
                raise ValueError('预测模型不同或轨迹不完整。')
            if (row['group'],row['arm'],row['unroll'])!=(definition['group'],definition['arm'],definition['operations']):
                raise ValueError('预测配置身份不同。')
            center=next(r for r in cost['scenarios'] if r['name']=='central-warm')
            values.append((n,center['cohort_cycles']))
        fit=linear(values)
        points[definition['group'],definition['arm']].append((definition['operations'],fit['slope']))
    result={}
    for group in plan['groups']:
        fits=[linear(points[group['id'],arm]) for arm in (0,1)]
        result[group['id']]=dict(predicted_ratio=fits[1]['slope']/fits[0]['slope'],
            predicted_control_cycles_per_pair=fits[0]['slope'],predicted_candidate_cycles_per_pair=fits[1]['slope'],predicted_count_fits=fits)
    return result


def verify_calibration(value,plan,plan_sha):
    definition={k:v for k,v in value.items() if k!='calibration_sha256'}
    if digest(definition)!=value['calibration_sha256'] or value['implementation_sha256']!=sha(Path(__file__)):
        raise ValueError('冻结误差界限或实现身份不同。')
    if value['plan_sha256']!=plan_sha or value['binary_sha256']!=plan['binary_sha256'] or value['model_sha256']!=plan['frozen_component_model_sha256']:
        raise ValueError('冻结误差界限的适用范围不同。')
    groups={g['id'] for g in plan['groups'] if g['split']=='calibration'}
    if set(value['calibration_groups'])!=groups or len(value['calibration_groups'])!=19:
        raise ValueError('误差校准组不同。')


def main(a):
    plan=load(a.payload/'plan.json');plan_sha=sha(a.payload/'plan.json')
    if sha(a.payload/'measure')!=plan['binary_sha256']:raise ValueError('夹具二进制身份不同。')
    predicted=predictions(plan,load(a.predictions),plan_sha)
    measured,diagnostic=native(plan,a.samples,'calibration' if a.mode=='calibrate' else 'test')
    rows=[]
    for name,m in measured.items():
        prediction=predicted[name]
        rows.append(dict(group=name,**prediction,**m,
            absolute_log_ratio_error=abs(math.log(prediction['predicted_ratio']/m['measured_ratio']))))
    common=dict(schema=4,model_sha256=plan['frozen_component_model_sha256'],plan_sha256=plan_sha,
        binary_sha256=plan['binary_sha256'],predictions_sha256=sha(a.predictions),
        implementation_sha256=sha(Path(__file__)),records=rows,native=diagnostic,
        scope='fixed CPU 0 hot e32 load-use schedule pair; loop and count slopes; selected group plan only',
        limits=plan['limits']+['nominal coverage requires exchangeable groups within this fixed schedule domain',
            'target is a future paired fixture measurement, not a noiseless hardware mean',
            'this domain does not establish new complete-operator or cross-algorithm confidence'],automatic_action='none')
    if a.mode=='calibrate':
        if len(rows)!=19:raise ValueError('95% 有限界限需要 19 个校准组。')
        common.update(kind='fixed-schedule-calibrated-error-bound',nominal_coverage=.95,order_statistic=19,
            calibration_groups=[r['group'] for r in rows],
            maximum_absolute_log_ratio_error=max(r['absolute_log_ratio_error'] for r in rows))
        common['calibration_sha256']=digest(common)
        write(a.output/'calibration.json',common)
    else:
        if not a.calibration:raise ValueError('必须提供先于保留组测量冻结的误差界限。')
        calibration=load(a.calibration);verify_calibration(calibration,plan,plan_sha)
        if calibration['predictions_sha256']!=sha(a.predictions):raise ValueError('预测批次身份不同。')
        factor=math.exp(calibration['maximum_absolute_log_ratio_error'])
        for row in rows:
            ratio=row['predicted_ratio'];lo,hi=ratio/factor,ratio*factor
            row.update(gain_interval=[1-hi,1-lo],covered=lo<=row['measured_ratio']<=hi,
                predicted_gain=1-ratio,measured_gain=1-row['measured_ratio'])
        common.update(kind='reserved-schedule-test',calibration_sha256=calibration['calibration_sha256'],
            observed_covered=sum(r['covered'] for r in rows),observed_total=len(rows),nominal_coverage=.95)
        write(a.output/'evaluation.json',common)
    seal(a.output)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['calibrate','test'])
    p.add_argument('--payload',type=Path,required=True);p.add_argument('--predictions',type=Path,required=True)
    p.add_argument('--samples',type=Path,required=True);p.add_argument('--calibration',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False);main(a)
