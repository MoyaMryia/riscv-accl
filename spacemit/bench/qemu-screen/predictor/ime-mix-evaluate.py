#!/usr/bin/env python3
"""检查冻结分项模型对 IME 混合循环的独立预测误差。"""
import argparse
from collections import defaultdict
import importlib.util
import math
from pathlib import Path
import statistics
from analyze import load, write, sha, seal

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('ime_mix_measure', HERE/'load-use-evaluate.py')
measure = importlib.util.module_from_spec(spec)
spec.loader.exec_module(measure)


def implementation():
    return {name: sha(HERE/name) for name in ('ime-mix-evaluate.py', 'load-use-evaluate.py')}


def check_plan(plan):
    groups = plan['groups']
    if len(groups) != 28 or len({g['id'] for g in groups}) != 28:
        raise ValueError('IME 混合计划必须有 28 个唯一组。')
    if len({(g['chains'], g['gap']) for g in groups}) != 28:
        raise ValueError('相同配置不能作为独立组。')
    for split, count in [('calibration',19), ('test',9)]:
        if sum(g['split']==split for g in groups) != count:
            raise ValueError('独立分组数量不同。')


def predictions(plan, source, plan_sha):
    if source['status'] != 'complete' or source['plan_sha256'] != plan_sha or source['binary_sha256'] != plan['binary_sha256']:
        raise ValueError('实际轨迹批次未完成或身份不同。')
    expected = {(r['id'], n) for r in plan['records'] for n in plan['trace_lengths']}
    rows = source['records']
    if len(rows) != len(expected) or {(r['id'],r['loops']) for r in rows} != expected:
        raise ValueError('实际轨迹矩阵不完整。')
    indexed = {(r['id'],r['loops']):r for r in rows}
    result = {}
    for definition in plan['records']:
        points = []
        for n in plan['trace_lengths']:
            row = indexed[definition['id'],n]
            if (row['group'], row['arm'], row['unroll']) != (definition['group'], definition['arm'], definition['operations']):
                raise ValueError('实际轨迹配置不同。')
            cost = row['cost']
            if cost['model_sha256'] != plan['frozen_component_model_sha256'] or not cost['coverage']['trace_complete']:
                raise ValueError('分项模型不同或轨迹不完整。')
            center = next(s for s in cost['scenarios'] if s['name']=='central-warm')
            points.append((n, center['cohort_cycles']))
        result[definition['group'], definition['arm'], definition['operations']] = measure.linear(points)['slope']
    return result


def native_loops(plan, path, split):
    _, diagnostic = measure.native(plan, path, split)
    values = defaultdict(list)
    for row in diagnostic['loop_fits']:
        values[row['id']].append(row['slope'])
    costs = {}
    for row in plan['records']:
        if row['split'] == split:
            if len(values[row['id']]) != 7:
                raise ValueError('每个版本必须有七个重复拟合。')
            costs[row['group'], row['arm'], row['operations']] = statistics.geometric_mean(values[row['id']])
    return costs, diagnostic


def verify_bound(bound, plan, plan_sha, predictions_sha):
    identity = {k:v for k,v in bound.items() if k != 'calibration_sha256'}
    if measure.digest(identity) != bound['calibration_sha256'] or bound['implementation_sha256'] != implementation():
        raise ValueError('误差界限或实现身份不同。')
    for key, expected in [('plan_sha256',plan_sha), ('binary_sha256',plan['binary_sha256']),
        ('model_sha256',plan['frozen_component_model_sha256']), ('predictions_sha256',predictions_sha)]:
        if bound[key] != expected:
            raise ValueError('误差界限适用范围不同。')
    expected = {g['id'] for g in plan['groups'] if g['split']=='calibration'}
    if len(bound['records']) != 19 or {r['group'] for r in bound['records']} != expected:
        raise ValueError('误差校准组不完整。')
    score = max(r['maximum_log_error'] for r in bound['records'])
    if not math.isfinite(score) or score < 0 or score != bound['maximum_group_log_error']:
        raise ValueError('冻结误差分数不同。')


def main(a):
    plan = load(a.payload/'plan.json')
    check_plan(plan)
    plan_sha = sha(a.payload/'plan.json')
    if sha(a.payload/'measure') != plan['binary_sha256']:
        raise ValueError('原生夹具二进制不同。')
    predicted = predictions(plan, load(a.predictions), plan_sha)
    split = 'calibration' if a.mode=='calibrate' else 'test'
    measured, diagnostic = native_loops(plan, a.samples, split)
    records = []
    for group in plan['groups']:
        if group['split'] != split:
            continue
        variants = []
        for unroll in (8,32,128):
            pc, pn = (predicted[group['id'],arm,unroll] for arm in (0,1))
            mc, mn = (measured[group['id'],arm,unroll] for arm in (0,1))
            pr, mr = pn/pc, mn/mc
            variants.append(dict(unroll=unroll, predicted_control_cycles=pc, predicted_candidate_cycles=pn,
                measured_control_cycles=mc, measured_candidate_cycles=mn, predicted_ratio=pr, measured_ratio=mr,
                predicted_gain=1-pr, measured_gain=1-mr, absolute_log_error=abs(math.log(pr/mr)),
                control_relative_cycle_error=pc/mc-1, candidate_relative_cycle_error=pn/mn-1,
                direction_match=(pr<1)==(mr<1)))
        records.append(dict(group=group['id'], variants=variants,
            maximum_log_error=max(v['absolute_log_error'] for v in variants)))
    result = dict(schema=7, model_sha256=plan['frozen_component_model_sha256'],
        plan_sha256=plan_sha, binary_sha256=plan['binary_sha256'], predictions_sha256=sha(a.predictions),
        implementation_sha256=implementation(), samples_sha256=sha(a.samples), records=records,
        nominal_group_coverage=.95, limits=plan['limits']+[
            'nominal group coverage assumes exchangeable groups within this fixed binary and data domain',
            'target is a future paired fixture measurement; no noiseless hardware-mean coverage claim',
            'ratio bounds do not calibrate absolute cycles or full-operator wall time'], automatic_action='none')
    a.output.mkdir(parents=True, exist_ok=False)
    write(a.output/'native-analysis.json', diagnostic)
    if a.mode == 'calibrate':
        result.update(order_statistic=19, maximum_group_log_error=max(r['maximum_log_error'] for r in records))
        result['calibration_sha256'] = measure.digest(result)
        write(a.output/'calibration.json', result)
    else:
        bound = load(a.calibration)
        verify_bound(bound, plan, plan_sha, sha(a.predictions))
        factor = math.exp(bound['maximum_group_log_error'])
        for group in records:
            for row in group['variants']:
                ratio = row['predicted_ratio']
                row['gain_interval'] = [1-ratio*factor, 1-ratio/factor]
                row['covered'] = row['gain_interval'][0] <= row['measured_gain'] <= row['gain_interval'][1]
            group['covered'] = all(r['covered'] for r in group['variants'])
        result.update(calibration_sha256=bound['calibration_sha256'],
            observed_groups_covered=sum(r['covered'] for r in records), observed_groups_total=len(records),
            observed_variants_covered=sum(v['covered'] for r in records for v in r['variants']),
            observed_variants_total=sum(len(r['variants']) for r in records))
        write(a.output/'evaluation.json', result)
    seal(a.output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['calibrate','test'])
    p.add_argument('--payload', type=Path, required=True)
    p.add_argument('--predictions', type=Path, required=True)
    p.add_argument('--samples', type=Path, required=True)
    p.add_argument('--calibration', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.mode=='test' and not a.calibration:
        p.error('后测必须提供先前冻结的误差界限。')
    main(a)
