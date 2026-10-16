#!/usr/bin/env python3
"""只用训练性能比较结果完成顺序与标量队列假设。"""
import argparse
from collections import Counter
import copy
import math
from pathlib import Path
from common import digest, read, write
import model
import state8

HERE = Path(__file__).resolve().parent


def configurations():
    queues = [dict(depth=0, kinds=[], capture='execute')]
    for depth in (1, 2, 3, 4, 8):
        for kinds in (['add', 'mul'], ['add', 'mul', 'load']):
            for capture in ('ready', 'execute'):
                queues.append(dict(depth=depth, kinds=kinds, capture=capture))
    for order in ('none', 'global', 'resource'):
        for queue in queues:
            for policy in ('pending', 'completion'):
                for cross_gap in (0, 3, 5):
                    for load_latency in (1, 3):
                        yield dict(**queue, order=order, policy=policy, cross_gap=cross_gap, load_latency=load_latency)


def parameters(prior, config):
    p = copy.deepcopy(prior)
    p.update(completion_order=config['order'], scalar_queue_depth=config['depth'], scalar_queue_kinds=config['kinds'],
        scalar_capture=config['capture'], waw_policy=config['policy'])
    p['latency']['load'] = config['load_latency']
    p['write_gap'] = {f'{a}:{b}': config['cross_gap'] if (a == 'mul') != (b == 'mul') else 1 if a != 'mul' else 0
        for a in ('add', 'mul', 'load') for b in ('add', 'mul', 'load')}
    return p


def main(a):
    prior = read(a.prior6)
    old = read(a.prior3)
    old_plan = read(a.training_plan)
    if old['plan_sha256'] != digest(a.training_plan):
        raise ValueError('旧训练计划身份不同。')
    rows = [(r, old['training']['cycles'][r['id']], 'r3/' + r['group']) for r in old_plan['records'] if r['split'] == 'training']
    inputs = []
    if len(a.probe_plan) != len(a.assessment):
        raise ValueError('旧机制输入数量不同。')
    for plan_path, assessment_path in zip(a.probe_plan, a.assessment):
        plan, assessment = read(plan_path), read(assessment_path)
        if digest(plan_path) != assessment['plan_sha256']:
            raise ValueError('旧机制计划身份不同。')
        rows += [(r, assessment['observations']['cycles'][r['id']], plan['batch'] + '/' + r['group'])
            for r in plan['records'] if r['family'] != 'reorder']
        inputs.append(dict(plan_sha256=digest(plan_path), assessment_sha256=digest(assessment_path)))
    plan = read(a.plan)
    observations = model.observations(plan, a.run, 'training')
    if plan['prior_models']['state6'] != digest(a.prior6):
        raise ValueError('第六轮模型身份不同。')
    rows += [(r, observations['cycles'][r['id']], 'r8/' + r['group']) for r in plan['records'] if r['split'] == 'training']
    counts = Counter(group for _, _, group in rows)
    programs = [(state8.compiled(r), actual, 1 / counts[group] / len(counts)) for r, actual, group in rows]
    scores, best, selected = [], math.inf, None
    for index, config in enumerate(configurations()):
        p = parameters(prior['parameters'], config)
        prepared = state8.prepare_parameters(p)
        try:
            predictions = [state8.steady(program, prepared) for program, _, _ in programs]
            loss = sum(math.log(pred / actual) ** 2 * weight for pred, (_, actual, weight) in zip(predictions, programs))
        except ValueError as error:
            scores.append(dict(index=index, **config, status='no-steady-period', reason=str(error), retained=True))
            continue
        scores.append(dict(index=index, **config, status='complete', group_mean_squared_log_error=loss, retained=True))
        if loss < best - 1e-10:
            best, selected = loss, p
        if index % 50 == 0:
            print(f'配置 {index}，当前组均方对数误差 {best:.8f}。', flush=True)
    if selected is None:
        raise ValueError('全部假设均未形成稳态。')
    write(a.output, dict(schema=8, parameters=selected, training_functions=len(rows), training_groups=len(counts),
        training_group_mean_squared_log_error=best, candidate_scores=scores,
        prior_model_sha256=digest(a.prior6), old_training_model_sha256=digest(a.prior3), old_training_plan_sha256=digest(a.training_plan),
        diagnostic_inputs=inputs, training_plan_sha256=digest(a.plan), training_run_receipt_sha256=digest(a.run / 'SHA256SUMS'),
        engine_files={name: digest(HERE / name) for name in ('state8.py', 'fit-completion-r8.py')},
        new_training_observations=observations, prediction_confidence=None,
        limits=['只使用本轮训练阶段与旧机制训练数据。', '校准与后测未用于模型选择。',
            '按配置组等权拟合。', '全部模型假设继续保留。', '有效参数不能证明真实硬件结构。']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('prior6', 'prior3', 'training-plan', 'plan', 'run', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('probe-plan', 'assessment'):
        parser.add_argument('--' + name, type=Path, action='append', required=True)
    main(parser.parse_args())
