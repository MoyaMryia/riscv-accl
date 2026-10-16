#!/usr/bin/env python3
"""核验便携片段比较范例，并保留历史漏报。"""
import argparse
import importlib.util
from pathlib import Path
import time
from common import digest, read, write


def replay(root):
    started = time.perf_counter()
    root = Path(root).resolve()
    receipt_count = 0
    for line in (root / 'SHA256SUMS').read_text().splitlines():
        expected, name = line.split('  ', 1)
        path = (root / name).resolve()
        if not path.is_relative_to(root) or digest(path) != expected:
            raise ValueError('便携片段包的文件身份不同。')
        receipt_count += 1
    spec = importlib.util.spec_from_file_location('portable_fragment_compare', root / 'fragment-compare.py')
    fragment = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fragment)
    oracle = {row['id']: row for row in read(root / 'historical-oracle.json')['records']}
    rows = []
    for record in read(root / 'expected-comparisons.json'):
        result = fragment.evaluate(root / 'manifests' / (record['id'] + '.json'))
        if result['comparison_sha256'] != record['comparison_sha256']:
            raise ValueError('便携片段比较结果不同。')
        if result['status'] != 'exploratory-pair-estimate' or result['prediction_confidence'] is not None:
            raise ValueError('片段范围或置信声明不同。')
        observed = oracle[record['id']]['historical_native_ratio']
        primary = result['primary_prediction']['candidate_over_baseline']
        if not result['retained'] or result['automatic_performance_rejection'] or result['automatic_full_test']:
            raise ValueError('候选保留规则不同。')
        rows.append(dict(id=record['id'], comparison_sha256=result['comparison_sha256'],
                         predicted_ratio=primary, historical_native_ratio=observed,
                         historical_gain_missed=primary >= 1 and observed < 1,
                         recommendation=result['recommendation'], retained=True))
    return dict(status='passed', receipt_entries=receipt_count, rows=rows,
                historical_misses_retained=sum(row['historical_gain_missed'] for row in rows),
                elapsed_seconds=time.perf_counter() - started, independent_accuracy_validation=False,
                limits=['本检查验证工具接入与历史失败保留。', '历史数据不能证明新片段的预测精度。',
                        '本次耗时不包含原始构建、轨迹采集与原生测量。'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    write(args.output, replay(args.root))
