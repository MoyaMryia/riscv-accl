#!/usr/bin/env python3
"""汇总发现批次的完整配对。只读目录，不改写记录。"""
import argparse
from collections import defaultdict
from fractions import Fraction
import json
from pathlib import Path
import statistics

ARMS = ('direct', 'prefix', 'lowacc')
COMPLETED = {'complete', 'quality', 'quality_review_pending'}
CONTROLLER_FAILURES = {'backend_busy', 'backend_unavailable', 'timeout', 'worker_crash',
                       'worker_exit', 'worker_protocol', 'worker_spawn'}
LEGACY = 'legacy_unicode_runs'


def controller_status(folder):
    """返回控制器写入的最终状态；旧批次可能没有该文件。"""
    path = folder / 'status.json'
    if not path.exists():
        return None, None
    value = json.loads(path.read_text())
    return value.get('status'), value.get('reason')


def load_attempts(batch):
    """返回 (配对字典, 计数)。配对字典键为 (case_id, round)。"""
    paired = {}
    counts = {'attempts': 0, 'complete': 0, 'incomplete': 0, 'other': 0, 'controller_rejected': 0}
    for folder in sorted((batch / 'attempts').iterdir()):
        if not folder.is_dir():
            continue
        counts['attempts'] += 1
        outcome_path = folder / 'outcome.json'
        result_path = folder / 'result.json'
        if not outcome_path.exists() or not result_path.exists():
            counts['incomplete'] += 1
            continue
        outcome = json.loads(outcome_path.read_text())
        reason = outcome.get('reason')
        if reason not in COMPLETED:
            counts['incomplete'] += 1
            continue
        # 资源或后置检查失败时，结果文件仍可能存在；该尝试不得进入配对。
        # 质量失败仍计入配对：答案已完整生成，计时有效。
        _, controller_reason = controller_status(folder)
        if controller_reason in CONTROLLER_FAILURES:
            counts['controller_rejected'] += 1
            continue
        row = json.loads(result_path.read_text())
        if row.get('arm') not in ARMS:
            counts['other'] += 1
            continue
        counts['complete'] += 1
        paired.setdefault((row['case_id'], row['round']), {})[row['arm']] = row
    return paired, counts


def triplets(paired):
    return {key: arms for key, arms in paired.items() if set(arms) == set(ARMS)}


def slowdown(arms):
    """返回 prefix、lowacc 相对 direct 的墙钟变化百分比。"""
    direct = arms['direct']['response']['wall_s']
    result = {}
    for arm in ARMS[1:]:
        result[arm] = 100 * (Fraction(arms[arm]['response']['wall_s']) / Fraction(direct) - 1)
    return result


def acceptance(row):
    trace = row.get('verification')
    if not trace:
        return None
    return trace['original_first_accepted'] / trace['original_proposed'] if trace['original_proposed'] else None


def group_key(case):
    """返回分组标签。代码按函数族、指令语言和文档模式，文本按资料长度。"""
    metadata = case.get('metadata') or {}
    if case['category'] == 'code':
        return ('code', metadata.get('family'), metadata.get('prompt_language'), metadata.get('doc_mode'))
    chars = metadata.get('material_chars') or 0
    bucket = 'short' if chars < 1000 else 'medium' if chars < 2000 else 'long'
    return (case['category'], bucket, None, None)


def legacy_case(case_id):
    """旧代码正控不在冻结题目集中，单独标记。"""
    if case_id != LEGACY:
        raise ValueError('case is absent from the frozen plan: ' + case_id)
    return {'case_id': case_id, 'category': 'code',
            'metadata': {'family': 'unicode_runs_control', 'prompt_language': 'legacy', 'doc_mode': 'none'}}


def summarize(paired, cases):
    """按分组统计墙钟、接受率、恢复比例、覆盖率和质量。"""
    by_id = {case['case_id']: case for case in cases}
    groups = defaultdict(list)
    for (case_id, repeat), arms in triplets(paired).items():
        case = by_id.get(case_id) or legacy_case(case_id)
        groups[group_key(case)].append((case_id, repeat, arms))
    result = {'triplets': 0, 'groups': {}}
    for key, rows in sorted(groups.items(), key=lambda item: tuple('' if part is None else str(part) for part in item[0])):
        label = '|'.join('' if part is None else str(part) for part in key)
        entry = {'triplets': len(rows), 'arms': {}}
        for arm in ARMS:
            walls = [arms[arm]['response']['wall_s'] for _, _, arms in rows]
            decode = [arms[arm]['response']['timings']['predicted_ms'] for _, _, arms in rows]
            traces = [arms[arm] for _, _, arms in rows if arms[arm].get('verification')]
            values = {
                'wall_mean_s': statistics.mean(walls),
                'decode_mean_ms': statistics.mean(decode),
                'quality_failures': sum(arms[arm]['quality']['passed'] is False for _, _, arms in rows),
                'review_pending': sum(arms[arm]['quality']['passed'] is None for _, _, arms in rows),
                'fallback_events': sum(len(arms[arm].get('fallback_events') or []) for _, _, arms in rows),
                'coverage_mean': statistics.mean(arms[arm]['coverage']['prefix_fraction'] for _, _, arms in rows),
            }
            accepted = [acceptance(row) for row in traces]
            accepted = [value for value in accepted if value is not None]
            values['acceptance_mean'] = statistics.mean(accepted) if accepted else None
            restores = [row['verification']['original_restore_fraction'] for row in traces
                        if row['verification'].get('original_restore_fraction') is not None]
            values['restore_mean'] = statistics.mean(restores) if restores else None
            entry['arms'][arm] = values
        changes = [slowdown(arms) for _, _, arms in rows]
        for arm in ARMS[1:]:
            entry[arm + '_slowdown_mean_pct'] = float(sum((item[arm] for item in changes), Fraction(0)) / len(changes))
        result['groups'][label] = entry
        result['triplets'] += len(rows)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch', type=Path, required=True, help='result/batch 目录')
    parser.add_argument('--cases', type=Path, required=True, help='冻结的 cases.json')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    paired, counts = load_attempts(args.batch)
    complete = triplets(paired)
    cases = json.loads(args.cases.read_text())
    summary = summarize(paired, cases)
    summary['counts'] = counts
    summary['triplets_complete'] = len(complete)
    summary['triplets_partial'] = len(paired) - len(complete)
    summary['fallbacks'] = sum(len(arms[arm].get('fallback_events') or [])
                               for arms in complete.values() for arm in ARMS)
    controller = args.batch / 'summary.json'
    summary['controller'] = json.loads(controller.read_text())['counts'] if controller.exists() else None
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'discovery-summary.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'triplets_complete': summary['triplets_complete'],
                      'triplets_partial': summary['triplets_partial'],
                      'complete_attempts': counts['complete'],
                      'incomplete_attempts': counts['incomplete']}))


if __name__ == '__main__':
    main()
