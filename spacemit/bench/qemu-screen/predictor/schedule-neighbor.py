#!/usr/bin/env python3
"""按实际循环版本建模，并校准组内三个版本的最大误差。"""
import argparse
from collections import defaultdict
import math
from pathlib import Path
import statistics
from analyze import load, write, sha, seal
from model import target
import importlib.util

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('neighbor_scope',HERE/'schedule-family.py')
scope=importlib.util.module_from_spec(spec);spec.loader.exec_module(scope)
measure=scope.measure


def implementation():
    return {name:sha(HERE/name) for name in ('schedule-neighbor.py','schedule-family.py','load-use-evaluate.py','family-model.py')}


def check_plan(plan):
    groups=plan['groups']
    if len(groups)!=80 or len({g['id'] for g in groups})!=80 or len({tuple(g[k] for k in ('m','vl','stride','chains')) for g in groups})!=80:
        raise ValueError('循环模型必须有 80 个唯一配置组。')
    for split,count in [('training',52),('calibration',19),('test',9)]:
        if sum(g['split']==split for g in groups)!=count:raise ValueError('循环模型分组数量不同。')
    if plan['loop_alignment_bytes']!=64 or plan['layout_seed'] is None:
        raise ValueError('必须固定循环对齐与独立代码布局种子。')
    for group in groups:scope.features(group,0)


def loop_costs(plan,samples,split):
    _,analysis=measure.native(plan,samples,split)
    fits=defaultdict(list)
    for row in analysis['loop_fits']:fits[row['id']].append(row['slope'])
    result={}
    for row in plan['records']:
        if row['split']!=split:continue
        values=fits[row['id']]
        if len(values)!=7:raise ValueError('循环成本需要七个完整重复拟合。')
        result[row['group'],row['arm'],row['operations']]=dict(
            cycles_per_loop=statistics.geometric_mean(values),repeat_slopes=values)
    return result,analysis


def estimate(model,group,arm,unroll):
    anchors=sorted([r for r in model['points'] if
        (r['m'],r['stride'],r['chains'],r['arm'],r['unroll'])==
        (group['m'],group['stride'],group['chains'],arm,unroll)],key=lambda r:r['vl'])
    if not anchors:raise ValueError('当前配置缺少对应训练锚点。')
    left=next((r for r in reversed(anchors) if r['vl']<=group['vl']),anchors[0])
    right=next((r for r in anchors if r['vl']>=group['vl']),anchors[-1])
    if left['vl']==right['vl']:
        value=left['cycles_per_loop'];kind='exact-anchor' if group['vl']==left['vl'] else 'clamped-anchor'
    else:
        weight=(group['vl']-left['vl'])/(right['vl']-left['vl'])
        value=math.exp((1-weight)*math.log(left['cycles_per_loop'])+weight*math.log(right['cycles_per_loop']))
        kind='log-cost-interpolation'
    if not math.isfinite(value) or value<=0:raise ValueError('预测循环成本必须为有限正数。')
    return value,dict(kind=kind,anchors=[left['group'],right['group']])


def predict(model,plan,split):
    records=[]
    for group in plan['groups']:
        if group['split']!=split:continue
        variants=[]
        for unroll in (8,32,128):
            a,am=estimate(model,group,0,unroll);b,bm=estimate(model,group,1,unroll)
            variants.append(dict(unroll=unroll,predicted_control_cycles=a,predicted_candidate_cycles=b,
                predicted_ratio=b/a,control_anchors=am,candidate_anchors=bm))
        records.append(dict(group=group['id'],variants=variants))
    return records


