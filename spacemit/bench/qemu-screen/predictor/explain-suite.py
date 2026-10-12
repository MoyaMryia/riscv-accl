#!/usr/bin/env python3
"""用完整实际程序核对等待诊断的默认场景。"""
import argparse
import importlib.util
from pathlib import Path
import math
import time
from analyze import load, write, sha, seal

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('suite_explain', HERE/'explain-cost.py')
explain = importlib.util.module_from_spec(spec)
spec.loader.exec_module(explain)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('--profiles', type=Path, nargs='+', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    inputs = load(a.source/'results.json')
    if inputs['status'] != 'complete':
        raise ValueError('源轨迹批次未完成。')
    records = []
    start = time.perf_counter()
    for row in inputs['records']:
        name = row['id']+f'-arm{row["arm"]}'
        result = explain.explain(a.source/name/'program', a.profiles)
        if result['base_model_sha256'] != row['cost']['model_sha256']:
            raise ValueError('默认成本模型身份不同。')
        center = next(r for r in row['cost']['scenarios'] if r['name'] == 'central-warm')
        baseline = result['records'][0]
        for key in ('cohort_cycles', 'serial_cycles'):
            if not math.isclose(center[key], baseline[key], rel_tol=1e-12, abs_tol=1e-7):
                raise ValueError('默认诊断周期与冻结成本重放不同。')
        for name_thread, thread in baseline['threads'].items():
            expected = center['threads'][name_thread]['estimated_component_cycles']
            if not math.isclose(thread['estimated_component_cycles'], expected, rel_tol=1e-12, abs_tol=1e-7):
                raise ValueError('默认分线程周期不同。')
        target = a.output/name
        target.mkdir()
        write(target/'explanation.json', result)
        records.append(dict(id=row['id'], arm=row['arm'], binary_sha256=row['binary_sha256'],
            default_equal=True, explanation=result))
        write(a.output/'results.json', dict(schema=4, status='running', records=records))
    write(a.output/'results.json', dict(schema=4, status='complete', records=records,
        source_sha256=sha(a.source/'results.json'), elapsed_seconds=time.perf_counter()-start,
        scope='declared wait attribution and constraint sensitivity; no measured stall or confidence claim'))
    seal(a.output)
