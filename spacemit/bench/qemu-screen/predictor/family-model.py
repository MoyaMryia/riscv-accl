#!/usr/bin/env python3
"""建立有范围限制的完整算子模型，并保留独立误差与检查组。"""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import statistics
import time
from analyze import load,write,sha,seal
from priority import conformal


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def positive(x):
    if type(x) not in (int,float) or not math.isfinite(x) or x<=0:raise ValueError('模型输入必须为有限正数。')
    return x


def paired_samples(path,workload,repeats):
    rows=[json.loads(x) for x in path.read_text().splitlines()]
    blocks=defaultdict(dict);times=defaultdict(list);calls_by_length={}
    for row in rows:
        if row['workload']!=workload or row['valid'] is not True:raise ValueError('板端样本范围不同或无效。')
        if row['phases']:continue
        key=(row['repeat'],row['length']);arm=row['arm'];calls=row['calls']
        if arm not in (0,1) or not 0<=row['repeat']<repeats or row['length'] not in (0,1,2):raise ValueError('配对样本标识无效。')
        if arm in blocks[key] or calls<=0:raise ValueError('配对样本重复或调用次数无效。')
        if row['length'] in calls_by_length and calls_by_length[row['length']]!=calls:raise ValueError('同一长度的调用次数不同。')
        calls_by_length[row['length']]=calls
        if len(row['threads'])!=4 or {t['cpu'] for t in row['threads']}!={0,1,2,3}:raise ValueError('线程 CPU 范围不同。')
        for t in row['threads']:
            if t['enabled']!=t['running'] or min(t['cycles'],t['instructions'],t['running'])<=0:
                raise ValueError('板端计数器无效或存在复用。')
            if t['frequency_before_khz']!=1600000 or t['frequency_after_khz']!=1600000:
                raise ValueError('频率快照超出模型范围。')
        value=positive(row['wall_ms'])/calls;blocks[key][arm]=value;times[arm].append(value)
    expected={(r,l) for r in range(repeats) for l in range(3)}
    if set(blocks)!=expected or any(set(b)!={0,1} for b in blocks.values()):raise ValueError('完整配对区块缺失。')
    logs=[math.log(blocks[k][1]/blocks[k][0]) for k in sorted(blocks)]
    return dict(control_ms=statistics.geometric_mean(times[0]),candidate_ms=statistics.geometric_mean(times[1]),
        measured_ratio=math.exp(statistics.mean(logs)),paired_log_ratios=logs,
        repeat_log_ratios=[statistics.mean(math.log(blocks[r,l][1]/blocks[r,l][0]) for l in range(3)) for r in range(repeats)],
        samples=2*len(blocks),samples_sha256=sha(path))


def nnls(x,y):
    """用坐标下降拟合非负系数，并检查最优性残差。"""
    if not x or len(x)!=len(y):raise ValueError('训练矩阵为空或长度不同。')
    width=len(x[0]);coeff=[0.0]*width
    matrix=[[v/positive(target) for v in row] for row,target in zip(x,y)]
    if any(len(r)!=width or any(not math.isfinite(v) or v<0 for v in r) for r in matrix):raise ValueError('训练特征无效。')
    residual=[1.0]*len(y);ridge=1e-8
    diagonal=[sum(r[j]**2 for r in matrix)+ridge for j in range(width)]
    for iteration in range(100000):
        for j in range(width):
            before=coeff[j]
            after=max(0.0,before+(sum(r[j]*e for r,e in zip(matrix,residual))-ridge*before)/diagonal[j])
            delta=after-before;coeff[j]=after
            for k in range(len(residual)):residual[k]-=matrix[k][j]*delta
        gradients=[sum(r[j]*e for r,e in zip(matrix,residual))-ridge*coeff[j] for j in range(width)]
        violation=max(abs(g) if coeff[j]>0 else max(g,0) for j,g in enumerate(gradients))
        if violation<1e-7:break
    else:raise ValueError('非负拟合未收敛，不能冻结模型。')
    return coeff,dict(iterations=iteration+1,optimality_residual=violation,ridge=ridge,
        objective='sum of squared relative wall-time errors with nonnegative coefficients')


def estimate(model,features):
    if len(features)!=len(model['coefficients_ms']) or any(type(v) not in (int,float) or not math.isfinite(v) or v<0 for v in features):
        raise ValueError('动态特征无效。')
    return positive(math.fsum(a*b for a,b in zip(model['coefficients_ms'],features)))


def verify_model(model):
    definition={k:v for k,v in model.items() if k!='model_sha256'}
    if digest(definition)!=model['model_sha256']:raise ValueError('冻结模型身份不同。')
    if model['implementation_sha256']!=sha(Path(__file__)):raise ValueError('预测实现与冻结模型不同。')


def inputs(a):
    plan=load(a.payload/'plan.json');features=load(a.features)
    if features['plan_sha256']!=sha(a.payload/'plan.json') or features['binary_sha256']!=plan['binary_sha256']:
        raise ValueError('特征计划或二进制身份不同。')
    if features['domain']!=plan['domain'] or features['feature_names']!=plan['features']:raise ValueError('特征范围不同。')
    values={}
    for r in features['records']:
        key=(r['id'],r['arm'])
        if key in values:raise ValueError('特征记录重复。')
        values[key]=r
    if set(values)!={(c['id'],arm) for c in plan['cases'] for arm in (0,1)}:raise ValueError('特征矩阵不完整。')
    return plan,features,values


