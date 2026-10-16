#!/usr/bin/env python3
"""拟合固定算子的形状模型，并核验独立校准与后测。"""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
import statistics

import summarize


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def seal(value):
    return dict(value, sha256=digest(value))


def verify(value, kind):
    copy = dict(value)
    identity = copy.pop('sha256', None)
    if identity != digest(copy) or value['kind'] != kind:
        raise ValueError('identity or kind')
    return identity


def write_new(path, value):
    with Path(path).open('x') as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write('\n')


def check_plan(plan):
    groups = plan['groups']
    if len({g['id'] for g in groups}) != len(groups):
        raise ValueError('duplicate group')
    seen = set()
    for family in ('ime', 'conv'):
        counts = collections.Counter(g['split'] for g in groups if g['family'] == family)
        if counts != {'train': 8, 'calibration': 19, 'test': 9}:
            raise ValueError('split counts')
    for group in groups:
        key = (group['family'], tuple(group['shape']))
        if key in seen or group['threads'] != [1, 4]:
            raise ValueError('shape leakage or threads')
        seen.add(key)


def execution_identity(root):
    return {str(p.relative_to(root)): summarize.file_hash(p)
            for family in ('ime', 'conv')
            for p in sorted((root/family).rglob('*'))
            if p.is_file() and (p.name == 'operator' or 'lib' in p.relative_to(root/family).parts)}


def features(case, basis):
    if basis == 'constant':
        return [1.0]
    a, b = case['shape']
    result = [1.0, math.log(a), math.log(b)]
    if basis == 'log-shape-padding':
        result.append(float(case['padding'] != 0))
    return result


def solve(matrix, target):
    rows = [list(row)+[y] for row, y in zip(matrix, target)]
    n = len(target)
    for col in range(n):
        pivot = max(range(col, n), key=lambda j: abs(rows[j][col]))
        rows[col], rows[pivot] = rows[pivot], rows[col]
        if abs(rows[col][col]) < 1e-14:
            raise ValueError('singular fit')
        scale = rows[col][col]
        rows[col] = [v/scale for v in rows[col]]
        for j in range(n):
            if j != col:
                scale = rows[j][col]
                rows[j] = [a-scale*b for a, b in zip(rows[j], rows[col])]
    return [row[-1] for row in rows]


def regress(rows, target, basis, ridge):
    xs = [features(row['case'], basis) for row in rows]
    size = len(xs[0])
    means = [0.0]+[statistics.mean(x[j] for x in xs) for j in range(1, size)]
    scales = [1.0]+[max(1e-12, statistics.pstdev(x[j] for x in xs)) for j in range(1, size)]
    zs = [[(v-m)/s for v, m, s in zip(x, means, scales)] for x in xs]
    matrix = [[math.fsum(x[i]*x[j] for x in zs)+(ridge if i == j and i else 0)
               for j in range(size)] for i in range(size)]
    rhs = [math.fsum(x[j]*row[target] for x, row in zip(zs, rows)) for j in range(size)]
    return dict(coefficients=solve(matrix, rhs), means=means, scales=scales)


def log_predict(fit, case, basis):
    return math.fsum(c*(x-m)/s for c, x, m, s in zip(
        fit['coefficients'], features(case, basis), fit['means'], fit['scales']))


def fit_component(rows, basis, ridge):
    result = {}
    for threads in (1, 4):
        subset = [r for r in rows if r['case']['thread_count'] == threads]
        result[str(threads)] = {target: regress(subset, target, basis, ridge)
                                for target in ('baseline', 'ratio')}
    return dict(basis=basis, ridge=ridge, fits=result)


def component_predict(component, case):
    fits = component['fits'][str(case['thread_count'])]
    base = math.exp(log_predict(fits['baseline'], case, component['basis']))
    ratio = math.exp(log_predict(fits['ratio'], case, component['basis']))
    return dict(baseline_ms=base, candidate_ms=base*ratio, ratio=ratio)


