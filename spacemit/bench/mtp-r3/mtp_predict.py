#!/usr/bin/env python3
"""构建 MTP 收益数据集，并用分组交叉验证评估预测器。只读记录。"""
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import random
import re
import statistics

FEATURES = ('prompt_tokens', 'chars', 'cjk_ratio', 'lines', 'code_fence', 'code_words',
            'question_marks', 'digits', 'ascii_words',
            'doc_none', 'doc_zh', 'doc_en', 'fam_stable_unique', 'fam_window_sums',
            'fam_transpose_rect', 'fam_interval_union', 'fam_unicode_runs')
DOC_NONE = re.compile('不要写注释或文档字符串|Do not write comments or docstrings', re.IGNORECASE)
DOC_ZH = re.compile('中文文档字符串|Chinese docstring', re.IGNORECASE)
DOC_EN = re.compile('英文文档字符串|English docstring', re.IGNORECASE)
FAMILIES = ('stable_unique', 'window_sums', 'transpose_rect', 'interval_union', 'unicode_runs')
CJK = re.compile(r'[\u4e00-\u9fff]')
CODE_WORDS = re.compile(r'\b(def|return|for|while|if|list|dict|int|str)\b')


def case_text(case):
    return '\n'.join(message['content'] for message in case['messages'])


def features(case, prompt_tokens):
    text = case_text(case)
    chars = len(text)
    cjk = len(CJK.findall(text))
    return {'prompt_tokens': prompt_tokens, 'chars': chars,
            'cjk_ratio': cjk / chars if chars else 0.0,
            'lines': text.count('\n') + 1,
            'code_fence': float('```' in text),
            'code_words': len(CODE_WORDS.findall(text)),
            'question_marks': text.count('?') + text.count('？'),
            'digits': sum(ch.isdigit() for ch in text),
            'ascii_words': len(re.findall(r'[A-Za-z]{2,}', text)),
            'doc_none': float(bool(DOC_NONE.search(text))),
            'doc_zh': float(bool(DOC_ZH.search(text))),
            'doc_en': float(bool(DOC_EN.search(text))),
            **{'fam_' + name: float(name in text) for name in FAMILIES}}


def rows_from_batch(batch, cases_path):
    """读取控制器批次，返回完整配对的训练行。"""
    import analyze_discovery
    cases = {case['case_id']: case for case in json.loads(Path(cases_path).read_text(encoding='utf-8'))}
    paired, _counts = analyze_discovery.load_attempts(Path(batch))
    rows = []
    for (case_id, repeat), arms in sorted(paired.items()):
        if not {'direct', 'prefix'} <= set(arms):
            continue
        case = cases.get(case_id)
        if case is None:
            continue
        direct = arms['direct']
        mtp = arms['prefix']
        direct_ms = direct['response']['wall_s'] * 1000
        mtp_ms = mtp['response']['wall_s'] * 1000
        row = features(case, direct['response']['usage']['prompt_tokens'])
        row.update(case_id=case_id, round=repeat,
                   family=(case.get('metadata') or {}).get('family') or case_id,
                   direct_ms=direct_ms, mtp_ms=mtp_ms, saving_ms=direct_ms - mtp_ms,
                   saving_pct=100 * (1 - mtp_ms / direct_ms))
        rows.append(row)
    return rows


def split_by_family(rows, folds):
    families = sorted({row['family'] for row in rows})
    if len(families) < folds:
        folds = max(2, len(families))
    rng = random.Random(20261020)
    rng.shuffle(families)
    return [[row for row in rows if row['family'] in set(families[index::folds])]
            for index in range(folds)]


def sigmoid(value):
    return 1 / (1 + math.exp(-max(-30.0, min(30.0, value))))


def fit(rows, label):
    stats = {}
    for name in FEATURES:
        values = [row[name] for row in rows]
        mean = sum(values) / len(values)
        spread = math.sqrt(sum((value - mean) ** 2 for value in values) / len(values)) or 1.0
        stats[name] = (mean, spread)
    weights = [0.0] * (len(FEATURES) + 1)
    vectors = [{name: (row[name] - stats[name][0]) / stats[name][1] for name in FEATURES} for row in rows]
    for _ in range(400):
        gradient = [0.0] * len(weights)
        for vector, row in zip(vectors, rows):
            predicted = sigmoid(weights[0] + sum(w * vector[name] for w, name in zip(weights[1:], FEATURES)))
            error = predicted - label(row)
            gradient[0] += error
            for index, name in enumerate(FEATURES):
                gradient[index + 1] += error * vector[name]
        for index in range(len(weights)):
            penalty = 0.0 if index == 0 else 0.01 * weights[index]
            weights[index] -= 0.2 * (gradient[index] / len(rows) + penalty)
    return stats, weights