def fit(a):
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    plan,features,values=inputs(a);x=[];y=[];groups=[];samples=[]
    for case in plan['cases']:
        if case['split']!='training':continue
        s=paired_samples(a.samples/(case['id'].removeprefix('conv-')+'.jsonl'),case['id'],plan['repeats'])
        groups.append(case['id']);samples.append(dict(id=case['id'],**s))
        for arm,key in ((0,'control_ms'),(1,'candidate_ms')):x.append(values[case['id'],arm]['features']);y.append(s[key])
    coeff,solver=nnls(x,y)
    model=dict(schema=3,kind='empirical-full-operator-family-wall-model',domain=plan['domain'],
        binary_sha256=plan['binary_sha256'],feature_names=plan['features'],coefficients_ms=coeff,
        training_groups=groups,training_samples=samples,solver=solver,
        implementation_sha256=sha(Path(__file__)),extractor_sha256=features['extractor_sha256'],
        plan_sha256=sha(a.payload/'plan.json'),features_sha256=sha(a.features),
        target='geometric mean wall milliseconds per call in the declared paired fixture',
        limits=['one fixed binary, one algorithm pair, seed 42, four pinned K1 cores, 1600000 kHz snapshots',
                'wall target includes worker dispatch, external calls, waits and amortized counter overhead',
                'census is a feature extractor; it does not time omitted callees',
                'coefficients do not identify causal hardware instruction costs',
                'no new binary, new algorithm, other core placement or frequency coverage'])
    model['model_sha256']=digest(model);write(out/'model.json',model);seal(out)


def evaluate(a):
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    plan,features,values=inputs(a);model=load(a.model);verify_model(model)
    if model['domain']!=plan['domain'] or model['plan_sha256']!=sha(a.payload/'plan.json') or model['extractor_sha256']!=features['extractor_sha256']:
        raise ValueError('评估范围与冻结模型不同。')
    records=[];start=time.perf_counter()
    for case in plan['cases']:
        if case['split']!=a.split:continue
        if case['id'] in model['training_groups']:raise ValueError('独立评估组与训练组重叠。')
        s=paired_samples(a.samples/(case['id'].removeprefix('conv-')+'.jsonl'),case['id'],plan['repeats'])
        control=estimate(model,values[case['id'],0]['features']);candidate=estimate(model,values[case['id'],1]['features'])
        ratio=candidate/control
        records.append(dict(group=case['id'],split=case['split'],predicted_control_ms=control,
            predicted_candidate_ms=candidate,predicted_ratio=ratio,scope_matched=True,
            log_ratio_error=math.log(s['measured_ratio']/ratio),
            gain_error_percentage_points=100*(s['measured_ratio']-ratio),**s))
    result=dict(schema=3,domain=model['domain'],model_sha256=model['model_sha256'],
        model_file_sha256=sha(a.model),training_groups=model['training_groups'],records=records,
        elapsed_seconds=time.perf_counter()-start,split=a.split,automatic_action='none',
        interval_limit='nominal coverage requires exchangeable shape groups within the declared fixture domain')
    if a.split=='test':
        if not a.calibration:raise ValueError('最终检查必须使用冻结的误差校准记录。')
        validation=load(a.calibration)
        if validation['split']!='calibration' or any(r['split']!='calibration' for r in validation['records']):raise ValueError('误差校准分组不同。')
        expected={c['id'] for c in plan['cases'] if c['split']=='calibration'}
        if {r['group'] for r in validation['records']}!=expected:raise ValueError('误差校准组不完整。')
        result['calibration_sha256']=sha(a.calibration)
        for row in records:
            error,meta=conformal(validation,model['model_sha256'],a.coverage,row['group'],model['domain'])
            if error is None:raise ValueError('误差校准不能产生有限界限。')
            ratio=row['predicted_ratio'];low=ratio*math.exp(-error);high=ratio*math.exp(error)
            row.update(predicted_gain=1-ratio,gain_interval=[1-high,1-low],calibration=meta,
                covered=low<=row['measured_ratio']<=high,
                direction='faster' if high<1 else 'slower' if low>1 else 'uncertain')
        result.update(requested_coverage=a.coverage,observed_covered=sum(r['covered'] for r in records),
            observed_total=len(records),maximum_gain_error_percentage_points=max(abs(r['gain_error_percentage_points']) for r in records))
        lines=['# 完整卷积算子独立检查','','所有候选均保留。模型只用于声明范围内的形状比较。',
            '区间覆盖声明依赖形状组的可交换性。结果不证明新算法或新二进制的预测精度。','',
            '| 负载 | 预测收益 | 预测区间 | 实测收益 | 区间覆盖 |','| --- | ---: | --- | ---: | --- |']
        for row in records:
            lo,hi=row['gain_interval'];lines.append(f'| {row["group"]} | {100*row["predicted_gain"]:.3f}% | {100*lo:.3f}% 至 {100*hi:.3f}% | {100*(1-row["measured_ratio"]):.3f}% | {row["covered"]} |')
        lines+=['',f'保留检查组覆盖数为 {result["observed_covered"]}/{len(records)}。',
            '九个保留组只能提供有限的覆盖率证据，不能确认总体覆盖率恰好等于声明值。',
            '拟合系数不表示某一硬件部件的因果成本。','']
        (out/'report.md').write_text('\n'.join(lines))
    write(out/'evaluation.json',result);seal(out)


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True)
    for action in ('fit','evaluate'):
        q=sub.add_parser(action);q.add_argument('payload',type=Path);q.add_argument('--features',type=Path,required=True)
        q.add_argument('--samples',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
        if action=='evaluate':
            q.add_argument('--model',type=Path,required=True);q.add_argument('--split',choices=('calibration','test'),required=True)
            q.add_argument('--calibration',type=Path);q.add_argument('--coverage',type=float,default=.95)
    a=p.parse_args();fit(a) if a.action=='fit' else evaluate(a)


if __name__=='__main__':main()