def training_rows(summaries):
    cases = collections.defaultdict(list)
    for summary in summaries:
        if summary['status'] != 'verified' or summary.get('split', 'train') != 'train':
            raise ValueError('training split')
        for row in summary['results']:
            if row['case']['split'] != 'train':
                raise ValueError('training leakage')
            cases[row['case']['id']].append(row)
    result = []
    for values in cases.values():
        case = values[0]['case']
        if len(values) != len(summaries) or any(v['case'] != case for v in values):
            raise ValueError('batch case identity')
        arm = '1' if case['family'] == 'ime' else '2'
        baselines = [v['fits']['0']['median_slope_ms_per_call'] for v in values]
        candidates = [v['fits'][arm]['median_slope_ms_per_call'] for v in values]
        if any(v <= 0 or not math.isfinite(v) for v in baselines+candidates):
            raise ValueError('nonpositive slope; retain data and stop fit')
        result.append(dict(case=case, group=case['id'].rsplit('-t', 1)[0],
                           baseline=statistics.mean(math.log(v) for v in baselines),
                           ratio=statistics.mean(math.log(c/b) for b, c in zip(baselines, candidates))))
    return result


def errors(prediction, baseline, candidate):
    measured = dict(baseline_ms=baseline, candidate_ms=candidate, ratio=candidate/baseline)
    return {key: abs(math.log(prediction[key]/measured[key])) for key in measured}


def build_model(plan, summaries, identities):
    check_plan(plan)
    if any(identity != identities[0] for identity in identities):
        raise ValueError('training binary or library identity')
    rows = training_rows(summaries)
    expected = {f'{g["id"]}-t{t}': dict(g, id=f'{g["id"]}-t{t}', thread_count=t)
                for g in plan['groups'] if g['split'] == 'train' for t in g['threads']}
    if len(rows) != len(expected) or any(r['case'] != expected.get(r['case']['id']) for r in rows):
        raise ValueError('training plan identity')
    components = {}
    selection = {}
    for family in ('ime', 'conv'):
        subset = [r for r in rows if r['case']['family'] == family]
        groups = sorted({r['group'] for r in subset})
        if len(groups) != 8 or len(subset) != 16:
            raise ValueError('training group coverage')
        choices = []
        bases = ['constant', 'log-shape'] + (['log-shape-padding'] if family == 'conv' else [])
        for basis in bases:
            for ridge in (0.01, 0.1, 1.0, 10.0):
                scores = []
                for group in groups:
                    component = fit_component([r for r in subset if r['group'] != group], basis, ridge)
                    scores.append(max(max(errors(component_predict(component, r['case']),
                        math.exp(r['baseline']), math.exp(r['baseline']+r['ratio'])).values())
                        for r in subset if r['group'] == group))
                choices.append(dict(basis=basis, ridge=ridge, mean_group_max_log_error=statistics.mean(scores),
                                    group_scores=scores))
        best = min(choices, key=lambda r: r['mean_group_max_log_error'])
        components[family] = fit_component(subset, best['basis'], best['ridge'])
        selection[family] = dict(groups=groups, choices=choices, selected=best)
    return seal(dict(schema=1, kind='operator-shape-model', plan_sha256=digest(plan),
                     training_summaries_sha256=[digest(s) for s in summaries],
                     execution_identity=identities[0], components=components, selection=selection,
                     target='median execution-length slope in ms per call',
                     scope='fixed-binary hot-repeated-input', prediction_confidence=None))


def prediction(model, case):
    verify(model, 'operator-shape-model')
    if case['family'] not in ('ime', 'conv') or case['thread_count'] not in (1, 4):
        raise ValueError('unsupported family or thread count')
    if any(type(v) != int or v <= 0 for v in case['shape']) or len(case['shape']) != 2:
        raise ValueError('invalid shape')
    if case['padding'] not in (0, 3) or (case['family'] == 'ime' and case['padding']):
        raise ValueError('invalid padding')
    return component_predict(model['components'][case['family']], case)


