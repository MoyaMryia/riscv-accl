#!/usr/bin/env python3
"""复算成果总账中的数字。任一数字与原始记录不一致时失败。

用法：python3 tools/verify_results_ledger.py [--ledger PATH] [--markdown PATH]
退出码 0 表示全部数字一致；1 表示存在差异；2 表示输入缺失或结构错误。
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = ROOT / 'spacemit/reports/results-ledger.json'
DEFAULT_MARKDOWN = ROOT / 'spacemit/reports/RESULTS-LEDGER.md'


class Mismatch(ValueError):
    pass


def close(actual, claimed, tolerance, label):
    if abs(actual - claimed) > tolerance:
        raise Mismatch('{}: computed {!r}, ledger {!r}, tolerance {}'.format(
            label, actual, claimed, tolerance))


def read_json(path):
    if not path.exists():
        raise FileNotFoundError('missing record: ' + str(path))
    return json.loads(path.read_text(encoding='utf-8'))


def check_final_delivery(root, block, tolerance):
    report = root / block['report']
    if not report.exists():
        raise FileNotFoundError('missing report: ' + str(report))
    text = report.read_text(encoding='utf-8')
    for row in block['rows']:
        ratio = row['wall_baseline_s'] / row['wall_final_s']
        close(ratio, row['speedup'], tolerance['speedup'],
              'final/{}@{}'.format(row['model'], row['prompt_tokens']))
        for field in ('wall_baseline_s', 'wall_final_s'):
            needle = '{:.3f}'.format(row[field])
            if needle not in text:
                raise Mismatch('final/{}@{}: {} {} absent from report'.format(
                    row['model'], row['prompt_tokens'], field, needle))
    return len(block['rows'])


def check_mtp(root, block, tolerance):
    summary = read_json(root / block['raw'])
    model = summary['models'][block['model']]
    claims = block['claims']
    direct = model['direct']['wall_mean_s']
    pure = model['mtp']['wall_mean_s']
    fallback = model['mtp_lowacc']['wall_mean_s']
    close(direct, claims['direct_mean_s'], tolerance['seconds'], 'mtp/direct')
    close(pure, claims['pure_mean_s'], tolerance['seconds'], 'mtp/pure')
    close(fallback, claims['fallback_mean_s'], tolerance['seconds'], 'mtp/fallback')
    rows = [item for item in summary['records'] if item.get('model') == block['model']]
    pairs = {}
    for item in rows:
        pairs.setdefault(item['round'], {})[item.get('variant') or item.get('arm')] = item['response']['wall_s']
    changes = [100 * (1 - arms['mtp'] / arms['direct']) for arms in pairs.values()
               if {'direct', 'mtp'} <= set(arms)]
    if not changes:
        raise Mismatch('mtp: no complete pair')
    close(sum(changes) / len(changes), claims['paired_reduction_pct'], tolerance['percent'],
          'mtp/paired_reduction')
    if len(changes) != claims['repeats']:
        raise Mismatch('mtp: paired repeat count differs: {}'.format(len(changes)))
    for arm in ('direct', 'mtp', 'mtp_lowacc'):
        checks = model[arm]['quality_checks']
        if model[arm]['repeats'] != claims['repeats'] or len(checks) != claims['repeats']:
            raise Mismatch('mtp/{}: repeat count differs'.format(arm))
        for item in checks:
            if item['passed'] is not True or item['result']['checks'] != claims['quality_checks']:
                raise Mismatch('mtp/{}: quality record differs'.format(arm))
    return 6


def paired_means(records, candidate, categories):
    """按题目配对计算候选相对直接的墙钟变化均值。"""
    pairs = {}
    for item in records:
        arm = item.get('variant') or item.get('arm')
        key = (item['category'], item['case_id'], item.get('round', 1))
        pairs.setdefault(key, {})[arm] = item['response']['wall_s']
    grouped = {category: [] for category in categories}
    for (category, _case, _round), arms in pairs.items():
        if {'direct', candidate} <= set(arms):
            grouped[category].append(100 * (arms[candidate] / arms['direct'] - 1))
    if any(not values for values in grouped.values()):
        raise Mismatch('general: a category has no complete pair')
    return {category: sum(values) / len(values) for category, values in grouped.items()}


def check_general(root, block, tolerance):
    summary = read_json(root / block['raw'])
    computed = paired_means(summary['records'], 'mtp', list(block['claims']))
    for category, claimed in block['claims'].items():
        close(computed[category], claimed, tolerance['percent'], 'general/' + category)
    return len(block['claims'])


def check_full_head(root, block, tolerance):
    summary = read_json(root / block['raw'])
    variants = summary['cases'][block['case_id']]['variants']
    claims = block['claims']
    close(variants['direct']['wall_s'], claims['direct_s'], tolerance['seconds'], 'full/direct')
    close(variants['prefix']['wall_s'], claims['prefix_s'], tolerance['seconds'], 'full/prefix')
    close(variants['full']['wall_s'], claims['full_s'], tolerance['seconds'], 'full/full')
    close(100 * (variants['prefix']['wall_s'] / variants['direct']['wall_s'] - 1),
          claims['prefix_change_pct'], tolerance['percent'], 'full/prefix_change')
    close(100 * (variants['full']['wall_s'] / variants['prefix']['wall_s'] - 1),
          claims['full_vs_prefix_pct'], tolerance['percent'], 'full/vs_prefix')
    return 5


def check_router(root, block, tolerance):
    summary = read_json(root / block['raw'])
    claims = block['claims']
    close(summary['baseline_total_s'], claims['baseline_total_s'], tolerance['seconds'], 'router/baseline')
    close(summary['routed_total_s'], claims['routed_total_s'], tolerance['seconds'], 'router/routed')
    close(-summary['wall_reduction_pct'], claims['wall_change_pct'], tolerance['percent'],
          'router/wall_change')
    if summary['routes'].get('prefix') != claims['prefix_routes']:
        raise Mismatch('router/prefix routes: {}'.format(summary['routes']))
    if summary['routes'].get('direct') != claims['direct_routes']:
        raise Mismatch('router/direct routes: {}'.format(summary['routes']))
    return 5


def check_bert(root, block, tolerance):
    training = read_json(root / block['raw'])
    metrics = training['metrics']
    claims = block['claims']
    if training['best_epoch'] != claims['best_epoch']:
        raise Mismatch('bert/best_epoch: {}'.format(training['best_epoch']))
    close(100 * metrics['best_dev']['accuracy'], claims['dev_accuracy_pct'], tolerance['percent'],
          'bert/dev')
    close(100 * metrics['test']['accuracy'], claims['test_accuracy_pct'], tolerance['percent'],
          'bert/test')
    close(100 * metrics['regression']['accuracy'], claims['regression_accuracy_pct'],
          tolerance['percent'], 'bert/regression')
    close(100 * metrics['baseline_ngram']['test']['accuracy'], claims['ngram_test_accuracy_pct'],
          tolerance['percent'], 'bert/ngram_test')
    return 4


CHECKS = {'mtp_r3': check_mtp, 'general_suite': check_general, 'full_head': check_full_head,
          'router_e2e': check_router, 'bert_classifier': check_bert}


def verify(ledger_path=DEFAULT_LEDGER, markdown_path=DEFAULT_MARKDOWN):
    ledger = json.loads(Path(ledger_path).read_text(encoding='utf-8'))
    tolerance = ledger['tolerance']
    markdown = Path(markdown_path)
    if not markdown.exists():
        raise FileNotFoundError('missing ledger document: ' + str(markdown))
    text = markdown.read_text(encoding='utf-8')
    checked = check_final_delivery(ROOT, ledger['final_delivery'], tolerance)
    for name, block in ledger['recomputed'].items():
        checked += CHECKS[name](ROOT, block, tolerance)
    for needle in ledger['markdown_checks']:
        if needle not in text:
            raise Mismatch('ledger document lacks: ' + needle)
    return checked


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger', type=Path, default=DEFAULT_LEDGER)
    parser.add_argument('--markdown', type=Path, default=DEFAULT_MARKDOWN)
    args = parser.parse_args(argv)
    try:
        count = verify(args.ledger, args.markdown)
    except (Mismatch, FileNotFoundError, KeyError, json.JSONDecodeError) as error:
        print('LEDGER_MISMATCH ' + str(error), file=sys.stderr)
        return 1
    print('LEDGER_OK {}'.format(count))
    return 0


if __name__ == '__main__':
    sys.exit(main())
