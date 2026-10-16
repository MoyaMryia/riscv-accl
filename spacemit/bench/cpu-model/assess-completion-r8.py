#!/usr/bin/env python3
"""分开核验机制校准、机制后测和数值等价重排。"""
import argparse
from collections import defaultdict
from itertools import combinations
import math
from pathlib import Path
import statistics
from audit import receipts
from common import digest, read, write
import model
import state8


def pair(rows, data, predicted):
    rows = sorted(rows, key=lambda row: row['arm'])
    if len(rows) != 2 or [r['arm'] for r in rows] != [0, 1]:
        raise ValueError('两个目标版本不完整。')
    ids = [r['id'] for r in rows]
    truth = data['cycles'][ids[1]] / data['cycles'][ids[0]]
    repeats = [data['slopes'][ids[1]][key] / value for key, value in data['slopes'][ids[0]].items()]
    predictions = {}
    for name in ('state3', 'state6', 'state8'):
        costs = [predicted[r['id']][name] for r in rows]
        ratio = costs[1] / costs[0]
        predictions[name] = dict(cycles=costs, ratio=ratio, ratio_error_percentage_points=100 * abs(ratio - truth),
            direction_sign_agreement=((ratio > 1) - (ratio < 1)) == ((truth > 1) - (truth < 1)),
            score=max([abs(math.log(p / data['cycles'][r['id']])) for r, p in zip(rows, costs)] + [abs(math.log(ratio / truth))]))
    return dict(ids=ids, packets=rows[0]['packets'], observed_cycles=[data['cycles'][i] for i in ids], observed_ratio=truth,
        observed_change_below_one_percent=abs(truth - 1) < .01, paired_repeat_ratio_range=[min(repeats), max(repeats)],
        repeat_range_crosses_one=min(repeats) <= 1 <= max(repeats), predictions=predictions, retained=True)


def metrics(versions):
    result = {}
    for name in ('state3', 'state6', 'state8'):
        factors = [max(p / actual, actual / p) for v in versions
            for p, actual in zip(v['predictions'][name]['cycles'], v['observed_cycles'])]
        errors = [v['predictions'][name]['ratio_error_percentage_points'] for v in versions]
        discernible = [v for v in versions if not v['observed_change_below_one_percent'] and not v['repeat_range_crosses_one']]
        result[name] = dict(functions=len(factors), versions=len(versions),
            median_cycle_error_factor=statistics.median(factors), maximum_cycle_error_factor=max(factors),
            median_ratio_error_percentage_points=statistics.median(errors), maximum_ratio_error_percentage_points=max(errors),
            discernible_versions=len(discernible), discernible_direction_agreement=sum(v['predictions'][name]['direction_sign_agreement'] for v in discernible))
    return result


def priorities(versions):
    result = {}
    for name in ('state3', 'state6', 'state8'):
        ordered = sorted(versions, key=lambda v: (v['predictions'][name]['ratio'], v['group']))
        concordant = discordant = predicted_ties = observed_overlap = 0
        for left, right in combinations(versions, 2):
            delta = left['predictions'][name]['ratio'] - right['predictions'][name]['ratio']
            a, b = left['paired_repeat_ratio_range'], right['paired_repeat_ratio_range']
            if delta == 0:
                predicted_ties += 1
            elif max(a[0], b[0]) <= min(a[1], b[1]):
                observed_overlap += 1
            elif delta * (left['observed_ratio'] - right['observed_ratio']) > 0:
                concordant += 1
            else:
                discordant += 1
        result[name] = dict(rows=[dict(priority=i + 1, group=v['group'], ids=v['ids'],
            predicted_ratio=v['predictions'][name]['ratio'], observed_ratio=v['observed_ratio'], retained=True,
            prediction_interval=None) for i, v in enumerate(ordered)], concordant_pairs=concordant,
            discordant_pairs=discordant, predicted_ties=predicted_ties, observed_repeat_overlap=observed_overlap,
            mean_observed_ratio_first_three=statistics.mean(v['observed_ratio'] for v in ordered[:3]))
    return result


