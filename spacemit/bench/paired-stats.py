#!/usr/bin/env python3
"""Compare two arms of small paired-launch benchmarks with a Welch interval.

Reads launch-level throughput values from the repository's three archived record
shapes: llama-bench JSONL (one launch per file, `avg_ts`), bench-server JSONL
(`model` launch field, `tps`), and lifecycle JSONL (`kind: measurement` labels,
server timing metrics). Prints per-launch values, arm means, the difference, and
a Welch 95% t-interval. Arms with a single launch get a point estimate only,
with a note that no run-to-run variance is estimable.
"""

import argparse
import json
import math
import re
import statistics
from pathlib import Path

# Two-sided 95% t critical values by degrees of freedom; below 30 floors to the
# conservative nearest listed value, above 30 to the normal approximation.
T_975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
         8: 2.306, 9: 2.262, 10: 2.228, 12: 2.179, 15: 2.131, 20: 2.086,
         25: 2.060, 30: 2.042}

LIFECYCLE_METRICS = {
    'prompt_per_second': lambda r: r['results'][0]['timings']['prompt_per_second'],
    'predicted_per_second': lambda r: r['results'][0]['timings']['predicted_per_second'],
    'ttft': lambda r: r['results'][0]['ttft_ms'] / 1000,
    'aggregate_tps': lambda r: r['aggregate_tps'],
}


def t_critical(df):
    keys = sorted(T_975)
    if df >= keys[-1]:
        return 1.960
    for key in keys:
        if df <= key:
            return T_975[key]
    raise AssertionError('unreachable')


def parse_select(argument):
    if not argument:
        return {}
    key, _, value = argument.partition('=')
    try:
        value = int(value)
    except ValueError:
        try:
            value = float(value)
        except ValueError:
            pass
    return {key: value}


def extract(path, metric, select):
    """Return {launch: [values]} from one archive file."""
    out = {}
    rows = [json.loads(line) for line in path.open(encoding='utf-8')]
    if not rows:
        raise SystemExit(f'{path}: no records')
    if 'avg_ts' in rows[0]:
        for row in rows:
            if all(row.get(key) == value for key, value in select.items()):
                out.setdefault(path.stem, []).append(row['avg_ts'])
        return out
    if any(row.get('kind') == 'measurement' for row in rows):
        if metric not in LIFECYCLE_METRICS:
            raise SystemExit(f'{path}: lifecycle metric must be one of {sorted(LIFECYCLE_METRICS)}')
        for row in rows:
            if row.get('kind') != 'measurement':
                continue
            if all(row.get(key) == value for key, value in select.items()):
                out.setdefault(row['label'], []).append(LIFECYCLE_METRICS[metric](row))
        return out
    for row in rows:
        if all(row.get(key) == value for key, value in select.items()):
            if metric != 'tps':
                raise SystemExit(f'{path}: bench-server records only support --metric tps')
            launch = row.get('model', path.stem)
            out.setdefault(launch, []).append(row['tps'])
    return out


def arm_values(paths, metric, select, label_regex):
    """Collapse launches to one mean value per launch."""
    values = []
    for path in paths:
        launches = extract(path, metric, select)
        for launch in sorted(launches):
            if label_regex and not re.search(label_regex, launch):
                continue
            values.append((launch, statistics.mean(launches[launch])))
    if not values:
        raise SystemExit('no records matched the selection')
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path, nargs='+')
    parser.add_argument('--candidate', type=Path, nargs='+', required=True)
    parser.add_argument('--metric', default='avg_ts',
                        help="avg_ts, tps, prompt_per_second, predicted_per_second, ttft, aggregate_tps")
    parser.add_argument('--select', action='append', default=[],
                        help='key=value filter, e.g. n_prompt=128 or prompt=english')
    parser.add_argument('--baseline-regex', default='',
                        help='keep only baseline launches whose label matches this regex')
    parser.add_argument('--candidate-regex', default='',
                        help='keep only candidate launches whose label matches this regex')
    parser.add_argument('--names', nargs=2, metavar=('BASE', 'CAND'), default=['baseline', 'candidate'])
    args = parser.parse_args()

    select = {}
    for item in args.select:
        select.update(parse_select(item))

    base = arm_values(args.baseline, args.metric, select, args.baseline_regex)
    cand = arm_values(args.candidate, args.metric, select, args.candidate_regex)

    print('| Arm | Launch | Value |')
    print('| --- | --- | ---: |')
    for name, arm in zip(args.names, (base, cand)):
        for launch, value in arm:
            print(f'| {name} | {launch} | {value:.4f} |')

    base_vals = [value for _, value in base]
    cand_vals = [value for _, value in cand]
    mean_b = statistics.mean(base_vals)
    mean_c = statistics.mean(cand_vals)
    diff = mean_c - mean_b
    rel = 100 * diff / mean_b
    print(f'\n{args.names[0]}: n={len(base_vals)} mean={mean_b:.4f}')
    print(f'{args.names[1]}: n={len(cand_vals)} mean={mean_c:.4f}')
    print(f'difference: {diff:+.4f} ({rel:+.2f}%)')

    if len(base_vals) < 2 or len(cand_vals) < 2:
        print('single launch in at least one arm: no run-to-run variance is estimable, '
              'so no interval is reported; treat the difference as a point estimate')
        return

    var_b = statistics.variance(base_vals)
    var_c = statistics.variance(cand_vals)
    se_sq = var_c / len(cand_vals) + var_b / len(base_vals)
    if se_sq == 0:
        print('both arms have zero launch variance: the interval collapses to the point estimate')
        return
    df = se_sq ** 2 / ((var_c / len(cand_vals)) ** 2 / (len(cand_vals) - 1)
                       + (var_b / len(base_vals)) ** 2 / (len(base_vals) - 1))
    half = t_critical(math.floor(df)) * math.sqrt(se_sq)
    print(f'Welch 95% interval for the difference: [{diff - half:.4f}, {diff + half:.4f}] '
          f'(df={df:.1f}); note: with n={len(base_vals)}/{len(cand_vals)} launches per arm '
          f'this interval has almost no power to detect small effects')


if __name__ == '__main__':
    main()
