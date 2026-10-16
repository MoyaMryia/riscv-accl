"""按预先固定的均衡指标选择默认配置。"""
import math
import statistics


def key(config):
    return f'm{config["mask"]}-t{config["threads"]}-u{config["ubatch"]}'


def choose(rows, configs, control):
    grouped = {}
    failed = set()
    for row in rows:
        name = key(row['config'])
        if row['status'] != 'pass':
            failed.add(name)
            continue
        shape = (row['model'], row['input_tokens'])
        grouped.setdefault((name, shape), []).append(row)
    reference = key(control)
    if reference in failed:
        raise ValueError('selection control failed')
    shapes = [('2B', 512), ('4B', 512), ('2B', 2048), ('4B', 2048)]
    rankings = []
    for config in configs:
        name = key(config)
        ratios = []
        details = []
        eligible = name not in failed
        for shape in shapes:
            a = grouped.get((reference, shape), [])
            b = grouped.get((name, shape), [])
            if not a:
                raise ValueError('selection control is incomplete')
            if not b:
                eligible = False
                continue
            for metric in ('ttft_ms', 'decode_ms'):
                av = [r[metric] for r in a]
                bv = [r[metric] for r in b]
                if any(not math.isfinite(v) or v <= 0 for v in av + bv):
                    raise ValueError('selection timing is invalid')
                am = statistics.mean(av)
                bm = statistics.mean(bv)
                ratio = bm / am
                spread = (max(av) - min(av)) / am * 100
                regression = (ratio - 1) * 100 > max(3, spread)
                eligible = eligible and not regression
                ratios.append(ratio)
                details.append(dict(model=shape[0], input_tokens=shape[1], metric=metric,
                    control_ms=av, candidate_ms=bv, ratio=ratio,
                    control_range_percent=spread, regression=regression))
        score = math.exp(statistics.mean(math.log(v) for v in ratios)) if ratios else None
        rankings.append(dict(config=config, eligible=eligible, score=score, metrics=details))
    valid = [r for r in rankings if r['eligible'] and len(r['metrics']) == 8]
    if not valid:
        raise ValueError('no complete admissible configuration')
    minimum = min(r['score'] for r in valid)
    tied = [r for r in valid if r['score'] <= minimum * 1.03]
    selected = min(tied, key=lambda r: (r['config']['mask'].bit_count(),
        int(r['config']['threads'] != 4) + int(r['config']['ubatch'] != 32),
        r['score'], key(r['config'])))
    return dict(selected=selected['config'], best_observed_score=minimum,
        selected_score=selected['score'], tie_factor=1.03, rankings=rankings)
