#!/usr/bin/env python3
"""核对配对卷积样本，并分开报告墙钟收益与用户态周期。"""
import argparse
from collections import defaultdict
import importlib.util
import json
import math
from pathlib import Path
import random
import statistics
from analyze import load, write, sha, seal

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('matched_family', HERE/'family-model.py')
family = importlib.util.module_from_spec(spec)
spec.loader.exec_module(family)


def evaluate(path, case, mode):
    paired = family.paired_samples(path, case, 7)
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    scope = 'sync-paused-user-cycles' if mode == 'bench-roi' else 'full-call-user-cycles'
    if any(row.get('counter_scope') != scope for row in rows):
        raise ValueError('周期计数范围不同。')
    groups = defaultdict(list)
    for row in rows:
        if not row['phases']:
            groups[row['arm'], row['repeat']].append(row)
    arms = []
    for arm in (0, 1):
        slopes = [[] for _ in range(4)]
        for repeat in range(7):
            values = groups[arm, repeat]
            calls = [row['calls'] for row in values]
            if len(set(calls)) != 3:
                raise ValueError('周期斜率需要三个不同调用长度。')
            mean = statistics.mean(calls)
            denominator = sum((n-mean)**2 for n in calls)
            for cpu in range(4):
                cycles = [next(t['cycles'] for t in row['threads'] if t['cpu'] == cpu) for row in values]
                slope = sum((n-mean)*v for n, v in zip(calls, cycles))/denominator
                if slope <= 0:
                    raise ValueError('周期斜率必须为正。')
                slopes[cpu].append(slope)
        medians = [statistics.median(values) for values in slopes]
        arms.append(dict(arm=arm, per_thread_cycles_per_call=medians,
            repeat_slopes=slopes, cohort_cycles=max(medians), serial_cycles=sum(medians)))
    rng = random.Random(20261012)
    logs = paired['repeat_log_ratios']
    boot = sorted(100*(1-math.exp(statistics.mean(rng.choices(logs, k=7)))) for _ in range(5000))
    return dict(mode=mode, counter_scope=scope, samples_sha256=sha(path),
        wall_gain_percent=100*(1-paired['measured_ratio']),
        paired_repeat_bootstrap_interval_percent=[boot[124], boot[4874]],
        paired_repeat_log_ratios=logs, arms=arms,
        interval_scope='paired measurement uncertainty; seven repeat blocks; no new-algorithm prediction confidence')


def main(a):
    plan = load(a.payload/'plan.json')
    if sha(a.payload/'matched') != plan['binary_sha256']:
        raise ValueError('板端二进制身份不同。')
    traces = load(a.traces)
    if traces['status'] != 'complete' or traces['identities']['binary'] != plan['binary_sha256']:
        raise ValueError('轨迹批次未完成或二进制身份不同。')
    by_arm = {(r['id'], r['arm']): r for r in traces['records']}
    if len(by_arm) != 2*len(plan['cases']):
        raise ValueError('轨迹记录矩阵不同。')
    records = []
    for case in plan['cases']:
        modes = []
        dumps = []
        for mode in ('bench', 'bench-roi'):
            name = case['id'].removeprefix('conv-')+'-'+mode
            modes.append(evaluate(a.samples/(name+'.jsonl'), case['id'], mode))
            dumps.append(sha(a.samples/(name+'.bin')))
        predicted = []
        for arm in (0, 1):
            row = by_arm[case['id'], arm]
            dumps.append(row['dump_sha256'])
            cost = row['cost']
            center = next(s for s in cost['scenarios'] if s['name'] == 'central-warm')
            predicted.append(dict(arm=arm, model_sha256=cost['model_sha256'],
                cohort_cycles=center['cohort_cycles'], serial_cycles=center['serial_cycles'],
                coverage=cost['coverage']))
        if len(set(dumps)) != 1:
            raise ValueError('原生模式与模拟模式的完整转储不同。')
        records.append(dict(id=case['id'], dump_sha256=dumps[0], measurements=modes,
            component_predictions=predicted,
            component_gain_percent=100*(1-predicted[1]['cohort_cycles']/predicted[0]['cohort_cycles'])))
    write(a.output/'evaluation.json', dict(schema=3, records=records,
        binary_sha256=plan['binary_sha256'], traces_sha256=sha(a.traces),
        limits=['sync pause changes barrier arrival time and wall performance',
            'paused cycles retain caller loop and pause boundary instructions',
            'generic instruction counts do not establish user-only scope',
            'cohort and serial values are declared combinations, not actual time bounds',
            'no independent new-algorithm prediction interval'], automatic_action='none'))
    seal(a.output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--payload', type=Path, required=True)
    p.add_argument('--samples', type=Path, required=True)
    p.add_argument('--traces', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    main(a)