def verify_model(model,plan,plan_sha):
    definition={k:v for k,v in model.items() if k!='model_sha256'}
    if measure.digest(definition)!=model['model_sha256'] or model['implementation_sha256']!=implementation():
        raise ValueError('循环模型或实现身份不同。')
    if model['plan_sha256']!=plan_sha or model['binary_sha256']!=plan['binary_sha256']:
        raise ValueError('循环模型适用范围不同。')
    expected={g['id'] for g in plan['groups'] if g['split']=='training'}
    if set(model['training_groups'])!=expected or len(model['training_groups'])!=52 or len(model['points'])!=312:
        raise ValueError('循环模型训练资料不同。')
    points={(r['group'],r['arm'],r['unroll']) for r in model['points']}
    if points!={(g,a,u) for g in expected for a in (0,1) for u in (8,32,128)}:
        raise ValueError('循环模型锚点矩阵不同。')
    groups={g['id']:g for g in plan['groups']}
    for point in model['points']:
        if any(point[k]!=groups[point['group']][k] for k in ('m','vl','stride','chains')):
            raise ValueError('循环模型锚点配置不同。')
        if not math.isfinite(point['cycles_per_loop']) or point['cycles_per_loop']<=0:
            raise ValueError('循环模型锚点不是有限正数。')


def verify_bound(bound,model,plan):
    definition={k:v for k,v in bound.items() if k!='calibration_sha256'}
    if measure.digest(definition)!=bound['calibration_sha256'] or bound['model_sha256']!=model['model_sha256']:
        raise ValueError('组内最大误差界限或模型身份不同。')
    expected={g['id'] for g in plan['groups'] if g['split']=='calibration'}
    if set(bound['calibration_groups'])!=expected or len(bound['calibration_groups'])!=19:
        raise ValueError('组内最大误差校准组不同。')
    if not math.isfinite(bound['maximum_group_log_error']) or bound['maximum_group_log_error']<0:
        raise ValueError('组内最大误差必须为有限非负数。')


LIMITS=['fixed aligned hot e32 load-accumulate loop on CPU 0; not complete-operator wall time',
    'each unroll version has its own measured training anchors; no affine count-cost assumption',
    'VL interpolation and endpoint clamps are empirical assumptions, not hardware laws',
    'group bounds protect all three planned unroll ratios under group exchangeability',
    'nominal coverage targets future paired fixture measurements, not noiseless hardware means',
    'no confidence transfer to other binaries, algorithms, data patterns or thread configurations']


def add_bounds(records,bound):
    factor=math.exp(bound['maximum_group_log_error'])
    for group in records:
        for row in group['variants']:
            ratio=row['predicted_ratio']
            row.update(predicted_gain=1-ratio,gain_interval=[1-ratio*factor,1-ratio/factor])
            if 'measured_ratio' in row:
                row.update(measured_gain=1-row['measured_ratio'],
                    covered=ratio/factor<=row['measured_ratio']<=ratio*factor,
                    direction_match=(ratio<1)==(row['measured_ratio']<1))
        if all('covered' in row for row in group['variants']):
            group['covered']=all(row['covered'] for row in group['variants'])


