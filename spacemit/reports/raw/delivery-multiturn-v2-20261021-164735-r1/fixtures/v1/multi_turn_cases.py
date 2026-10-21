#!/usr/bin/env python3
"""固定多轮题集与逐轮判定。

题集只使用资料中给出的数字和名称。
判定只做确定性文本匹配，不使用模型判分。
后续轮次依赖前面轮次的事实，用于检查跨轮状态保持。
"""
import copy
import re

SYSTEM = '你是严谨的助手。只依据对话中给出的资料回答。资料没有的信息要说明无法确定。'


def num(value):
    """匹配独立出现的整数，避免命中更长数字的一部分。"""
    return rf'(?<![\d.]){value}(?![\d.])'


CONVERSATIONS = [
    {
        'conversation_id': 'site_totals',
        'category': 'state',
        'turns': [
            {'user': '北岭站有 48 台设备，南湾站有 36 台，东港站有 24 台。'
                     '项目负责人是林岚。三个站合计多少台设备？只回答数字。',
             'require': [num(108)]},
            {'user': '南湾新增 3 台，北岭报废 2 台。现在三个站合计多少台？只回答数字。',
             'require': [num(109)]},
            {'user': '项目负责人是谁？只回答姓名。',
             'require': ['林岚']},
            {'user': '用一句话同时写出当前设备总数和项目负责人。',
             'require': [num(109), '林岚']},
        ],
    },
    {
        'conversation_id': 'inventory',
        'category': 'state',
        'turns': [
            {'user': '过滤芯期初库存 80 件，本周入库 24 件，领用 31 件，报损 3 件。'
                     '盘点库存是多少件？只回答数字。',
             'require': [num(70)]},
            {'user': '补货阈值是 60 件。按上面的库存，需要补货吗？'
                     '只回答需要或不需要。',
             'require': ['不需要|无需|不用补货']},
            {'user': '如果报损是 20 件而不是 3 件，其他数字不变，库存是多少件？'
                     '只回答数字。',
             'require': [num(53)]},
            {'user': '按修正后的库存，需要补货吗？库存是多少件？',
             'require': ['需要', num(53)]},
        ],
    },
    {
        'conversation_id': 'policy_versions',
        'category': 'state',
        'turns': [
            {'user': '资料：旧版 V1.2 规定告警确认时限 30 分钟，已于 3 月 15 日废止。'
                     '现行 V2.0 规定 15 分钟。现行确认时限是多少分钟？只回答数字。',
             'require': [num(15)]},
            {'user': '旧版 V1.2 的确认时限是多少分钟？只回答数字。',
             'require': [num(30)]},
            {'user': '如果值班员按 30 分钟确认告警，是否符合现行规定？'
                     '只回答符合或不符合。',
             'require': ['不符合|不合规|违反']},
            {'user': '现行版本号是什么？',
             'require': [r'V2\.0|V2']},
        ],
    },
    {
        'conversation_id': 'meeting_gap',
        'category': 'state',
        'turns': [
            {'user': '会议 A 为 09:00 至 10:00，会议 B 为 10:30 至 11:15。'
                     '两场会议之间有多少分钟空档？只回答数字。',
             'require': [num(30)]},
            {'user': '若会议 A 延长 45 分钟，会议 B 不变，两场会冲突吗？'
                     '只回答冲突或不冲突。',
             'require': ['冲突|重叠']},
            {'user': '若会议 A 保持原时长，会议 B 提前到 09:45，会冲突吗？'
                     '只回答冲突或不冲突。',
             'require': ['冲突|重叠']},
            {'user': '会议 A 保持 09:00 至 10:00。会议 B 最早可以在几点开始？'
                     '只回答时间。',
             'require': ['10:00|十点']},
        ],
    },
    {
        'conversation_id': 'duration_math',
        'category': 'state',
        'turns': [
            {'user': '2.5 小时等于多少分钟？只回答数字。',
             'require': [num(150)]},
            {'user': '150 分钟再加 45 分钟，合计多少小时多少分钟？',
             'require': [r'3\s*小时.{0,8}15|195']},
            {'user': '3 小时 15 分钟合计多少分钟？只回答数字。',
             'require': [num(195)]},
            {'user': '每节课 45 分钟，195 分钟最多能排几节完整的课？只回答数字。',
             'require': [num(4)]},
        ],
    },
    {
        'conversation_id': 'doc_citations',
        'category': 'state',
        'turns': [
            {'user': '资料片段：L01 北岭站有 48 台设备。L02 南湾站有 36 台设备。'
                     'L03 东港站有 24 台设备。L02 写的是哪个站的多少台设备？',
             'require': ['南湾', num(36), 'L02'], 'forbid': [r'L01|L03']},
            {'user': '三个站合计多少台设备？只回答数字。',
             'require': [num(108)]},
            {'user': '哪一条资料写的是东港站？',
             'require': ['L03']},
            {'user': '用一句话写出合计台数，并标出你引用的资料编号。',
             'require': [num(108), r'L0[123]']},
        ],
    },
]


def read_cases():
    """返回经过检查的题集副本；结构错误时立即失败。"""
    cases = copy.deepcopy(CONVERSATIONS)
    if not isinstance(cases, list) or len(cases) < 4:
        raise ValueError('conversations must be a list of at least four items')
    identifiers, total = [], 0
    for conversation in cases:
        if not isinstance(conversation, dict):
            raise ValueError('conversation must be an object')
        identifier = conversation.get('conversation_id')
        if not isinstance(identifier, str) or re.fullmatch(r'[a-z]+(?:_[a-z]+)*', identifier) is None:
            raise ValueError('conversation identifier is invalid')
        if identifier in identifiers:
            raise ValueError('conversation identifiers are not unique')
        identifiers.append(identifier)
        if not isinstance(conversation.get('category'), str) or not conversation['category']:
            raise ValueError('category is absent')
        turns = conversation.get('turns')
        if not isinstance(turns, list) or not 2 <= len(turns) <= 6:
            raise ValueError('each conversation must have two to six turns')
        total += len(turns)
        for turn in turns:
            if not isinstance(turn, dict) or not isinstance(turn.get('user'), str) or not turn['user'].strip():
                raise ValueError('turn prompt is absent')
            require = turn.get('require')
            if not isinstance(require, list) or not require:
                raise ValueError('turn requirements are absent')
            for key in ('require', 'forbid'):
                for pattern in turn.get(key, []):
                    if not isinstance(pattern, str) or not pattern:
                        raise ValueError('invalid pattern')
                    re.compile(pattern)
    if total < 16:
        raise ValueError('the fixed set has too few turns: ' + str(total))
    return cases


def assess(turn, answer):
    """按逐轮要求判定一个回答，返回可复核的匹配结果。"""
    if not isinstance(answer, str):
        raise TypeError('answer must be text')
    text = re.sub(r'[`*_]', '', answer)
    checks = []
    for pattern in turn['require']:
        checks.append({'pattern': pattern, 'kind': 'require',
                       'matched': bool(re.search(pattern, text, re.I | re.S))})
    for pattern in turn.get('forbid', []):
        checks.append({'pattern': pattern, 'kind': 'forbid',
                       'matched': bool(re.search(pattern, text, re.I | re.S))})
    failures = [c for c in checks
                if (c['kind'] == 'require' and not c['matched'])
                or (c['kind'] == 'forbid' and c['matched'])]
    return {'passed': not failures, 'checks': checks,
            'failures': failures, 'answer_chars': len(answer)}


def planned_turns(cases):
    """返回计划轮次数。"""
    return sum(len(c['turns']) for c in cases)
