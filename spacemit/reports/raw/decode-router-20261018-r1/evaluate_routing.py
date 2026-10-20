#!/usr/bin/env python3
"""测量分类开销，并回放既有配对时间。"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import resource
import statistics
import time

import classifier
import policy
import train

POLICIES = {'two': ('direct', 'prefix'), 'three': policy.ROUTES}


def read_replay(measurements, requests):
    summary = json.loads(Path(measurements).read_text())['cases']
    cases = json.loads(Path(requests).read_text())
    if not isinstance(summary, dict) or not summary or not isinstance(cases, list):
        raise ValueError('配对时间或请求格式无效')
    if any(not isinstance(case, dict) or not isinstance(case.get('case_id'), str) or not case['case_id'] for case in cases):
        raise ValueError('配对任务标识无效')
    ids = [case['case_id'] for case in cases]
    if len(set(ids)) != len(ids) or set(ids) != set(summary):
        raise ValueError('配对任务标识不同或重复')
    result = []
    for case in cases:
        measured = summary[case['case_id']]
        if not isinstance(measured, dict) or not isinstance(measured.get('variants'), dict):
            raise ValueError('配对实验臂格式无效')
        variants = measured['variants']
        if set(variants) != set(policy.ROUTES) or any(not isinstance(v, dict) for v in variants.values()):
            raise ValueError('配对数据必须包含三个解码路径')
        times = {name: variants[name].get('wall_s') for name in policy.ROUTES}
        if any(type(value) not in (int, float) or not math.isfinite(value) or value <= 0 for value in times.values()):
            raise ValueError('配对时间必须为有限正数')
        result.append({'case_id': case['case_id'], 'text': policy.request_text(case), 'times': times})
    return result


def replay(model, rows):
    direct = sum(row['times']['direct'] for row in rows)
    result = {'direct_sum_s': direct, 'requests': len(rows), 'policies': {}}
    selections = {name: [] for name in POLICIES}
    for row in rows:
        start = time.perf_counter_ns()
        prediction = classifier.predict(model, row['text'])
        prediction_ns = time.perf_counter_ns() - start
        for name, routes in POLICIES.items():
            start = time.perf_counter_ns()
            decision = policy.choose(model, prediction, routes)
            decision_ns = prediction_ns + time.perf_counter_ns() - start
            guarded = policy.choose(model, prediction, routes, score_guard=True)
            selections[name].append({'case_id': row['case_id'], **decision,
                'category': prediction['category'], 'score': prediction['score'],
                'decision_ns': decision_ns, 'measured_wall_s': row['times'][decision['route']],
                'guarded_route': guarded['route'], 'guarded_measured_wall_s': row['times'][guarded['route']]})
    for name, routes in POLICIES.items():
        selected = selections[name]
        oracle = sum(min(row['times'][route] for route in routes) for row in rows)
        measured = sum(row['measured_wall_s'] for row in selected)
        overhead = sum(row['decision_ns'] for row in selected) / 1e9
        result['policies'][name] = {'oracle_sum_s': oracle, 'selected_sum_s': measured,
            'guarded_selected_sum_s': sum(row['guarded_measured_wall_s'] for row in selected),
            'decision_sum_s': overhead, 'estimated_sum_s': measured + overhead,
            'estimated_reduction_pct': 100 * (1 - (measured + overhead) / direct),
            'selections': selected}
    return result


def benchmark(model, rows, repeats):
    samples = []
    for repeat in range(repeats):
        for row in rows:
            start = time.perf_counter_ns()
            prediction = classifier.predict(model, row['text'])
            after_prediction = time.perf_counter_ns()
            decision = policy.choose(model, prediction, POLICIES['two'])
            end = time.perf_counter_ns()
            samples.append({'id': row['id'], 'repeat': repeat,
                'prediction_ns': after_prediction - start, 'decision_ns': end - start,
                'route': decision['route']})
    values = sorted(sample['decision_ns'] / 1e6 for sample in samples)
    return {'unique_requests': len(rows), 'repeats': repeats, 'calls': len(samples),
        'decision_ms': {'min': values[0], 'median': statistics.median(values),
                        'p95': values[math.ceil(.95 * len(values)) - 1], 'max': values[-1]},
        'samples': samples}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('model', 'tasks', 'measurements', 'requests', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--repeats', type=int, default=40)
    args = parser.parse_args(argv)
    if not 0 < args.repeats <= 1000:
        parser.error('重复数必须在 1 至 1000 之间')
    model = classifier.load_model(args.model)
    tasks = train.read_tasks(args.tasks)
    test = [row for row in tasks if row['split'] == 'test']
    paired = read_replay(args.measurements, args.requests)
    args.output.mkdir(parents=True, exist_ok=False)
    timing_rows = test + [{'id': 'paired-' + row['case_id'], 'text': row['text']} for row in paired]
    result = {'hardware': list(platform.uname()), 'model_bytes': args.model.stat().st_size, 'score_guard': False,
              'identities': {}, 'classification': train.evaluate(model, test),
              'benchmark': benchmark(model, timing_rows, args.repeats), 'replay': replay(model, paired),
              'process_hwm_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    for name, path in {'model': args.model, 'tasks': args.tasks, 'measurements': args.measurements,
                       'requests': args.requests, 'evaluator': Path(__file__),
                       'classifier': Path(classifier.__file__), 'policy': Path(policy.__file__),
                       'training_entry': Path(train.__file__)}.items():
        result['identities'][name] = {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    (args.output / 'evaluation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key not in ('benchmark', 'replay')},
                     ensure_ascii=False), flush=True)
    print('DECISION_MS', json.dumps(result['benchmark']['decision_ms']), flush=True)
    print('REPLAY', json.dumps(result['replay'], ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