def main(a):
    plan_path=a.plan or a.payload/'plan.json';plan=load(plan_path);plan_sha=sha(plan_path);check_plan(plan)
    if a.mode!='predict' and sha(a.payload/'measure')!=plan['binary_sha256']:
        raise ValueError('循环夹具二进制身份不同。')
    if a.mode=='fit':
        scope.verify_traces(plan,load(a.traces),plan_sha)
        inventory=load(a.payload/'inventory/inventory.json')
        for function in inventory['functions']:
            branches=[r for r in function['instructions'] if r['objdump_mnemonic']=='bne' and target(r) is not None and target(r)<r['address']]
            if len(branches)!=1 or target(branches[0])%64:
                raise ValueError('实际循环未对齐。')
        measured,analysis=loop_costs(plan,a.samples,'training');points=[]
        for group in plan['groups']:
            if group['split']!='training':continue
            for arm in (0,1):
                for unroll in (8,32,128):
                    points.append(dict(group=group['id'],**{k:group[k] for k in ('m','vl','stride','chains')},
                        arm=arm,unroll=unroll,**measured[group['id'],arm,unroll]))
        model=dict(schema=6,kind='empirical-aligned-loop-scope-model',points=points,
            target_unit='U-mode cycles per loop; loop control included',plan_sha256=plan_sha,
            binary_sha256=plan['binary_sha256'],implementation_sha256=implementation(),
            training_groups=[g['id'] for g in plan['groups'] if g['split']=='training'],
            training_samples_sha256=sha(a.samples),traces_sha256=sha(a.traces),limits=LIMITS)
        model['model_sha256']=measure.digest(model)
        write(a.output/'model.json',model);write(a.output/'native-analysis.json',analysis)
    else:
        model=load(a.model);verify_model(model,plan,plan_sha)
        split='calibration' if a.mode=='calibrate' else 'test';records=predict(model,plan,split)
        common=dict(schema=6,model_sha256=model['model_sha256'],records=records,
            nominal_group_coverage=.95,limits=LIMITS,automatic_action='none')
        if a.mode!='predict':
            measured,analysis=loop_costs(plan,a.samples,split)
            for group in records:
                for row in group['variants']:
                    key=(group['group'],row['unroll'])
                    control=measured[key[0],0,key[1]];candidate=measured[key[0],1,key[1]]
                    ratio=candidate['cycles_per_loop']/control['cycles_per_loop']
                    row.update(measured_ratio=ratio,measured_control_cycles=control['cycles_per_loop'],
                        measured_candidate_cycles=candidate['cycles_per_loop'],
                        absolute_log_error=abs(math.log(row['predicted_ratio']/ratio)))
                group['maximum_log_error']=max(r['absolute_log_error'] for r in group['variants'])
            common['samples_sha256']=sha(a.samples);write(a.output/'native-analysis.json',analysis)
        if a.mode=='calibrate':
            common.update(calibration_groups=[r['group'] for r in records],order_statistic=19,
                maximum_group_log_error=max(r['maximum_log_error'] for r in records))
            common['calibration_sha256']=measure.digest(common)
            write(a.output/'calibration.json',common)
        else:
            bound=load(a.calibration);verify_bound(bound,model,plan);add_bounds(records,bound)
            common['calibration_sha256']=bound['calibration_sha256']
            if a.mode=='test':
                common.update(observed_groups_covered=sum(r['covered'] for r in records),observed_groups_total=len(records),
                    observed_variants_covered=sum(v['covered'] for r in records for v in r['variants']),
                    observed_variants_total=sum(len(r['variants']) for r in records))
                write(a.output/'evaluation.json',common)
            else:
                write(a.output/'prediction.json',common)
                lines=['# 对齐循环范围预测','','全部候选均保留。',
                    '声明的 95% 组覆盖依赖固定范围内配置组的可交换性。',
                    '每组界限同时保护三个计划展开版本。',
                    '目标为用户态循环周期，不能转移到完整算子或其他二进制。','',
                    '| 保留组 | 展开数量 | 预测收益 | 声明区间 |',
                    '| --- | ---: | ---: | --- |']
                for group in records:
                    for row in group['variants']:
                        lo,hi=row['gain_interval']
                        lines.append(f'| {group["group"]} | {row["unroll"]} | {100*row["predicted_gain"]:.3f}% | {100*lo:.3f}% 至 {100*hi:.3f}% |')
                (a.output/'report.md').write_text('\n'.join(lines)+'\n')
    seal(a.output)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['fit','calibrate','test','predict'])
    p.add_argument('--payload',type=Path);p.add_argument('--plan',type=Path);p.add_argument('--samples',type=Path)
    p.add_argument('--traces',type=Path);p.add_argument('--model',type=Path);p.add_argument('--calibration',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if not a.plan and not a.payload:p.error('必须提供夹具或冻结计划。')
    if a.mode!='predict' and (not a.payload or not a.samples):p.error('测量阶段必须提供夹具与样本。')
    if a.mode=='fit' and not a.traces:p.error('拟合必须提供完整轨迹。')
    if a.mode!='fit' and not a.model:p.error('必须提供冻结模型。')
    if a.mode in ('test','predict') and not a.calibration:p.error('必须提供先前冻结的误差界限。')
    a.output.mkdir(parents=True,exist_ok=False);main(a)
