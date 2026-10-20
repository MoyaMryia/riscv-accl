#!/usr/bin/env python3
"""从已完成记录计算 MTP 路由的逐请求、逐家族与逐类别 oracle。只读。"""
import argparse
from collections import defaultdict
import json
import random
from pathlib import Path
import statistics

ARMS = ('direct', 'prefix', 'lowacc')


def summary_rows(path, candidate):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    rows = []
    for item in data['records']:
        arm = item.get('variant') or item.get('arm')
        if arm == candidate:
            arm = 'prefix'
        wall = item['response']['wall_s']
        if isinstance(wall, bool) or not isinstance(wall, (int, float)) or wall <= 0:
            raise ValueError('wall time is invalid: ' + item.get('case_id', '?'))
        rows.append({'case_id': item['case_id'], 'round': item.get('round', 1), 'arm': arm,
                     'category': item['category'], 'wall_s': wall, 'family': None})
    return rows


def batch_rows(path):
    import analyze_discovery
    paired, _counts = analyze_discovery.load_attempts(Path(path))
    rows = []
    for (case_id, repeat), arms in paired.items():
        for arm, record in arms.items():
            rows.append({'case_id': case_id, 'round': repeat, 'arm': arm,
                         'category': record['category'], 'wall_s': record['response']['wall_s'],
                         'family': None})
    return rows


def attach_families(rows, cases_path):
    cases = {case['case_id']: case for case in json.loads(Path(cases_path).read_text(encoding='utf-8'))}
    for row in rows:
        case = cases.get(row['case_id'])
        metadata = (case or {}).get('metadata') or {}
        row['family'] = metadata.get('family') or row['case_id']


def pairs(rows):
    indexed = {}
    for row in rows:
        indexed.setdefault((row['case_id'], row['round']), {})[row['arm']] = row
    result = []
    for key, arms in indexed.items():
        if 'direct' not in arms or 'prefix' not in arms:
            continue
        result.append((arms['direct'], arms['prefix']))
    return sorted(result, key=lambda item: (item[0]['case_id'], item[0]['round']))


def gain(selected):
    direct = sum(d['wall_s'] for d, _ in selected)
    chosen = sum(min(d['wall_s'], m['wall_s']) for d, m in selected)
    return 100 * (1 - chosen / direct)


def grouped(selected, key):
    groups = defaultdict(list)
    for direct, mtp in selected:
        groups[key(direct)].append((direct, mtp))
    return groups


def group_gain(items):
    direct = sum(d['wall_s'] for d, _ in items)
    best = min(sum(d['wall_s'] for d, _ in items), sum(m['wall_s'] for _, m in items))
    return 100 * (1 - best / direct)


def bootstrap(selected, clusters, rounds, seed):
    """按任务家族聚类重采样，返回总净收益的 95% 区间。"""
    by_name = defaultdict(list)
    for direct, mtp in selected:
        by_name[clusters[(direct['case_id'], direct['round'])]].append((direct, mtp))
    names = sorted(by_name)
    if len(names) < 2:
        return None
    rng = random.Random(seed)
    values = []
    for _ in range(rounds):
        sample = []
        for _ in names:
            sample.extend(by_name[rng.choice(names)])
        values.append(gain(sample))
    values.sort()
    return [values[int(0.025 * (rounds - 1))], values[int(0.975 * (rounds - 1))]]


def summarize(selected, min_family_pct, rounds, seed):
    if not selected:
        raise ValueError('no complete direct/MTP pair')
    clusters = {(d['case_id'], d['round']): d['family'] or d['case_id'] for d, _ in selected}
    families = {}
    for name, items in grouped(selected, lambda row: row['family'] or row['case_id']).items():
        families[name] = {'pairs': len(items), 'oracle_gain_pct': group_gain(items),
                          'enabled': group_gain(items) >= min_family_pct}
    narrow = [item for item in selected
              if families[(item[0]['family'] or item[0]['case_id'])]['enabled']]
    categories = {}
    for name, items in grouped(selected, lambda row: row['category']).items():
        categories[name] = {'pairs': len(items), 'oracle_gain_pct': group_gain(items)}
    enabled = sorted(name for name, item in families.items() if item['enabled'])
    return {'pairs': len(selected),
            'per_request_oracle_pct': gain(selected),
            'bootstrap_95': bootstrap(selected, clusters, rounds, seed),
            'categories': categories,
            'families': families,
            'narrow_families': enabled,
            'narrow_gain_pct': gain(narrow) if narrow else 0.0,
            'narrow_pairs': len(narrow)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--summary', type=Path)
    source.add_argument('--batch', type=Path)
    parser.add_argument('--candidate', default='mtp')
    parser.add_argument('--cases', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--min-family-pct', type=float, default=3.0)
    parser.add_argument('--rounds', type=int, default=10000)
    parser.add_argument('--seed', type=int, default=20261020)
    args = parser.parse_args(argv)
    rows = summary_rows(args.summary, args.candidate) if args.summary else batch_rows(args.batch)
    if args.cases:
        attach_families(rows, args.cases)
    selected = pairs(rows)
    result = summarize(selected, args.min_family_pct, args.rounds, args.seed)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'oracle.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in
                      ('pairs', 'per_request_oracle_pct', 'bootstrap_95',
                       'narrow_gain_pct', 'narrow_pairs')}, ensure_ascii=False))
    print(json.dumps(result['narrow_families'], ensure_ascii=False))


if __name__ == '__main__':
    main()
