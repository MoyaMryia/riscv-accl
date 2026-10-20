#!/usr/bin/env python3
"""微调本地 BERT 编码器，并导出路由分类器。"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import random
import time

import bert_common
import classifier
import train as task_data

REPOSITORY = 'uer/chinese_roberta_L-4_H-256'
REVISION = '68d674689f3c9d425e5436149c8acece077187f1'


def sha256(path):
    """返回文件的 SHA-256 值。"""
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def read_inputs(base, tasks, receipt_path, regression_path):
    """读取并核对本次运行的全部外部输入。"""
    try:
        receipt = json.loads(Path(receipt_path).read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError('receipt 文件无法读取或不是有效 JSON') from error
    expected_keys = {'base', 'dataset_sha256', 'repository', 'revision'}
    if not isinstance(receipt, dict) or set(receipt) != expected_keys:
        raise ValueError('receipt 字段无效')
    if receipt['repository'] != REPOSITORY or receipt['revision'] != REVISION:
        raise ValueError('receipt 模型来源无效')
    if not isinstance(receipt['dataset_sha256'], str) or len(receipt['dataset_sha256']) != 64 \
            or any(char not in '0123456789abcdef' for char in receipt['dataset_sha256']):
        raise ValueError('receipt 数据集哈希无效')
    pins = receipt['base']
    if not isinstance(pins, dict) or not pins:
        raise ValueError('receipt base 哈希无效')
    for name, digest in pins.items():
        if not isinstance(name, str) or not name or Path(name).is_absolute() \
                or '..' in Path(name).parts or name != Path(name).as_posix():
            raise ValueError('receipt base 文件名无效')
        if not isinstance(digest, str) or len(digest) != 64 \
                or any(char not in '0123456789abcdef' for char in digest):
            raise ValueError('receipt base 文件哈希无效')
    files = {path.relative_to(base).as_posix(): path for path in base.rglob('*') if path.is_file()}
    if set(files) != set(pins):
        raise ValueError('base 文件集合与 receipt 不同')
    for name, path in files.items():
        if sha256(path) != pins[name]:
            raise ValueError(f'base 文件哈希不匹配：{name}')
    if sha256(tasks) != receipt['dataset_sha256']:
        raise ValueError('tasks 文件哈希与 receipt 不同')
    rows = task_data.read_tasks(tasks)
    regression = json.loads(Path(regression_path).read_text(encoding='utf-8'))
    if not isinstance(regression, list) or not regression:
        raise ValueError('regression 必须是非空数组')
    regression_ids = set()
    regression_texts = set()
    training_texts = {' '.join(row['text'].casefold().split()) for row in rows if row['split'] == 'train'}
    for row in regression:
        if not isinstance(row, dict) or set(row) != {'id', 'label', 'text'}:
            raise ValueError('regression 行字段无效')
        if not isinstance(row['id'], str) or not row['id'].strip() or row['id'] in regression_ids:
            raise ValueError('regression id 无效或重复')
        if not isinstance(row['label'], str) or row['label'] not in classifier.LABELS:
            raise ValueError('regression label 无效')
        if not isinstance(row['text'], str) or not row['text'].strip():
            raise ValueError('regression text 无效')
        row['text'].encode('utf-8')
        normalized = ' '.join(row['text'].casefold().split())
        if normalized in training_texts or normalized in regression_texts:
            raise ValueError('regression 文本重复或进入训练集')
        regression_ids.add(row['id'])
        regression_texts.add(normalized)
    return rows, regression


def write_json(path, value):
    """以稳定、可读的 JSON 格式写入结果。"""
    with Path(path).open('w', encoding='utf-8') as target:
        json.dump(value, target, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        target.write('\n')


def metrics(model, rows, predictions):
    """使用缓存预测调用统一指标函数。"""
    return task_data.evaluate(model, rows, predict=lambda _model, text: predictions[text])


def main(argv=None):
    """执行 BERT 微调，保存最佳 dev 模型并评估冻结数据。"""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base', 'tasks', 'receipt', 'regression', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(argv)
    rows, regression = read_inputs(args.base, args.tasks, args.receipt, args.regression)
    args.output.mkdir(parents=True, exist_ok=False)

    import torch
    from torch import nn
    from torch.optim import AdamW
    from transformers import BertModel, BertTokenizerFast

    defaults = bert_common.DEFAULTS
    random.seed(defaults['seed'])
    torch.manual_seed(defaults['seed'])
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(defaults['threads'])
    torch.set_num_interop_threads(1)
    device = torch.device('cpu')
    tokenizer = BertTokenizerFast.from_pretrained(args.base, local_files_only=True)
    encoder = BertModel.from_pretrained(args.base, local_files_only=True, add_pooling_layer=False)
    hidden_size = int(encoder.config.hidden_size)
    head = nn.Linear(hidden_size, len(classifier.LABELS))
    dropout = nn.Dropout(float(encoder.config.hidden_dropout_prob))
    encoder.to(device)
    head.to(device)
    label_ids = {label: index for index, label in enumerate(classifier.LABELS)}
    metadata = {'cls_token_id': tokenizer.cls_token_id, 'sep_token_id': tokenizer.sep_token_id,
                'max_tokens': defaults['max_tokens']}
    examples = []
    for row in rows:
        token_ids = tokenizer(row['text'], add_special_tokens=False)['input_ids']
        selected = bert_common.add_special(token_ids, metadata)
        examples.append((row, selected, label_ids[row['label']]))

    optimizer = AdamW([
        {'params': list(encoder.parameters()), 'lr': defaults['encoder_lr']},
        {'params': list(head.parameters()), 'lr': defaults['head_lr']},
    ], weight_decay=defaults['weight_decay'])
    train_examples = [item for item in examples if item[0]['split'] == 'train']
    dev_rows = [row for row in rows if row['split'] == 'dev']
    test_rows = [row for row in rows if row['split'] == 'test']
    dev_examples = [item for item in examples if item[0]['split'] == 'dev']
    started = time.perf_counter()
    history = []
    best_key = None
    best_epoch = None
    best_state = None
    best_head_state = None
    best_dev_predictions = None

    def forward_batch(batch):
        lengths = [len(item[1]) for item in batch]
        width = max(lengths)
        pad = tokenizer.pad_token_id
        input_ids = torch.full((len(batch), width), pad, dtype=torch.long, device=device)
        attention = torch.zeros((len(batch), width), dtype=torch.long, device=device)
        for index, (_, token_ids, _) in enumerate(batch):
            input_ids[index, :len(token_ids)] = torch.tensor(token_ids, dtype=torch.long, device=device)
            attention[index, :len(token_ids)] = 1
        token_types = torch.zeros_like(input_ids)
        output = encoder(input_ids=input_ids, attention_mask=attention, token_type_ids=token_types)
        return output.last_hidden_state[:, 0, :]

    def predict_examples(selected_examples):
        encoder.eval()
        head.eval()
        result = {}
        with torch.no_grad():
            for start in range(0, len(selected_examples), defaults['batch_size']):
                batch = selected_examples[start:start + defaults['batch_size']]
                embeddings = forward_batch(batch)
                logits = head(embeddings)
                probabilities = torch.softmax(logits, dim=-1)
                for offset, (row, token_ids, _) in enumerate(batch):
                    values = logits[offset].tolist()
                    scores_list = probabilities[offset].tolist()
                    best = max(range(len(scores_list)), key=scores_list.__getitem__)
                    result[row['text']] = {
                        'category': classifier.LABELS[best], 'score': scores_list[best],
                        'scores': dict(zip(classifier.LABELS, scores_list)), 'logits': values,
                        'selected_token_ids': token_ids,
                        'cls_embedding': embeddings[offset].tolist(),
                    }
        return result

    for epoch in range(1, defaults['epochs'] + 1):
        encoder.train()
        head.train()
        order = list(train_examples)
        random.shuffle(order)
        loss_sum = 0.0
        for start in range(0, len(order), defaults['batch_size']):
            batch = order[start:start + defaults['batch_size']]
            targets = torch.tensor([item[2] for item in batch], dtype=torch.long, device=device)
            optimizer.zero_grad(set_to_none=True)
            embeddings = forward_batch(batch)
            logits = head(dropout(embeddings))
            loss = nn.functional.cross_entropy(logits, targets, reduction='mean')
            loss.backward()
            optimizer.step()
            loss_sum += float(loss.detach()) * len(batch)
        dev_predictions = predict_examples(dev_examples)
        dev_metrics = metrics({'min_score': classifier.DEFAULT_MIN_SCORE}, dev_rows, dev_predictions)
        macro_f1 = sum(item['f1'] for item in dev_metrics['per_label'].values()) / len(classifier.LABELS)
        entry = {'epoch': epoch, 'train_loss': loss_sum / len(train_examples),
                 'dev': dev_metrics, 'dev_macro_f1': macro_f1}
        history.append(entry)
        write_json(args.output / 'history.json', history)
        print(json.dumps(entry, ensure_ascii=False, allow_nan=False), flush=True)
        key = (macro_f1, dev_metrics['accuracy'])
        if best_key is None or key > best_key:
            best_key = key
            best_epoch = epoch
            best_state = {name: value.detach().clone() for name, value in encoder.state_dict().items()}
            best_head_state = {name: value.detach().clone() for name, value in head.state_dict().items()}
            best_dev_predictions = dev_predictions

    encoder.load_state_dict(best_state)
    head.load_state_dict(best_head_state)
    encoder.eval()
    head.eval()
    encoder.save_pretrained(args.output / 'encoder', safe_serialization=True)
    tokenizer.save_pretrained(args.output / 'encoder')
    head_weight = head.weight.detach().cpu().tolist()
    head_bias = head.bias.detach().cpu().tolist()
    config = encoder.config
    head_file = {
        'format': 1, 'labels': list(classifier.LABELS), 'hidden_size': hidden_size,
        'vocab_size': int(config.vocab_size), 'max_tokens': defaults['max_tokens'],
        'cls_token_id': int(tokenizer.cls_token_id), 'sep_token_id': int(tokenizer.sep_token_id),
        'pad_token_id': int(tokenizer.pad_token_id), 'weights': head_weight, 'bias': head_bias,
        'min_score': classifier.DEFAULT_MIN_SCORE,
    }
    write_json(args.output / 'head.json', head_file)

    test_examples = [item for item in examples if item[0]['split'] == 'test']
    test_predictions = predict_examples(test_examples)
    dev_metric = metrics({'min_score': classifier.DEFAULT_MIN_SCORE}, dev_rows, best_dev_predictions)
    test_metric = metrics({'min_score': classifier.DEFAULT_MIN_SCORE}, test_rows, test_predictions)
    regression_examples = []
    for row in regression:
        token_ids = tokenizer(row['text'], add_special_tokens=False)['input_ids']
        regression_examples.append((row, bert_common.add_special(token_ids, metadata), label_ids[row['label']]))
    regression_predictions = predict_examples(regression_examples)
    regression_metric = metrics({'min_score': classifier.DEFAULT_MIN_SCORE}, regression, regression_predictions)

    def records(selected_rows, predictions):
        by_text = predictions
        output = []
        for row in selected_rows:
            prediction = by_text[row['text']]
            output.append({'id': row['id'], 'label': row['label'], 'text': row['text'],
                           **prediction})
        return output

    write_json(args.output / 'best-dev-predictions.json', records(dev_rows, best_dev_predictions))
    write_json(args.output / 'test-predictions.json', records(test_rows, test_predictions))
    write_json(args.output / 'regression-predictions.json', records(regression, regression_predictions))
    baseline = classifier.load_model(Path(__file__).with_name('model.json.gz'))
    baseline_metrics = {
        'test': task_data.evaluate(baseline, test_rows),
        'regression': task_data.evaluate(baseline, regression),
    }
    counts = Counter(row['split'] for row in rows)
    elapsed = time.perf_counter() - started
    result = {
        'configuration': defaults,
        'versions': {'python': platform.python_version(), 'torch': torch.__version__,
                     'transformers': __import__('transformers').__version__},
        'split_counts': {name: counts[name] for name in task_data.SPLITS},
        'regression_count': len(regression), 'best_epoch': best_epoch,
        'metrics': {'best_dev': dev_metric, 'test': test_metric,
                    'regression': regression_metric, 'baseline_ngram': baseline_metrics},
        'parameters': {'encoder': sum(parameter.numel() for parameter in encoder.parameters()),
                       'head': sum(parameter.numel() for parameter in head.parameters()),
                       'total': sum(parameter.numel() for parameter in encoder.parameters())
                                + sum(parameter.numel() for parameter in head.parameters())},
        'elapsed_seconds': elapsed,
    }
    write_json(args.output / 'training.json', result)
    print(json.dumps(result, ensure_ascii=False, allow_nan=False), flush=True)
    return result


if __name__ == '__main__':
    main()