def main(a):
    plan, frozen = read(a.plan), read(a.model)
    if digest(Path(__file__).with_name('state8.py')) != frozen['engine_files']['state8.py']:
        raise ValueError('第八轮冻结引擎身份不同。')
    if frozen['training_plan_sha256'] != digest(a.plan):
        raise ValueError('第八轮计划身份不同。')
    if a.stage != 'training' and digest(a.run / 'frozen-model.json') != digest(a.model):
        raise ValueError('板端冻结模型身份不同。')
    receipts(a.run)
    data = model.observations(plan, a.run, a.stage)
    p = state8.prepare_parameters(frozen['parameters'])
    predicted, grouped, validation = {}, defaultdict(list), defaultdict(list)
    for row in plan['records']:
        if row['split'] != a.stage:
            continue
        predicted[row['id']] = dict(row['prior_cycles'], state8=state8.steady(state8.compiled(row), p))
        (validation if row['semantic_pair'] else grouped)[row['group']].append(row)
    groups = []
    for name, rows in sorted(grouped.items()):
        if len(rows) != 4:
            raise ValueError('机制组不完整。')
        variants = [pair([r for r in rows if r['packets'] == packets], data, predicted) for packets in (9, 21)]
        groups.append(dict(group=name, family=rows[0]['family'], type_order=rows[0]['type_order'], gap=rows[0]['gap'], chains=rows[0]['chains'],
            variants=variants, score=max(v['predictions']['state8']['score'] for v in variants), retained=True, semantic_pair=False))
    positives, dump_pairs = [], 0
    for name, rows in sorted(validation.items()):
        version = pair(rows, data, predicted)
        for length in plan['dump_lengths']:
            outputs = [(a.run / 'dumps' / f'{identifier}-{length}.bin').read_bytes() for identifier in version['ids']]
            if outputs[0] != outputs[1]:
                raise ValueError('重排的完整输出不同。')
            dump_pairs += 1
        positives.append(dict(group=name, **version, semantic_pair=True))
    versions = [v for g in groups for v in g['variants']]
    result = dict(schema=8, stage=a.stage, model_sha256=digest(a.model), plan_sha256=digest(a.plan), observations=data,
        groups=groups, mechanism_metrics=metrics(versions), semantic_validation=positives, complete_semantic_dump_pairs=dump_pairs,
        semantic_metrics=metrics(positives) if positives else None, prediction_confidence=None,
        limits=['机制目标版本没有通用数值等价声明。', '重排检查不转用机制组的校准界限。',
            '名义覆盖依赖固定范围内配置组可交换性。', '测量重复范围不是预测置信区间。', '全部候选继续保留。'])
    if positives:
        result['semantic_priorities'] = priorities(positives)
        result['limits'].append('排序比较中的重复范围重叠只描述观测分离，不能形成预测置信区间。')
    if a.stage == 'calibration':
        rank = math.ceil((len(groups) + 1) * .95)
        if rank > len(groups):
            raise ValueError('校准组不足。')
        bound = sorted(g['score'] for g in groups)[rank - 1]
        result.update(rank=rank, log_bound=bound, factor=math.exp(bound), nominal_group_coverage=.95)
    if a.stage == 'test':
        calibration = read(a.calibration)
        if calibration['model_sha256'] != digest(a.model) or digest(a.run / 'frozen-calibration.json') != digest(a.calibration):
            raise ValueError('板端校准身份不同。')
        for group in groups:
            group['covered'] = group['score'] <= calibration['log_bound']
            for version in group['variants']:
                version['covered'] = version['predictions']['state8']['score'] <= calibration['log_bound']
        result.update(calibration_sha256=digest(a.calibration), groups_covered=sum(g['covered'] for g in groups), group_count=len(groups),
            versions_covered=sum(v['covered'] for v in versions), versions=len(versions),
            semantic_observed_faster=sum(v['observed_ratio'] < .99 for v in positives),
            semantic_observed_slower=sum(v['observed_ratio'] > 1.01 for v in positives))
    write(a.output, result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['training', 'calibration', 'test'])
    for name in ('plan', 'model', 'run', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--calibration', type=Path)
    main(parser.parse_args())
