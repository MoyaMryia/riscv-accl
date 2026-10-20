"""训练并评估解码路由分类器。"""
import argparse
from collections import Counter
import json
from pathlib import Path

import classifier

SPLITS = ('train', 'dev', 'test')
FIELDS = {'id', 'text', 'label', 'split'}


def read_tasks(path):
    """读取并检查 JSONL 任务及其拆分。"""
    rows = []
    ids = set()
    normalized_texts = set()
    counts = Counter()
    with Path(path).open(encoding='utf-8') as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f'第 {line_number} 行不是有效 JSON') from error
            if not isinstance(row, dict) or set(row) != FIELDS:
                raise ValueError(f'第 {line_number} 行字段无效')
            task_id, text = row['id'], row['text']
            label, split = row['label'], row['split']
            if not isinstance(task_id, str) or not task_id.strip():
                raise ValueError(f'第 {line_number} 行 id 无效')
            if not isinstance(text, str) or not text.strip():
                raise ValueError(f'第 {line_number} 行 text 无效')
            text.encode('utf-8')
            if not isinstance(label, str) or label not in classifier.LABELS:
                raise ValueError(f'第 {line_number} 行 label 无效')
            if not isinstance(split, str) or split not in SPLITS:
                raise ValueError(f'第 {line_number} 行 split 无效')
            normalized = ' '.join(text.casefold().split())
            if task_id in ids:
                raise ValueError(f'第 {line_number} 行 id 重复')
            if normalized in normalized_texts:
                raise ValueError(f'第 {line_number} 行归一化 text 重复')
            ids.add(task_id)
            normalized_texts.add(normalized)
            counts[split] += 1
            rows.append(row)
    empty_splits = [split for split in SPLITS if counts[split] == 0]
    if empty_splits:
        raise ValueError(f'任务拆分不能为空：{", ".join(empty_splits)}')
    return rows


def evaluate(model, rows):
    """计算 argmax 准确率、混淆矩阵和阈值覆盖数据。"""
    labels = classifier.LABELS
    confusion = {actual: {predicted: 0 for predicted in labels} for actual in labels}
    correct = 0
    covered = 0
    covered_correct = 0
    for row in rows:
        result = classifier.predict(model, row['text'])
        predicted = result['category']
        confusion[row['label']][predicted] += 1
        is_correct = predicted == row['label']
        correct += is_correct
        if result['score'] >= model['min_score']:
            covered += 1
            covered_correct += is_correct
    count = len(rows)
    return {
        'accuracy': correct / count,
        'confusion': confusion,
        'high_score_coverage_count': covered,
        'high_score_coverage': covered / count,
        'high_score_accuracy': covered_correct / covered if covered else None,
    }


def main(argv=None):
    """训练模型，保存文件，并评估 dev 与 test 拆分。"""
    parser = argparse.ArgumentParser(description='训练解码路由分类器')
    parser.add_argument('--tasks', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(argv)
    rows = read_tasks(args.tasks)
    args.output.mkdir(parents=True, exist_ok=False)
    train_rows = [row for row in rows if row['split'] == 'train']
    dev_rows = [row for row in rows if row['split'] == 'dev']
    test_rows = [row for row in rows if row['split'] == 'test']
    model_path = args.output / 'model.json.gz'
    classifier.save_model(classifier.train(train_rows), model_path)
    model = classifier.load_model(model_path)
    counts = Counter(row['split'] for row in rows)
    result = {
        'split_counts': {split: counts[split] for split in SPLITS},
        'model_bytes': model_path.stat().st_size,
        'metrics': {
            'dev': evaluate(model, dev_rows),
            'test': evaluate(model, test_rows),
        },
    }
    with (args.output / 'training.json').open('w', encoding='utf-8') as target:
        json.dump(result, target, ensure_ascii=False, indent=2, sort_keys=True)
        target.write('\n')
    return result


if __name__ == '__main__':
    main()