def score(stats, weights, row):
    vector = {name: (row[name] - stats[name][0]) / stats[name][1] for name in FEATURES}
    return sigmoid(weights[0] + sum(w * vector[name] for w, name in zip(weights[1:], FEATURES)))


def best_threshold(train, stats, weights, classifier_ms, positive_pct=5.0):
    """在训练折上选使净收益最大的概率阈值。"""
    scores = sorted(score(stats, weights, row) for row in train)
    candidates = {0.0, 1.0}
    candidates.update(scores[index] for index in range(0, len(scores), max(1, len(scores) // 20)))
    best = (float('-inf'), 1.0)
    for threshold in candidates:
        gain = evaluate(train, lambda row: score(stats, weights, row) >= threshold,
                        classifier_ms, positive_pct)['net_gain_pct']
        if gain > best[0]:
            best = (gain, threshold)
    return best[1]


def evaluate(rows, choose, classifier_ms, positive_pct=5.0):
    """返回净收益、精确率、召回率与误判平均损失。"""
    direct = sum(row['direct_ms'] for row in rows)
    chosen = 0.0
    true_positive = false_positive = predicted = actual = 0
    losses = []
    for row in rows:
        if choose(row):
            predicted += 1
            chosen += row['mtp_ms'] + classifier_ms
            if row['saving_pct'] >= positive_pct:
                true_positive += 1
            else:
                false_positive += 1
                losses.append(-row['saving_ms'])
        else:
            chosen += row['direct_ms']
        if row['saving_pct'] >= positive_pct:
            actual += 1
    return {'rows': len(rows), 'net_gain_pct': 100 * (1 - chosen / direct),
            'precision': true_positive / predicted if predicted else None,
            'recall': true_positive / actual if actual else None,
            'predicted': predicted,
            'false_positive_mean_loss_ms': statistics.mean(losses) if losses else 0.0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch', type=Path, required=True)
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--classifier-ms', type=float, default=3.0)
    parser.add_argument('--folds', type=int, default=4)
    args = parser.parse_args(argv)
    rows = rows_from_batch(args.batch, args.cases)
    if not rows:
        raise ValueError('no complete pair')
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'dataset.json').write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    folds = split_by_family(rows, args.folds)
    median_direct = statistics.median(row['direct_ms'] for row in rows)
    margin = 2.0 + 100 * args.classifier_ms / median_direct
    results = []
    for index, test in enumerate(folds):
        train = [row for fold in folds if fold is not test for row in fold]
        if not train or not test:
            continue
        stats, weights = fit(train, lambda row: 1.0 if row['saving_pct'] >= 5.0 else 0.0)
        threshold = best_threshold(train, stats, weights, args.classifier_ms)
        results.append({'fold': index, 'families': sorted({row['family'] for row in test}),
                        'threshold': threshold,
                        'logistic': evaluate(test, lambda row: score(stats, weights, row) >= threshold,
                                             args.classifier_ms),
                        'all_mtp': evaluate(test, lambda row: True, args.classifier_ms),
                        'none': evaluate(test, lambda row: False, args.classifier_ms)})
    summary = {'rows': len(rows), 'families': len({row['family'] for row in rows}),
               'positive_pct': 100 * sum(row['saving_pct'] >= 5 for row in rows) / len(rows),
               'margin_pct': margin, 'folds': results}
    (args.output / 'stage2-cv.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'rows': summary['rows'], 'families': summary['families'],
                      'positive_pct': round(summary['positive_pct'], 1),
                      'folds': [{'families': item['families'],
                                 'logistic_gain': round(item['logistic']['net_gain_pct'], 3),
                                 'all_mtp_gain': round(item['all_mtp']['net_gain_pct'], 3)}
                                for item in results]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
