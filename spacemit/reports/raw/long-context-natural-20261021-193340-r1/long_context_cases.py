#!/usr/bin/env python3
"""用本地官方分词器构造六个长短对照案例，保存完整原文。"""
import argparse
import copy
import json
from pathlib import Path

MAX_TOKENS = 256
TOKEN_TOLERANCE = 64
LEVELS = {
    'short': {'target_tokens': None, 'token_tolerance': TOKEN_TOLERANCE, 'context': 12288, 'deadline_s': 900},
    '16k': {'target_tokens': 16384, 'token_tolerance': TOKEN_TOLERANCE, 'context': 20480, 'deadline_s': 10800},
    '32k': {'target_tokens': 32768, 'token_tolerance': TOKEN_TOLERANCE, 'context': 36864, 'deadline_s': 21600},
}
MEMORY_LIMITS = {'startup_available_bytes': 8 * 1024**3,
                 'running_available_bytes': 1024**3,
                 'rss_bytes': 12 * 1024**3, 'sample_interval_s': 1}
SYSTEM = '请仅依据资料直接回答问题。保留各字段对应关系，不输出思考过程。'
TASKS = {
    'lookup': {
        'facts': ['资料甲：A17 的设备数为 137 台。',
                  '资料乙：B29 的负责人为顾青禾。',
                  '资料丙：C43 的巡检周期为 19 天。'],
        'question': '问题：A17 的设备数、B29 的负责人、C43 的巡检周期分别是什么？',
        'reference': {'设备数': '137 台', '负责人': '顾青禾', '巡检周期': '19 天',
                      '依据': '资料甲给出 A17 设备数；资料乙给出 B29 负责人；资料丙给出 C43 巡检周期。'},
    },
    'revision': {
        'facts': ['版本记录一：P17 生效版本为 V3，负责人为梁知远，确认期限为 2027-03-11。',
                  '版本记录二：P17 更新为 V8，负责人为沈若宁，确认期限为 2027-05-23；替代记录一全部字段。',
                  '版本记录三：P17 更新为 V12，负责人为陶云舟，确认期限为 2027-09-17；替代记录二全部字段。'],
        'question': '问题：按记录顺序更新后，P17 最终生效版本、负责人、确认期限分别是什么？',
        'reference': {'版本': 'V12', '负责人': '陶云舟', '确认期限': '2027-09-17',
                      '依据': '记录三替代记录二全部字段；记录二此前替代记录一全部字段。'},
    },
}


def payload_settings():
    """返回固定请求参数。"""
    return {'model': 'local', 'id_slot': 0, 'stream': True, 'temperature': 0,
            'seed': 42, 'max_tokens': MAX_TOKENS, 'cache_prompt': False,
            'chat_template_kwargs': {'enable_thinking': False},
            'stream_options': {'include_usage': True}, 'verbose': True}


def filler_limit(level):
    """返回档位的填充行数上限。"""
    return (LEVELS[level]['target_tokens'] or 0) * 2


def messages_for(task, filler_lines):
    """把关键记录分布在资料开头、中间和末尾。"""
    facts = TASKS[task]['facts']
    filler = [f'巡检资料 Z{i:06d}：状态正常，归档至独立资料库。' for i in range(filler_lines)]
    middle = filler_lines // 2
    document = '\n'.join([facts[0], *filler[:middle], facts[1], *filler[middle:], facts[2]])
    return [{'role': 'system', 'content': SYSTEM},
            {'role': 'user', 'content': document + '\n\n' + TASKS[task]['question']}]


def check_count(count, level):
    """检查完整输入的词元数及输出空间。"""
    spec = LEVELS[level]
    if type(count) is not int or count <= 0 or count + MAX_TOKENS > spec['context']:
        raise ValueError('输入词元数无效或上下文空间不足')
    target = spec['target_tokens']
    if target is not None and abs(count - target) > spec['token_tolerance']:
        raise ValueError('长输入词元数超出目标范围')


def generate_cases(count_tokens):
    """按完整消息词元数二分填充行数，不调用推理。"""
    result = []
    for task in TASKS:
        for level, spec in LEVELS.items():
            def measure(lines):
                messages = messages_for(task, lines)
                count = count_tokens(messages)
                return lines, messages, count

            chosen = measure(0)
            target = spec['target_tokens']
            if target is not None:
                low, high = 0, 1
                upper = measure(high)
                while upper[2] < target:
                    low, high = high, high * 2
                    upper = measure(high)
                candidates = [chosen, upper]
                while high - low > 1:
                    mid = (low + high) // 2
                    item = measure(mid)
                    candidates.append(item)
                    if item[2] < target:
                        low = mid
                    else:
                        high = mid
                chosen = min(candidates, key=lambda item: (abs(item[2] - target), item[0]))
            lines, messages, count = chosen
            check_count(count, level)
            result.append({'case_id': task + '-' + level, 'task': task, 'level': level,
                           'messages': messages, 'filler_lines': lines, 'local_token_count': count,
                           'reference': copy.deepcopy(TASKS[task]['reference']),
                           'payload_settings': payload_settings()})
    return result


def read_cases(path):
    """在文件入口一次验证类型、矩阵、原文和固定参数。"""
    cases = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(cases, list) or len(cases) != len(TASKS) * len(LEVELS):
        raise ValueError('案例必须组成完整六项矩阵')
    seen = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError('案例必须为对象')
        task, level, identifier = case.get('task'), case.get('level'), case.get('case_id')
        if not isinstance(task, str) or task not in TASKS or not isinstance(level, str) or level not in LEVELS:
            raise ValueError('任务或档位无效')
        if identifier != task + '-' + level or identifier in seen:
            raise ValueError('案例标识无效或重复')
        seen.add(identifier)
        lines = case.get('filler_lines')
        if type(lines) is not int or not 0 <= lines <= filler_limit(level):
            raise ValueError('填充行数无效')
        if case.get('messages') != messages_for(task, lines):
            raise ValueError('案例原文与构造规则不同')
        if case.get('reference') != TASKS[task]['reference']:
            raise ValueError('参考事实不同')
        if json.dumps(case.get('payload_settings'), sort_keys=True) != json.dumps(payload_settings(), sort_keys=True):
            raise ValueError('请求参数的类型或值不同')
        check_count(case.get('local_token_count'), level)
    return cases


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tokenizer', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(str(args.tokenizer), local_files_only=True)

    def count(messages):
        return len(tokenizer.apply_chat_template(messages, enable_thinking=False,
                                                 add_generation_prompt=True, tokenize=True))

    cases = generate_cases(count)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(cases, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
