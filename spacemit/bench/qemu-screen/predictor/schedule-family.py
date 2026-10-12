#!/usr/bin/env python3
"""拟合固定组合指令范围，并使用分阶段独立误差校准。"""
import argparse
import importlib.util
import json
import math
from pathlib import Path
from analyze import load, write, sha, seal

HERE=Path(__file__).resolve().parent


def module(name):
    spec=importlib.util.spec_from_file_location('schedule_'+name.replace('-','_'),HERE/(name+'.py'))
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


family=module('family-model')
measure=module('load-use-evaluate')


def implementation():
    return {name:sha(HERE/name) for name in ('schedule-family.py','family-model.py','load-use-evaluate.py')}


def features(group,arm):
    m,vl,stride,chains=(group[k] for k in ('m','vl','stride','chains'))
    if m not in (1,2,4) or not 1<=vl<=8*m or stride not in (0,16) or chains not in (2,4) or arm not in (0,1):
        raise ValueError('组合指令特征超出范围。')
    fraction=vl/(8*m)
    return [float(arm==a and m==b and stride==s and chains==c)*(fraction if k else 1-fraction)
        for a in (0,1) for b in (1,2,4) for s in (0,16) for c in (2,4) for k in (0,1)]


def check_plan(plan):
    groups=plan['groups']
    if len({g['id'] for g in groups})!=52 or len(groups)!=52:
        raise ValueError('组合指令计划必须有 52 个唯一组。')
    if len({tuple(g[k] for k in ('m','vl','stride','chains')) for g in groups})!=52:
        raise ValueError('相同配置不能作为不同误差组。')
    for split,count in [('training',24),('calibration',19),('test',9)]:
        if sum(g['split']==split for g in groups)!=count:raise ValueError('分组数量不同。')
    for group in groups:features(group,0)


def verify_model(model,plan,plan_sha):
    definition={k:v for k,v in model.items() if k!='model_sha256'}
    if measure.digest(definition)!=model['model_sha256'] or model['implementation_sha256']!=implementation():
        raise ValueError('组合指令模型或实现身份不同。')
    if model['plan_sha256']!=plan_sha or model['binary_sha256']!=plan['binary_sha256']:
        raise ValueError('组合指令模型适用范围不同。')
    expected={g['id'] for g in plan['groups'] if g['split']=='training'}
    if set(model['training_groups'])!=expected or len(model['training_groups'])!=24:
        raise ValueError('训练组不同。')


def estimate(model,group,arm):
    value=math.fsum(x*y for x,y in zip(features(group,arm),model['coefficients']))
    if not math.isfinite(value) or value<=0:raise ValueError('组合成本必须为有限正数。')
    return value


def verify_traces(plan,traces,plan_sha):
    measure.predictions(plan,traces,plan_sha)
    definitions={r['id']:r for r in plan['records']}
    for row in traces['records']:
        definition=definitions[row['id']]
        center=next(r for r in row['cost']['scenarios'] if r['name']=='central-warm')
        if len(center['threads'])!=1:raise ValueError('组合轨迹必须为单线程。')
        keys=next(iter(center['threads'].values()))['keys']
        m,vl,s=(definition[k] for k in ('m','vl','stride'))
        expected=row['loops']*definition['operations']
        arithmetic=f'vfadd.vv|32|{m}|{vl}|0|0'
        loadname='vlse32.v' if s else 'vle32.v'
        stride='None' if s and vl==1 else str(s)
        loading=f'{loadname}|32|{m}|{vl}|{stride}|4096'
        if keys.get(arithmetic)!=expected or keys.get(loading)!=expected:
            raise ValueError('实际向量配置或动态数量不同。')


def predicted(model,plan):
    result={}
    for group in plan['groups']:
        a,b=(estimate(model,group,arm) for arm in (0,1))
        result[group['id']]=dict(group=group['id'],split=group['split'],
            predicted_control_cycles_per_pair=a,predicted_candidate_cycles_per_pair=b,predicted_ratio=b/a)
    return result


def verify_calibration(calibration,model,plan):
    definition={k:v for k,v in calibration.items() if k!='calibration_sha256'}
    if measure.digest(definition)!=calibration['calibration_sha256'] or calibration['model_sha256']!=model['model_sha256']:
        raise ValueError('组合指令误差界限或模型身份不同。')
    expected={g['id'] for g in plan['groups'] if g['split']=='calibration'}
    if set(calibration['calibration_groups'])!=expected or len(calibration['calibration_groups'])!=19:
        raise ValueError('组合指令误差校准组不同。')
    q=calibration['maximum_absolute_log_ratio_error']
    if not math.isfinite(q) or q<0:raise ValueError('误差界限必须为有限非负数。')


def intervals(records,calibration):
    factor=math.exp(calibration['maximum_absolute_log_ratio_error'])
    for row in records:
        ratio=row['predicted_ratio']
        row.update(predicted_gain=1-ratio,gain_interval=[1-ratio*factor,1-ratio/factor])
        if 'measured_ratio' in row:
            row.update(measured_gain=1-row['measured_ratio'],
                covered=ratio/factor<=row['measured_ratio']<=ratio*factor)


