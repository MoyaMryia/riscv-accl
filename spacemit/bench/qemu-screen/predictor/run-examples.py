#!/usr/bin/env python3
"""核验便携包，并重放全部范例与独立检查结果。"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time
import importlib.util
from analyze import load, write, seal

HERE = Path(__file__).resolve().parent


def close(actual, expected):
    if not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError('重放数值与冻结检查记录不同。')


def check_prediction(prediction, validation, grouped=False):
    for key in ('model_sha256', 'calibration_sha256'):
        if prediction[key] != validation[key]:
            raise ValueError('重放身份与独立检查身份不同。')
    known = {r['group']: r for r in validation['records']}
    if len(known) != len(prediction['records']):
        raise ValueError('独立检查组数量不同。')
    covered_groups, covered_variants, total_variants, directions = 0, 0, 0, 0
    seen = set()
    for row in prediction['records']:
        group = row.get('group', row.get('id'))
        if group in seen or group not in known:
            raise ValueError('重放组重复或超出独立检查范围。')
        seen.add(group)
        old = known[group]
        pairs = [(row, old)]
        if grouped:
            variants = {v['unroll']: v for v in old['variants']}
            if sorted(variants) != sorted(v['unroll'] for v in row['variants']):
                raise ValueError('展开版本不同。')
            pairs = [(v, variants[v['unroll']]) for v in row['variants']]
        group_covered = True
        for current, measured in pairs:
            close(current['predicted_gain'], measured['predicted_gain'])
            for actual, expected in zip(current['gain_interval'], measured['gain_interval']):
                close(actual, expected)
            low, high = current['gain_interval']
            covered = low <= 1-measured['measured_ratio'] <= high
            if covered != measured['covered']:
                raise ValueError('区间覆盖重算结果不同。')
            group_covered &= covered
            covered_variants += covered
            total_variants += 1
            directions += (current['predicted_gain']>0)==(measured['measured_ratio']<1)
        covered_groups += group_covered
    expected = validation['observed_groups_covered' if grouped else 'observed_covered']
    if covered_groups != expected:
        raise ValueError('观测覆盖总数不同。')
    return dict(groups_covered=covered_groups, groups_total=len(known),
        variants_covered=covered_variants, variants_total=total_variants,
        point_direction_matches=directions,point_direction_total=total_variants,
        model_sha256=prediction['model_sha256'], nominal_coverage=.95,
        population_coverage_confirmed=False, automatic_action='none')


def main(output):
    spec = importlib.util.spec_from_file_location('verify_evidence', HERE/'verify-evidence.py')
    verify = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verify)
    integrity = verify.receipt(HERE/'SHA256SUMS', HERE)
    if integrity['failures']:
        raise ValueError('便携包完整性检查失败。')
    output.mkdir(parents=True, exist_ok=False)
    write(output/'integrity.json', integrity)
    start = time.perf_counter()
    for name, script in [('ime', 'demo.py'), ('conv', 'family-demo.py'),
                         ('schedule-v5', 'schedule-demo.py'), ('loops-v6', 'neighbor-demo.py')]:
        with (output/(name+'.log')).open('w') as log:
            subprocess.run([sys.executable, HERE/script, '--output', output/name],
                stdout=log, stderr=subprocess.STDOUT, check=True)
    ime_audit = (HERE/'examples/ime-mix-v7').exists()
    if ime_audit:
        with (output/'ime-mix-v7.log').open('w') as log:
            subprocess.run([sys.executable,HERE/'ime-mix-demo.py','--output',output/'ime-mix-v7'],
                stdout=log,stderr=subprocess.STDOUT,check=True)
    with (output/'memory.json').open('w') as log:
        subprocess.run([sys.executable, HERE/'memory-reference.py', '--mode', '3',
            '--threads', '4', '--span', '8388608'], stdout=log, check=True)
    checks, normalized = {}, {}
    for name, example, grouped in [('conv', 'conv-family-v3', False),
        ('schedule-v5', 'schedule-family-v5', False), ('loops-v6', 'aligned-loop-v6', True)]:
        prediction = load(output/name/'prediction.json')
        checks[name] = check_prediction(prediction,
            load(HERE/'examples'/example/'validation.json'), grouped)
        normalized[name] = dict(model_sha256=prediction['model_sha256'],
            calibration_sha256=prediction['calibration_sha256'], records=prediction['records'])
    if ime_audit:
        prediction=load(output/'ime-mix-v7/prediction.json')
        checks['ime-mix-v7']=check_prediction(prediction,load(HERE/'examples/ime-mix-v7/validation.json'),True)
        checks['ime-mix-v7']['point_model_use']='diagnostic only; broad intervals do not repair wrong directions'
        normalized['ime-mix-v7']=dict(model_sha256=prediction['model_sha256'],
            calibration_sha256=prediction['calibration_sha256'],records=prediction['records'])
    normalized['ime'] = dict(model_sha256=load(output/'ime/run.json')['model_sha256'],
        records=load(output/'ime/plan.json')['records'])
    normalized['memory'] = load(output/'memory.json')
    encoded = json.dumps(normalized, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    result = dict(schema=6, checks=checks, host_run_seconds=time.perf_counter()-start,
        portable_prediction_sha256=hashlib.sha256(encoded).hexdigest(), automatic_action='none',
        timing_scope='host replay only; not K1 performance', all_candidates_retained=True)
    write(output/'result.json', result)
    lines = ['# K1 模型便携重放', '', '已验证：包内文件完整性、冻结模型身份与独立检查数值重放。',
        '全部候选均保留。', '声明的 95% 覆盖依赖各自固定范围内配置组的可交换性。',
        '观测覆盖不能确认总体覆盖率。', '', '| 模型 | 独立观测覆盖 | 用途 |',
        '| --- | ---: | --- |']
    scopes = {'conv': '固定卷积算法对与形状范围', 'schedule-v5': '保留的组合斜率模型；存在覆盖缺口',
              'loops-v6': '固定对齐循环与三个展开版本'}
    scopes['ime-mix-v7']='固定 IME 混合循环；点预测方向错误，区间很宽'
    for name, check in checks.items():
        lines.append(f'| {name} | {check["groups_covered"]}/{check["groups_total"]} 组 | {scopes[name]} |')
    lines += ['', '分项周期范例用于成本诊断，不提供新算法的预测置信度。',
        '访存范例查询固定模式的有效载荷吞吐率，不外推算法耗时。',
        '主机重放时间不表示 K1 上的运行时间。']
    (output/'report.md').write_text('\n'.join(lines)+'\n')
    seal(output)
    print(output/'report.md')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    main(parser.parse_args().output.resolve())
