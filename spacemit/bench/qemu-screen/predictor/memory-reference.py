#!/usr/bin/env python3
"""查询固定访存模式的 K1 实测参考，不外推算法耗时。"""
import argparse
import json
from pathlib import Path
from analyze import load, sha

HERE = Path(__file__).resolve().parent


def select(profile, mode, threads, span):
    matches = [r for r in profile['records'] if
        (r['mode'], r['threads'], r['span_bytes_per_buffer']) == (mode, threads, span)]
    if len(matches) != 1:
        raise ValueError('必须选择已测的唯一访存配置。')
    return dict(record=matches[0], samples_sha256=profile['samples_sha256'],
        plan_sha256=profile['plan_sha256'], frequency_snapshots_khz=profile['frequency_snapshots_khz'],
        limits=profile['limits'], algorithm_time_estimate=None,
        scope='measured payload throughput for one fixed pattern; no interpolation or algorithm confidence')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile', type=Path, default=HERE/'profiles/k1-memory-20261012/memory-profile.json')
    p.add_argument('--mode', type=int, required=True)
    p.add_argument('--threads', type=int, required=True)
    p.add_argument('--span', type=int, required=True)
    a = p.parse_args()
    result = select(load(a.profile), a.mode, a.threads, a.span)
    result['profile_sha256'] = sha(a.profile)
    print(json.dumps(result, ensure_ascii=False, indent=2))
