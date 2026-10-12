import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEST = Path(__file__).resolve().parent
sources = {}
receipts = {}


def load(path):
    data = path.read_bytes()
    sources[str(path.relative_to(ROOT))] = hashlib.sha256(data).hexdigest()
    return json.loads(data)


def receipt(directory):
    path = ROOT / 'raw' / directory / 'SHA256SUMS'
    count = 0
    for line in path.read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        target = path.parent / name.lstrip('*')
        assert hashlib.sha256(target.read_bytes()).hexdigest() == digest, str(target)
        count += 1
    receipts[directory] = count
    sources[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()


results = {}
for candidate, directory, rounds, requests in [
    ('C1', 'k1-local-candidates-C1-complete-20261009-040000', 2, 64),
    ('C3', 'k1-local-candidates-C3-final-20261009-130000', 4, 128),
    ('B1-r2', 'k1-local-candidates-B1-r2-final-20261009-171400', 2, 64),
]:
    receipt(directory)
    path = ROOT / 'raw' / directory
    summary = load(path / 'summary.json')
    assert summary['baseline_preserved'] is True
    assert len(summary['repeats']) == rounds
    measures = []
    for group in summary['repeats']:
        assert group['status'] == 'eligible'
        assert len(group['comparisons']) == 8
        for row in group['comparisons']:
            assert row['passed'] is True
            for metric in row['metrics'].values():
                control = sum(metric['base_ms']) / len(metric['base_ms'])
                gain = 100 * (1 - sum(metric['candidate_ms']) / len(metric['candidate_ms']) / control)
                spread = 100 * (max(metric['base_ms']) - min(metric['base_ms'])) / control
                assert abs(gain - metric['reduction_pct']) < 1e-9
                assert abs(spread - metric['control_range_pct']) < 1e-9
                assert metric['advance'] == (gain > max(3, spread))
                assert metric['clear_regression'] == (gain < -max(3, spread))
            if candidate == 'B1-r2':
                assert not any(x['clear_regression'] for x in row['metrics'].values())
                primary = row['tokens'] == 2048 and row['outputs'] == 65
                metric = 'decode'
            else:
                primary = row['outputs'] == 1
                metric = 'ttft'
                if primary:
                    assert row['metrics']['prefill']['advance'] and row['metrics']['ttft']['advance']
                else:
                    assert not row['metrics']['decode']['clear_regression']
            if primary:
                assert row['metrics'][metric]['advance']
                measures.append({'模型': row['model'], '输入词元': row['tokens'],
                                 '指标': metric, '对照': group.get('reference', 'B0'),
                                 '耗时减少百分比': row['metrics'][metric]['reduction_pct']})
    pairs = 0
    for model in ('2B', '4B'):
        answers = load(path / 'complete-answers' / (model + '-pairs.json'))
        assert len(answers) == 6
        for arms in answers.values():
            values = list(arms.values())
            assert len(values) == 2
            assert values[0]['request'] == values[1]['request']
            assert values[0]['answer'] == values[1]['answer']
            for value in values:
                assert value['finish_reason'] == 'stop'
                assert all(value['audit'].values())
                assert hashlib.sha256(value['answer'].encode()).hexdigest() == value['answer_sha256']
            pairs += 1
    review = load(path / ('local-review.json' if candidate == 'C1' else 'complete-answer-review.json'))
    results[candidate] = {'判定': '通过本次加速实验验收', '独立冷请求数': requests,
                          '完整回答数': pairs * 2, '配对全文相同': True,
                          '基线保留': True, '主指标原始结果': measures,
                          '共有绝对质量失败': '保留为基线限制，不作为本次验收阻塞项',
                          '原机器摘要': summary['status'], '本机全文复核记录已存在': True}

receipt('k1-prior-judgment-audit-20261009-172800')
audit = load(ROOT / 'raw/k1-prior-judgment-audit-20261009-172800/audit-result.json')
assert not audit['差异']
receipt('k1-local-candidates-C2-r2-state-20261009-171400')
state = load(ROOT / 'raw/k1-local-candidates-C2-r2-state-20261009-171400/local-review.json')
assert all(x['三路实际字节逐位相同'] and x['回退实际字节与主探针 RS=3 部分相同'] for x in state['模型'].values())
results['C2-r2'] = {'判定': '待验证', '已验证': '算子、新三路模型状态和独立 RS=3 回退',
                    '当前状态': '2026-10-09 17:43，初筛 4B／2048／1 词元的最后一次控制请求正在执行',
                    '待验证': '完整初筛、两轮独立复验及完整回答'}
results['旧 C2'] = {'判定': '未通过收益门槛', '依据': '2B／2048／1 词元的首词元延迟减少 2.7961286%，预填充减少 2.7965186%，均未超过 3%'}
results['A1、旧 B1、D'] = {'判定': '各旧版本未通过算子性能门槛', '依据': '本次复查没有发现推翻既有负结果的证据'}
record = {'时间': '2026-10-09 17:43，Asia/Singapore',
          '验收范围': '共有答案错误不阻塞；原库对照、数值与状态一致、无新增回归和固定性能门槛仍须通过',
          '结果': results, '证据收据复核文件数': receipts, '输入文件哈希': sources,
          '限制': ['所测 K1、两个固定 Qwen3.5 模型及固定配置下的实验结论。',
                   '每臂每配置两次请求不能证明总体置信区间。',
                   '没有验证 B1-r2 与 C3 同时开启的组合，收益不能相加。',
                   '完整回答没有逐请求操作系统线程快照。',
                   'Python 段错误及其结果污染风险仍待专项调查。',
                   '初次状态读取因板端没有 rg 返回 127。后续 shell 读取成功。此监控命令故障不是模型故障。']}
(DEST / 'decisions.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'判定': {key: value['判定'] for key, value in results.items()}, '收据': receipts}, ensure_ascii=False, indent=2))