def stage_rows(model, plan, summary, split):
    verify(model, 'operator-shape-model')
    check_plan(plan)
    if model['plan_sha256'] != digest(plan) or summary.get('split') != split:
        raise ValueError('plan or split identity')
    expected = {f'{g["id"]}-t{t}': dict(g, id=f'{g["id"]}-t{t}', thread_count=t)
                for g in plan['groups'] if g['split'] == split for t in g['threads']}
    if len(summary['results']) != len(expected):
        raise ValueError('stage coverage')
    result = []
    seen = set()
    for row in summary['results']:
        case = row['case']
        if case != expected.get(case['id']) or case['id'] in seen:
            raise ValueError('stage group identity')
        seen.add(case['id'])
        baseline = row['fits']['0']['median_slope_ms_per_call']
        arm = '1' if case['family'] == 'ime' else '2'
        candidate = row['fits'][arm]['median_slope_ms_per_call']
        if not all(math.isfinite(v) and v > 0 for v in (baseline, candidate)):
            raise ValueError('nonpositive target; retain data and stop evaluation')
        pred = prediction(model, case)
        result.append(dict(case=case, group=case['id'].rsplit('-t', 1)[0], predicted=pred,
                           measured=dict(baseline_ms=baseline, candidate_ms=candidate, ratio=candidate/baseline),
                           absolute_log_errors=errors(pred, baseline, candidate)))
    return result


def calibrate(model, plan, summary):
    rows = stage_rows(model, plan, summary, 'calibration')
    bounds = {}
    for family in ('ime', 'conv'):
        groups = collections.defaultdict(list)
        for row in rows:
            if row['case']['family'] == family:
                groups[row['group']].append(max(row['absolute_log_errors'].values()))
        scores = [dict(group=group, maximum_log_error=max(values)) for group, values in sorted(groups.items())]
        n = len(scores)
        rank = math.ceil((n+1)*0.95)
        if rank > n:
            raise ValueError('too few calibration groups')
        q = sorted(r['maximum_log_error'] for r in scores)[rank-1]
        bounds[family] = dict(groups=scores, quantile_rank=rank, maximum_log_error=q, factor=math.exp(q))
    return seal(dict(schema=1, kind='operator-shape-calibration', model_sha256=model['sha256'],
                     plan_sha256=digest(plan), summary_sha256=digest(summary), coverage=0.95, bounds=bounds,
                     assumption='exchangeable configuration groups within each fixed family and scope',
                     coverage_scope='joint baseline, candidate and ratio targets across both thread counts; per family',
                     rows=rows))


def verify_calibration(calibration, model, plan):
    verify(calibration, 'operator-shape-calibration')
    if calibration['model_sha256'] != verify(model, 'operator-shape-model') or calibration['plan_sha256'] != digest(plan):
        raise ValueError('calibration identity')
    expected = {g['id'] for g in plan['groups'] if g['split'] == 'calibration'}
    actual = {g['group'] for b in calibration['bounds'].values() for g in b['groups']}
    if actual != expected:
        raise ValueError('calibration groups')
    for bound in calibration['bounds'].values():
        if len(bound['groups']) != 19 or bound['quantile_rank'] != 19:
            raise ValueError('calibration rank')
        q = max(g['maximum_log_error'] for g in bound['groups'])
        if bound['maximum_log_error'] != q or bound['factor'] != math.exp(q):
            raise ValueError('calibration bound')


def in_domain(case):
    if case['family'] == 'ime':
        a = [96, 160, 224, 320, 480, 768, 1152, 1792, 2304, 3584, 4608]
        b = [16, 32, 48, 64, 96, 128]
    else:
        a = [160, 320, 640, 896, 1280, 1792, 2560, 3584, 4608, 5632, 6656, 9216]
        b = [2, 5, 7, 11, 17, 23, 40, 56]
    return case['shape'][0] in a and case['shape'][1] in b


def query(model, plan, calibration, cases):
    verify_calibration(calibration, model, plan)
    measured = {(g['family'], tuple(g['shape'])) for g in plan['groups'] if g['split'] != 'test'}
    result = []
    for case in cases:
        pred = prediction(model, case)
        independent = (case['family'], tuple(case['shape'])) not in measured
        row = dict(case=case, predicted=pred, predicted_saved_ms=pred['baseline_ms']-pred['candidate_ms'],
                   scope='fixed-binary hot-repeated-input', independent_of_fit_and_calibration=independent,
                   in_declared_grid=in_domain(case), candidate_elimination=False)
        if independent and in_domain(case):
            factor = calibration['bounds'][case['family']]['factor']
            row['ratio_interval'] = [pred['ratio']/factor, pred['ratio']*factor]
            row['coverage_status'] = 'conditional 95% per-family group coverage; exchangeability unverified'
        else:
            row['ratio_interval'] = None
            row['coverage_status'] = 'unavailable for observed groups or shapes outside the declared grid'
        result.append(row)
    return sorted(result, key=lambda r: r['predicted_saved_ms'], reverse=True)


