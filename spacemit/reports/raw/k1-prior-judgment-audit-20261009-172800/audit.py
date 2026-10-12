import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEST = Path(__file__).resolve().parent
inputs = {}
errors = []
gate_count = 0
comparison_count = 0
raw_comparison_count = 0
raw_requests = set()
decisions = []


def read(path):
    data = path.read_bytes()
    inputs[str(path.relative_to(ROOT))] = hashlib.sha256(data).hexdigest()
    return json.loads(data)


def check(condition, label):
    if not condition:
        errors.append(label)


def gate(value, label):
    global gate_count
    base = value['base_ms']
    candidate = value['candidate_ms']
    check(len(base) >= 2 and len(candidate) >= 2, label + ': 样本不足')
    check(all(math.isfinite(v) and v > 0 for v in base + candidate), label + ': 时间无效')
    mean_base = sum(base) / len(base)
    gain = 100 * (1 - sum(candidate) / len(candidate) / mean_base)
    noise = 100 * (max(base) - min(base)) / mean_base
    check(abs(gain - value['reduction_pct']) < 1e-9, label + ': 收益计算不符')
    check(abs(noise - value['control_range_pct']) < 1e-9, label + ': 控制范围不符')
    check((gain > max(3, noise)) == value['advance'], label + ': 收益判定不符')
    check((gain < -max(3, noise)) == value['clear_regression'], label + ': 退化判定不符')
    gate_count += 1


def walk(value, label):
    if isinstance(value, dict):
        if {'base_ms', 'candidate_ms', 'advance', 'clear_regression'} <= value.keys():
            gate(value, label)
        else:
            for key, child in value.items():
                walk(child, label + '/' + key)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk(child, label + '/' + str(index))


raw = ROOT / 'raw'
result_files = sorted(p for p in raw.glob('k1-local-candidates-*/**/result.json')
                      if DEST not in p.parents)
for path in result_files:
    obj = read(path)
    if not isinstance(obj, dict) or 'comparisons' not in obj:
        continue
    walk(obj, str(path.relative_to(ROOT)))
    is_b1 = 'B1-r2' in str(path)
    for row in obj['comparisons']:
        metrics = row['metrics']
        if is_b1:
            passed = not any(v['clear_regression'] for v in metrics.values())
            if row['tokens'] == 2048 and row['outputs'] == 65:
                passed = passed and metrics['decode']['advance']
        else:
            passed = (metrics['prefill']['advance'] and metrics['ttft']['advance']) if row['outputs'] == 1 else not metrics['decode']['clear_regression']
        label = str(path.relative_to(ROOT)) + ':' + str((row['model'], row['tokens'], row['outputs']))
        check(passed == row['passed'], label + ': 配置门槛不符')
        comparison_count += 1
        if not passed:
            decisions.append({'证据': label, '通过': False, '指标': metrics})
        prefix = '{}-p{}-n{}-'.format(row['model'], row['tokens'], row['outputs'])
        files = sorted(path.parent.glob(prefix + '*.jsonl'), key=lambda p: int(p.stem.rsplit('-', 1)[1]))
        if len(files) != 4:
            continue
        records = []
        configs = []
        for f in files:
            data = f.read_bytes()
            inputs[str(f.relative_to(ROOT))] = hashlib.sha256(data).hexdigest()
            entries = [json.loads(line) for line in data.splitlines()]
            configs.append(next(x for x in entries if x['kind'] == 'config'))
            records.append(next(x for x in entries if x['kind'] == 'measurement'))
            raw_requests.add(str(f.relative_to(ROOT)))
        check(len({tuple(r['prompt_token_sha256']) for r in records}) == 1, label + ': 输入哈希不同')
        check(len({tuple(r['results'][0]['token_ids']) for r in records}) == 1, label + ': 输出词元不同')
        for config, record in zip(configs, records):
            check(config['threads'] == 4 and config['batch_size'] == config['ubatch_size'] == 32, label + ': 配置不同')
            check(config['cache_type_k'] == config['cache_type_v'] == 'f16', label + ': KV 类型不同')
            timing = record['results'][0]['timings']
            check(timing['cache_n'] == 0 and timing['prompt_n'] == row['tokens'], label + ': 冷输入不同')
            check(len(record['results'][0]['token_ids']) == row['outputs'], label + ': 输出长度不同')
        for name, value in metrics.items():
            times = [r['results'][0]['ttft_ms'] if name == 'ttft' else r['results'][0]['timings']['prompt_ms' if name == 'prefill' else 'predicted_ms'] for r in records]
            check(value['base_ms'] == [times[0], times[3]], label + ': 控制计时与原记录不同')
            check(value['candidate_ms'] == [times[1], times[2]], label + ': 候选计时与原记录不同')
        raw_comparison_count += 1

native_files = [
    raw / 'k1-local-candidates-screen-20261008-185900/summary.json',
    raw / 'k1-local-candidates-checkpoint-20261008-190630/D/summary.json',
    raw / 'k1-local-candidates-C2-B1-results-20261009-050000/k1-local-candidates-B1-r2-20261008-231500/summary.json',
    raw / 'k1-local-candidates-C2-r2-result-20261009-130000/summary.json',
]
for path in native_files:
    if path.exists():
        walk(read(path), str(path.relative_to(ROOT)))

paired_count = 0
answer_count = 0
reference_answers = {}
for directory in ['k1-local-candidates-C1-complete-20261009-040000',
                  'k1-local-candidates-C3-final-20261009-130000',
                  'k1-local-candidates-B1-r2-final-20261009-171400']:
    for model in ('2B', '4B'):
        path = raw / directory / 'complete-answers' / (model + '-pairs.json')
        pairs = read(path)
        check(len(pairs) == 6, directory + ': 任务数不同')
        for task, arms in pairs.items():
            values = list(arms.values())
            check(len(values) == 2, directory + ': 配对数量不同')
            check(values[0]['request'] == values[1]['request'], directory + ':' + task + ': 请求不同')
            check(values[0]['answer'] == values[1]['answer'], directory + ':' + task + ': 全文不同')
            for value in values:
                check(value['finish_reason'] == 'stop' and all(value['audit'].values()), directory + ':' + task + ': 停止或审计失败')
                check(hashlib.sha256(value['answer'].encode()).hexdigest() == value['answer_sha256'], directory + ':' + task + ': 文本哈希不同')
                answer_count += 1
            key = model + '/' + task
            if key in reference_answers:
                check(reference_answers[key] == (values[0]['request'], values[0]['answer']), directory + ':' + task + ': 与已复核控制不同')
            else:
                reference_answers[key] = (values[0]['request'], values[0]['answer'])
            paired_count += 1

summary = {'状态': '通过' if not errors else '发现差异', '门槛计算核验数': gate_count,
           '配置判定核验数': comparison_count, '原冷请求计时核验配置数': raw_comparison_count,
           '原冷请求文件数': len(raw_requests), '完整回答配对数': paired_count, '完整回答数': answer_count,
           '配置失败记录': decisions, '差异': errors,
           '限制': '历史快照含重复记录。上述计数不是独立实验数量。未复核全部路径日志、原生计时预算或二进制状态。本次未启动板端任务。四线程配置不等于逐请求操作系统线程快照。'}
(DEST / 'audit-result.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
(DEST / 'input-sha256.json').write_text(json.dumps(inputs, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in summary.items() if k != '配置失败记录'}, ensure_ascii=False, indent=2))