LIMITS=['fixed CPU 0 hot e32 load and accumulation schedule; not a complete operator',
    'coefficients describe combined sequence costs, not causal hardware components',
    'the VL basis can extrapolate below half VL; independent groups assess this fixed domain',
    'nominal coverage requires exchangeable groups within the fixed plan',
    'target is a future paired fixture measurement, not a noiseless hardware mean',
    'no confidence transfer to another binary, algorithm pair, data pattern or thread configuration']


def main(a):
    plan_path=a.plan or a.payload/'plan.json';plan=load(plan_path);check_plan(plan);plan_sha=sha(plan_path)
    if a.mode!='predict':
        if not a.payload or sha(a.payload/'measure')!=plan['binary_sha256']:
            raise ValueError('原生组合夹具二进制身份不同。')
    if a.mode=='fit':
        if not a.traces:raise ValueError('必须提供完整实际轨迹批次。')
        verify_traces(plan,load(a.traces),plan_sha)
        measured,diagnostic=measure.native(plan,a.samples,'training')
        x=[];y=[]
        for group in plan['groups']:
            if group['split']!='training':continue
            row=measured[group['id']]
            for arm,key in [(0,'control_cycles_per_pair'),(1,'candidate_cycles_per_pair')]:
                x.append(features(group,arm));y.append(row[key])
        coefficients,solver=family.nnls(x,y)
        solver={**solver,'objective':'sum of squared relative combined-pair cycle errors with nonnegative coefficients'}
        model=dict(schema=5,kind='empirical-mixed-sequence-scope-model',coefficients=coefficients,
            target_unit='U-mode cycles per address-load-accumulate pair; loop control removed',
            binary_sha256=plan['binary_sha256'],plan_sha256=plan_sha,
            implementation_sha256=implementation(),solver=solver,
            training_groups=[g['id'] for g in plan['groups'] if g['split']=='training'],
            training_samples_sha256=sha(a.samples),traces_sha256=sha(a.traces),limits=LIMITS)
        model['model_sha256']=measure.digest(model)
        write(a.output/'model.json',model)
        write(a.output/'training-analysis.json',dict(measured=measured,native=diagnostic))
    else:
        if not a.model:raise ValueError('必须提供冻结模型。')
        model=load(a.model);verify_model(model,plan,plan_sha)
        predictions=predicted(model,plan)
        if a.mode=='predict':
            if not a.calibration:raise ValueError('必须提供冻结误差界限。')
            calibration=load(a.calibration);verify_calibration(calibration,model,plan)
            rows=[predictions[g['id']] for g in plan['groups'] if g['split']=='test']
            intervals(rows,calibration)
            write(a.output/'prediction.json',dict(schema=5,model_sha256=model['model_sha256'],
                calibration_sha256=calibration['calibration_sha256'],records=rows,
                nominal_coverage=.95,limits=LIMITS,automatic_action='none'))
            lines=['# 固定组合指令范围预测','','全部候选均保留。',
                '区间声明为 95%，并依赖固定范围内配置组的可交换性。',
                '组合成本不是完整算子墙钟时间，也不是硬件部件因果成本。',
                '区间不能转移到新二进制或新算法对。','',
                '| 保留组 | 预测收益 | 声明区间 |','| --- | ---: | --- |']
            for row in rows:
                lo,hi=row['gain_interval']
                lines.append(f'| {row["group"]} | {100*row["predicted_gain"]:.3f}% | {100*lo:.3f}% 至 {100*hi:.3f}% |')
            (a.output/'report.md').write_text('\n'.join(lines)+'\n')
        else:
            split='calibration' if a.mode=='calibrate' else 'test'
            measured,diagnostic=measure.native(plan,a.samples,split)
            rows=[]
            for name,m in measured.items():
                row={**predictions[name],**m}
                row['absolute_log_ratio_error']=abs(math.log(row['predicted_ratio']/row['measured_ratio']))
                rows.append(row)
            common=dict(schema=5,model_sha256=model['model_sha256'],records=rows,
                samples_sha256=sha(a.samples),nominal_coverage=.95,limits=LIMITS,automatic_action='none')
            write(a.output/'native-analysis.json',diagnostic)
            if a.mode=='calibrate':
                common.update(calibration_groups=[r['group'] for r in rows],order_statistic=19,
                    maximum_absolute_log_ratio_error=max(r['absolute_log_ratio_error'] for r in rows))
                common['calibration_sha256']=measure.digest(common)
                write(a.output/'calibration.json',common)
            else:
                if not a.calibration:raise ValueError('必须提供先前冻结的误差界限。')
                calibration=load(a.calibration);verify_calibration(calibration,model,plan)
                intervals(rows,calibration)
                common.update(calibration_sha256=calibration['calibration_sha256'],
                    observed_covered=sum(r['covered'] for r in rows),observed_total=len(rows))
                write(a.output/'evaluation.json',common)
    seal(a.output)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['fit','calibrate','test','predict'])
    p.add_argument('--payload',type=Path);p.add_argument('--plan',type=Path)
    p.add_argument('--samples',type=Path);p.add_argument('--traces',type=Path)
    p.add_argument('--model',type=Path);p.add_argument('--calibration',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if not a.payload and not a.plan:p.error('必须提供夹具或冻结计划。')
    if a.mode!='predict' and (not a.payload or not a.samples):p.error('测量阶段必须提供夹具和原始样本。')
    a.output.mkdir(parents=True,exist_ok=False);main(a)