def evaluate(model, plan, summary, calibration):
    verify_calibration(calibration, model, plan)
    rows = stage_rows(model, plan, summary, 'test')
    groups = collections.defaultdict(list)
    for row in rows:
        bound = calibration['bounds'][row['case']['family']]
        row['covered'] = max(row['absolute_log_errors'].values()) <= bound['maximum_log_error']+1e-12
        row['direction_agrees'] = (row['predicted']['ratio'] < 1) == (row['measured']['ratio'] < 1)
        row['intervals'] = {key: [value/bound['factor'], value*bound['factor']] for key, value in row['predicted'].items()}
        row['predicted_saved_ms'] = row['predicted']['baseline_ms']-row['predicted']['candidate_ms']
        row['gain_percent_interval'] = [100*(1-row['intervals']['ratio'][1]), 100*(1-row['intervals']['ratio'][0])]
        groups[row['group']].append(row)
    counts = {}
    for family in ('ime', 'conv'):
        subset = [row for row in rows if row['case']['family'] == family]
        counts[family] = dict(groups=9, groups_covered=sum(all(r['covered'] for r in g) for g in groups.values() if g[0]['case']['family'] == family),
                              configurations=len(subset), configurations_covered=sum(r['covered'] for r in subset),
                              direction_agreement=sum(r['direction_agrees'] for r in subset),
                              median_ratio_factor_error=math.exp(statistics.median(r['absolute_log_errors']['ratio'] for r in subset)),
                              maximum_ratio_factor_error=math.exp(max(r['absolute_log_errors']['ratio'] for r in subset)))
    return seal(dict(schema=1, kind='operator-shape-evaluation', model_sha256=model['sha256'],
                     calibration_sha256=calibration['sha256'], summary_sha256=digest(summary), counts=counts,
                     candidate_elimination=False, rows=sorted(rows, key=lambda r: r['predicted_saved_ms'], reverse=True)))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='action', required=True)
    fit = sub.add_parser('fit')
    fit.add_argument('--plan', type=Path, required=True)
    fit.add_argument('--batch', type=Path, action='append', required=True)
    fit.add_argument('--output', type=Path, required=True)
    for action in ('calibrate', 'evaluate'):
        a = sub.add_parser(action)
        a.add_argument('--plan', type=Path, required=True)
        a.add_argument('--model', type=Path, required=True)
        a.add_argument('--batch', type=Path, required=True)
        a.add_argument('--output', type=Path, required=True)
        if action == 'evaluate':
            a.add_argument('--calibration', type=Path, required=True)
    a = sub.add_parser('predict')
    for name in ('plan', 'model', 'calibration', 'cases', 'output'):
        a.add_argument('--'+name, type=Path, required=True)
    args = p.parse_args()
    plan = json.loads(args.plan.read_text())
    if args.action == 'fit':
        summaries = [summarize.summarize(b) for b in args.batch]
        result = build_model(plan, summaries, [execution_identity(b) for b in args.batch])
    elif args.action == 'predict':
        model = json.loads(args.model.read_text())
        result = seal(dict(kind='operator-shape-predictions', rows=query(model, plan,
            json.loads(args.calibration.read_text()), json.loads(args.cases.read_text()))))
    else:
        model = json.loads(args.model.read_text())
        if model['execution_identity'] != execution_identity(args.batch):
            raise ValueError('evaluation binary or library identity')
        summary = summarize.summarize(args.batch)
        result = calibrate(model, plan, summary) if args.action == 'calibrate' else evaluate(
            model, plan, summary, json.loads(args.calibration.read_text()))
    write_new(args.output, result)
    print(json.dumps({'sha256': result['sha256'], 'kind': result['kind'], 'counts': result.get('counts')}))


if __name__ == '__main__':
    main()
