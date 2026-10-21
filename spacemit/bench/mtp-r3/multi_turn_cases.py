#!/usr/bin/env python3
"""固定多轮题集与 v2 逐轮判定。

题集只使用资料中的数字和名称。
判定器保留可解释的事实检查，并把复杂歧义交给人工复核。
"""
import ast
import copy
from decimal import Decimal, localcontext
from fractions import Fraction
import re
import unicodedata

ASSESSMENT_VERSION = 'v2'
SYSTEM = '你是严谨的助手。只依据对话中给出的资料回答。资料没有的信息要说明无法确定。'
DOCUMENT = {
    'L01': {'site': '北岭', 'count': 48},
    'L02': {'site': '南湾', 'count': 36},
    'L03': {'site': '东港', 'count': 24},
}


def expect(kind, name, expected, unit=None):
    """构造有类型的期望值。"""
    item = {'type': kind, 'name': name, 'expected': expected}
    if unit is not None:
        item['unit'] = unit
    return item


CONVERSATIONS = [
    {
        'conversation_id': 'site_totals',
        'category': 'state',
        'turns': [
            {'user': '北岭站有 48 台设备，南湾站有 36 台，东港站有 24 台。'
                     '项目负责人是林岚。三个站合计多少台设备？只回答数字。',
             'require': [expect('number', '设备总数', 108, '台')]},
            {'user': '南湾新增 3 台，北岭报废 2 台。现在三个站合计多少台？只回答数字。',
             'require': [expect('number', '设备总数', 109, '台')]},
            {'user': '项目负责人是谁？只回答姓名。',
             'require': [expect('name', '负责人', '林岚')]},
            {'user': '用一句话同时写出当前设备总数和项目负责人。',
             'require': [expect('number', '设备总数', 109, '台'), expect('name', '负责人', '林岚')]},
        ],
    },
    {
        'conversation_id': 'inventory',
        'category': 'state',
        'turns': [
            {'user': '过滤芯期初库存 80 件，本周入库 24 件，领用 31 件，报损 3 件。'
                     '盘点库存是多少件？只回答数字。',
             'require': [expect('number', '库存', 70, '件')]},
            {'user': '补货阈值是 60 件。按上面的库存，需要补货吗？'
                     '只回答需要或不需要。',
             'require': [expect('restock', '补货', False)]},
            {'user': '如果报损是 20 件而不是 3 件，其他数字不变，库存是多少件？'
                     '只回答数字。',
             'require': [expect('number', '库存', 53, '件')]},
            {'user': '按修正后的库存，需要补货吗？库存是多少件？',
             'require': [expect('restock', '补货', True), expect('number', '库存', 53, '件')]},
        ],
    },
    {
        'conversation_id': 'policy_versions',
        'category': 'state',
        'turns': [
            {'user': '资料：旧版 V1.2 规定告警确认时限 30 分钟，已于 3 月 15 日废止。'
                     '现行 V2.0 规定 15 分钟。现行确认时限是多少分钟？只回答数字。',
             'require': [expect('number', '现行时限', 15, '分钟')]},
            {'user': '旧版 V1.2 的确认时限是多少分钟？只回答数字。',
             'require': [expect('number', '旧版时限', 30, '分钟')]},
            {'user': '如果值班员按 30 分钟确认告警，是否符合现行规定？'
                     '只回答符合或不符合。',
             'require': [expect('compliance', '符合现行规定', False)]},
            {'user': '现行版本号是什么？',
             'require': [expect('version', '现行版本', 'V2.0')]},
        ],
    },
    {
        'conversation_id': 'meeting_gap',
        'category': 'state',
        'turns': [
            {'user': '会议 A 为 09:00 至 10:00，会议 B 为 10:30 至 11:15。'
                     '两场会议之间有多少分钟空档？只回答数字。',
             'require': [expect('number', '空档分钟数', 30, '分钟')]},
            {'user': '若会议 A 延长 45 分钟，会议 B 不变，两场会冲突吗？'
                     '只回答冲突或不冲突。',
             'require': [expect('conflict', '会议冲突', True)]},
            {'user': '若会议 A 保持原时长，会议 B 提前到 09:45，会冲突吗？'
                     '只回答冲突或不冲突。',
             'require': [expect('conflict', '会议冲突', True)]},
            {'user': '会议 A 保持 09:00 至 10:00。会议 B 最早可以在几点开始？'
                     '只回答时间。',
             'require': [expect('time', '最早开始时间', 600)]},
        ],
    },
    {
        'conversation_id': 'duration_math',
        'category': 'state',
        'turns': [
            {'user': '2.5 小时等于多少分钟？只回答数字。',
             'require': [expect('number', '分钟数', 150, '分钟')]},
            {'user': '150 分钟再加 45 分钟，合计多少小时多少分钟？',
             'require': [expect('duration', '合计分钟数', 195)]},
            {'user': '3 小时 15 分钟合计多少分钟？只回答数字。',
             'require': [expect('number', '分钟数', 195, '分钟')]},
            {'user': '每节课 45 分钟，195 分钟最多能排几节完整的课？只回答数字。',
             'require': [expect('number', '完整课时数', 4, '节')]},
        ],
    },
    {
        'conversation_id': 'doc_citations',
        'category': 'state',
        'turns': [
            {'user': '资料片段：L01 北岭站有 48 台设备。L02 南湾站有 36 台设备。'
                     'L03 东港站有 24 台设备。L02 写的是哪个站的多少台设备？',
             'require': [expect('record', '资料内容', 'L02')], 'sources': DOCUMENT},
            {'user': '三个站合计多少台设备？只回答数字。',
             'require': [expect('number', '设备总数', 108, '台')], 'sources': DOCUMENT},
            {'user': '哪一条资料写的是东港站？',
             'require': [expect('citation', '资料编号', 'L03')], 'sources': DOCUMENT},
            {'user': '用一句话写出合计台数，并标出你引用的资料编号。',
             'require': [expect('number', '设备总数', 108, '台')], 'sources': DOCUMENT,
             'format': {'citations': list(DOCUMENT)}},
        ],
    },
]


# 数字按完整词元读取；编号和版本号使用各自的词元规则。
NUMBER = r'(?<![A-Za-z0-9_.])[-+]?\d+(?:\.\d+)?(?![A-Za-z0-9_]|\.\d)'
CITATION = r'(?<![A-Za-z0-9])L\d+(?![A-Za-z0-9])'
VERSION = r'(?<![A-Za-z0-9])V?\d+(?:\.\d+)*(?![A-Za-z0-9]|\.\d)'
UNIT_PATTERN = r'台|件|小时|分钟|分|节|人|秒|天|周|吨|千克|公斤|公里|米|元|时'
NEGATION = r'(?:不是|并非|不为|非|没有|不等于|不应为)\s*$'
UNCERTAIN = (r'无法|不能|不确定|不知道|未提供|未提及|可能|也许|大概|或者|或是|如果|假如|是否|吗|[?？]'
             r'|约|估计|估算|大致|左右|上下|近似|差不多|接近'
             r'|不一定|未必|不见得|不成立|不正确|不准确|说法|声称|所谓|据说|除非'
             r'|不是负责人|并非负责人|不担任负责人'
             r'|(?:不是|并非).{0,6}(?:答案|结果)|(?:答案|结果).{0,6}(?:不对|错误)')
CONTEXT = r'题面|题目|问题|用户|资料|已知|给出|提到|引用|期初|阈值|每节|原先|原始'
POLARITIES = {
    'conflict': (r'不(?:会)?冲突|没有冲突|无冲突|不存在冲突|不重叠|没有重叠|无重叠',
                 r'冲突|重叠'),
    'restock': (r'不需要(?:补货)?|无需(?:补货)?|不用(?:补货)?|不必(?:补货)?',
                r'需要(?:补货)?|必须补货|要补货'),
    'compliance': (r'不符合|不合规|违反', r'符合|合规'),
}
AFFIRMATIVE = r'是|是的|对|对的|会|有|要|正确'
DENIAL = r'否|不是|不|不会|没有|无'
DIGITS = dict(zip('零〇一二两三四五六七八九', (0, 0, 1, 2, 2, 3, 4, 5, 6, 7, 8, 9)))
UNITS = {'十': 10, '百': 100, '千': 1000, '万': 10000}


def read_cases():
    """在入口检查一次题集，返回副本。"""
    cases = copy.deepcopy(CONVERSATIONS)
    if not isinstance(cases, list) or len(cases) < 4:
        raise ValueError('conversations must be a list of at least four items')
    identifiers, total = set(), 0
    for conversation in cases:
        if not isinstance(conversation, dict):
            raise ValueError('conversation must be an object')
        identifier = conversation.get('conversation_id')
        if not isinstance(identifier, str) or re.fullmatch(r'[a-z]+(?:_[a-z]+)*', identifier) is None:
            raise ValueError('conversation identifier is invalid')
        if identifier in identifiers:
            raise ValueError('conversation identifiers are not unique')
        identifiers.add(identifier)
        if not isinstance(conversation.get('category'), str) or not conversation['category']:
            raise ValueError('category is absent')
        turns = conversation.get('turns')
        if not isinstance(turns, list) or not 2 <= len(turns) <= 6:
            raise ValueError('each conversation must have two to six turns')
        total += len(turns)
        for turn in turns:
            if not isinstance(turn, dict) or not isinstance(turn.get('user'), str) or not turn['user'].strip():
                raise ValueError('turn prompt is absent')
            sources = turn.get('sources', {})
            if not isinstance(sources, dict):
                raise ValueError('sources must be an object')
            for key, record in sources.items():
                if not isinstance(key, str) or re.fullmatch(CITATION, key) is None:
                    raise ValueError('source identifier is invalid')
                if (not isinstance(record, dict) or set(record) != {'site', 'count'}
                        or not isinstance(record['site'], str) or not record['site']
                        or type(record['count']) is not int):
                    raise ValueError('source record is invalid')
            require = turn.get('require')
            if not isinstance(require, list) or not require:
                raise ValueError('turn requirements are absent')
            for item in require:
                if (not isinstance(item, dict) or not {'type', 'name', 'expected'} <= item.keys()
                        or item.keys() - {'type', 'name', 'expected', 'unit'}
                        or not isinstance(item['name'], str) or not item['name']):
                    raise ValueError('typed expectation is invalid')
                kind, value = item['type'], item['expected']
                if not isinstance(kind, str) or kind not in EVALUATORS:
                    raise ValueError('expectation type is invalid')
                if 'unit' in item and (kind != 'number' or item['unit'] not in ('台', '件', '分钟', '节')):
                    raise ValueError('numeric unit is invalid')
                if kind in ('number', 'duration', 'time') and type(value) is not int:
                    raise ValueError('numeric expectation must be an integer')
                if kind in POLARITIES and type(value) is not bool:
                    raise ValueError('polarity expectation must be a boolean')
                if kind in ('name', 'version', 'citation', 'record'):
                    if not isinstance(value, str) or not value:
                        raise ValueError('text expectation is invalid')
                if kind == 'version' and re.fullmatch(VERSION, value) is None:
                    raise ValueError('version expectation is invalid')
                if kind in ('citation', 'record') and value not in sources:
                    raise ValueError('expectation refers to an absent source')
            format_spec = turn.get('format', {})
            if (not isinstance(format_spec, dict) or set(format_spec) - {'citations'}
                    or not isinstance(format_spec.get('citations', []), list)
                    or any(not isinstance(ref, str) or ref not in sources
                           for ref in format_spec.get('citations', []))):
                raise ValueError('format expectation is invalid')
    if total < 16:
        raise ValueError('the fixed set has too few turns: ' + str(total))
    return cases


def _chinese_integer(text):
    """把中文整数转换为数值。"""
    if not any(char in UNITS for char in text):
        return int(''.join(str(DIGITS[char]) for char in text))
    total, section, digit = 0, 0, 0
    for char in text:
        if char in DIGITS:
            digit = DIGITS[char]
        elif char == '万':
            total += (section + digit) * UNITS[char]
            section, digit = 0, 0
        else:
            section += (digit or 1) * UNITS[char]
            digit = 0
    return total + section + digit


def _chinese_number(match):
    """转换数词，保留“一共”等固定词。"""
    text = match.group()
    if text == '一' and match.string[match.end():match.end() + 1] in ('共', '起', '致', '样', '定'):
        return text
    sign = '-' if text.startswith('负') else ''
    text = text.removeprefix('负')
    integer, dot, fraction = text.partition('点')
    value = str(_chinese_integer(integer))
    if dot:
        value += '.' + ''.join(str(DIGITS[char]) for char in fraction)
    return sign + value


def _normalize(answer):
    """统一标点、数字和算术符号。"""
    text = unicodedata.normalize('NFKC', answer)
    text = re.sub(r'[\x60_]', '', text.replace('**', ''))
    text = text.translate(str.maketrans({'−': '-', '－': '-', '×': '*', '÷': '/'}))
    text = re.sub(r'负?[零〇一二两三四五六七八九十百千万]+(?:点[零〇一二两三四五六七八九]+)?',
                  _chinese_number, text)
    return re.sub(r'([+-])\s+(?=\d)', r'\1', text)


def _clauses(text):
    """按句子和分句读取声明。"""
    return [part.strip() for part in re.split(r'[。!！?？;；,\n]|(?<!\d)\.(?!\d)', text) if part.strip()]


def _negative(text, start, end):
    """识别词元前的否定和词元后的明确否定。"""
    return bool(re.search(NEGATION, text[:start])
                or re.match(r'\s*(?:台|件|分钟|小时|节|站)?\s*(?:不对|错误|不是|并非|非现行|不符合)', text[end:]))


def _decide(expected, positives, negatives=()):
    """比较全部声明，矛盾声明进入人工复核。"""
    observed = list(dict.fromkeys(positives))
    denied = list(dict.fromkeys(negatives))
    if len(observed) > 1 or (observed and denied):
        return None
    if observed:
        return observed[0] == expected
    return False


def _numbers(text):
    """读取完整数值及其位置。"""
    return [(Decimal(match.group()), match) for match in re.finditer(NUMBER, text)]


def _arithmetic(node, expression):
    """用精确分数计算受限算式；未知语法进入人工复核。"""
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return Fraction(ast.get_source_segment(expression, node))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _arithmetic(node.operand, expression)
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.BinOp):
        left = _arithmetic(node.left, expression)
        right = _arithmetic(node.right, expression)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div) and right:
            return left / right
    raise ValueError('unsupported arithmetic')


def _duration_dimension(node, quantities):
    """计算已解析算式的时长维度；裸数的加法单位随同另一项。"""
    if isinstance(node, ast.Constant):
        return (1 if node.col_offset in quantities else None), True
    if isinstance(node, ast.UnaryOp):
        return _duration_dimension(node.operand, quantities)
    left, left_valid = _duration_dimension(node.left, quantities)
    right, right_valid = _duration_dimension(node.right, quantities)
    valid = left_valid and right_valid
    if isinstance(node.op, (ast.Add, ast.Sub)):
        return (left if left is not None else right), (valid and (left is None or right is None or left == right))
    if left is None and right is None:
        return None, valid
    if isinstance(node.op, ast.Mult):
        return (left or 0) + (right or 0), valid
    return (left or 0) - (right or 0), valid


def _quantity_unit(text, end):
    """读取数值后的单位，支持括号内的单位。"""
    match = re.match(rf'\s*(?:\(\s*)?({UNIT_PATTERN})', text[end:])
    return match[1] if match else None


def _target_numbers(clause, unit):
    """区分目标数量、站点数量和结论前的时长输入。"""
    for value, match in _numbers(clause):
        after = clause[match.end():]
        if re.match(r'\s*(?:个)?站', after):
            continue
        found = _quantity_unit(clause, match.end())
        if (unit == '节' and found in DURATION_FACTORS
                and not re.search(r'答案|结果|商|课时|完整.*课', clause[:match.start()])):
            continue
        yield value, match, found


def _numeric_claims(text, unit):
    """区分目标声明、算式结果和题面引用。"""
    positive, negative, equations, units = [], [], [], []
    ambiguous = False
    for clause in _clauses(text):
        if (re.search(CONTEXT, clause)
                and not re.search(r'合计|总计|总数|计算|共|答案(?:是|为)|最多|能排|可排', clause)):
            continue
        if '=' in clause:
            # 带余数的除法分别检查整数商和余数。
            division = re.search(
                rf'({NUMBER})\s*(?:{UNIT_PATTERN})?\s*/\s*({NUMBER})\s*(?:{UNIT_PATTERN})?\s*='
                rf'\s*({NUMBER})\s*(?:{UNIT_PATTERN})?\s*余(?:数(?:为|是|:)?|下)?\s*({NUMBER})\s*(?:{UNIT_PATTERN})?',
                clause) if unit == '节' else None
            if division and clause.count('=') == 1:
                dividend, divisor, quotient, remainder = map(Decimal, division.groups())
                if dividend < 0 or divisor <= 0:
                    ambiguous = True
                    continue
                computed, computed_remainder = divmod(Fraction(dividend), Fraction(divisor))
                division_units = [_quantity_unit(clause, division.end(index)) for index in range(1, 5)]
                equations.append({'computed': computed, 'claimed': quotient,
                                  'dividend': dividend, 'divisor': divisor, 'quotient': quotient,
                                  'remainder': remainder, 'computed_remainder': computed_remainder,
                                  'units': division_units,
                                  'units_valid': all(found is None or found == wanted for found, wanted
                                                     in zip(division_units, ('分钟', '分钟', '节', '分钟')))})
                (negative if _negative(clause, division.start(), division.end()) else positive).append(quotient)
                rest = clause[:division.start()] + clause[division.end():]
            else:
                units.extend(found for _, match in _numbers(clause)
                             if (found := _quantity_unit(clause, match.end())))
                # 时长在调用前统一为分钟；记录单位位置以检查算式维度。
                quantity_positions, removed = set(), 0

                def strip_unit(match):
                    nonlocal removed
                    quantity_positions.add(match.start() - removed + int(match[1].startswith(('+', '-'))))
                    removed += len(match[0]) - len(match[1])
                    return match[1]

                plain = re.sub(rf'({NUMBER})\s*(?:\(\s*(?:{UNIT_PATTERN})\s*\)|{UNIT_PATTERN})',
                               strip_unit, clause)
                match = re.search(rf'([-+\d.()\s*/]+)=\s*({NUMBER})', plain)
                if match is None or plain.count('=') != 1:
                    ambiguous = True
                    continue
                try:
                    expression = match[1].strip()
                    node = ast.parse(expression, mode='eval').body
                    computed = _arithmetic(node, expression)
                except (SyntaxError, ValueError):
                    ambiguous = True
                    continue
                claimed = Decimal(match[2])
                equation = {'computed': computed, 'claimed': claimed}
                if unit == '分钟':
                    start = match.start(1) + len(match[1]) - len(match[1].lstrip())
                    dimension, valid = _duration_dimension(node, {position - start for position in quantity_positions})
                    if not valid or dimension not in (None, 1):
                        equation['units_valid'] = False
                equations.append(equation)
                (negative if _negative(plain, match.start(), match.end()) else positive).append(claimed)
                rest = plain[:match.start()] + plain[match.end():]
            if _numbers(rest) or re.search(r'[A-Za-z]', re.sub(CITATION, '', rest, flags=re.I)):
                ambiguous = True
            continue
        for value, match, found in _target_numbers(clause, unit):
            if found:
                units.append(found)
            (negative if _negative(clause, match.start(), match.end()) else positive).append(value)
    return positive, negative, equations, ambiguous, units


def _equations_wrong(equations):
    """检查算式结果，并独立检查已声明的余数。"""
    return any(entry['computed'] != entry['claimed'] or not entry.get('units_valid', True)
               or ('remainder' in entry and entry['remainder'] != entry['computed_remainder'])
               for entry in equations)


def _number(item, text, sources):
    unit = item.get('unit')
    if unit == '分钟':
        text = _minute_text(text)
    positive, negative, equations, ambiguous, units = _numeric_claims(text, unit)
    matched = _decide(item['expected'], positive, negative)
    if _equations_wrong(equations):
        matched = False
    elif ambiguous:
        matched = None
    if unit and any(found != unit for found in units):
        matched = False
    return matched, {'values': positive, 'denied': negative, 'equations': equations, 'units': units}


def _polarity(item, text, sources):
    negative, positive = POLARITIES[item['type']]
    values = []
    for clause in _clauses(text):
        if re.fullmatch(AFFIRMATIVE, clause):
            values.append(True)
            continue
        if re.fullmatch(DENIAL, clause):
            values.append(False)
            continue
        for match in re.finditer(f'(?:{negative})|(?:{positive})', clause):
            value = re.fullmatch(negative, match.group()) is None
            # 双重否定与未列出的否定结构交给人工复核。
            if (re.search(r'不|非|无|没', clause[:match.start()])
                    or re.match(r'\s*(?:并|也)?(?:不存在|没有|不成立|不发生|不会发生)',
                                clause[match.end():])):
                return None, {'values': values}
            values.append(value)
    return _decide(item['expected'], values), {'values': values}


def _version_key(value):
    """统一版本号的 V 前缀与末尾零分量。"""
    parts = [int(part) for part in value.upper().removeprefix('V').split('.')]
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    return tuple(parts)


def _literal(item, text, sources):
    kind, expected = item['type'], item['expected']
    pattern = {'version': VERSION, 'citation': rf'(?:{CITATION})|(?:第\s*\d+\s*条)'}.get(
        kind, re.escape(expected))
    positive, negative, ambiguous = [], [], False
    for clause in _clauses(text):
        for match in re.finditer(pattern, clause, re.I):
            if kind == 'name':
                before, after = clause[:match.start()], clause[match.end():]
                if (re.search(r'[\u4e00-\u9fff]$', before)
                        and not re.search(r'(?:负责人(?:是|为)?|姓名(?:是|为)?|答案(?:是|为)?|是|为|由|不是|不为)\s*$', before)):
                    continue
                if (re.match(r'[\u4e00-\u9fff]', after)
                        and not re.match(r'(?:(?:是|为|担任)(?:项目)?负责人|负责|不是|不为)', after)):
                    ambiguous = True
            value = match.group().upper() if kind in ('version', 'citation') else match.group()
            if kind == 'citation' and (ordinal := re.fullmatch(r'第\s*(\d+)\s*条', value)):
                value = 'L' + ordinal[1].zfill(2)
            denied = _negative(clause, match.start(), match.end())
            if kind == 'version' and re.search(r'非现行|不是现行|已废止|旧版|废止版本', clause):
                denied = True
            (negative if denied else positive).append(value)
        if kind == 'name':
            for match in re.finditer(r'负责人(?:是|为|:)?\s*([\u4e00-\u9fff]{2,3})', clause):
                value = match[1].removesuffix('是')
                if value != expected and not value.startswith(('不是', '不为')):
                    positive.append(value)
            for match in re.finditer(r'([\u4e00-\u9fff]{2,3})(?:才)?(?:是|为|担任)(?:项目)?负责人', clause):
                value = match[1].removesuffix('才')
                if value != expected:
                    positive.append(value)
    if kind == 'version':
        matched = _decide(_version_key(expected), [_version_key(value) for value in positive],
                          [_version_key(value) for value in negative])
    else:
        matched = None if ambiguous else _decide(expected, positive, negative)
    observed = {'values': positive, 'denied': negative}
    if kind == 'citation' and not positive and not negative:
        resolved, content = _record(item, text, sources)
        if resolved is True:
            matched = True
            observed['resolved_from_content'] = {'citation': expected, 'content': content}
    return matched, observed


DURATION_FACTORS = {'小时': 60, '分钟': 1, '分': 1, '秒': Fraction(1, 60)}
QUANTITY = rf'({NUMBER})\s*(?:个)?(小时|分钟|分|秒)'
DURATION = rf'(?:{QUANTITY})(?:\s*(?:又|零)?\s*(?![+-])(?:{QUANTITY}))*'


def _minute_text(text):
    """把完整时长转换为分钟，保留其他声明。"""
    def convert(match):
        prefix = '+' if match.group().startswith('+') else ''
        value = sum((Fraction(part[1]) * DURATION_FACTORS[part[2]]
                     for part in re.finditer(QUANTITY, match.group())), Fraction(0))
        denominator = value.denominator
        for factor in (2, 5):
            while denominator % factor == 0:
                denominator //= factor
        if denominator != 1:
            return prefix + f'({value.numerator}/{value.denominator})分钟'
        with localcontext() as context:
            context.prec = len(str(abs(value.numerator))) + len(str(value.denominator)) + 1
            return prefix + str(Decimal(value.numerator) / Decimal(value.denominator)) + '分钟'
    return re.sub(DURATION, convert, text)


def _duration(item, text, sources):
    converted = _minute_text(text)
    positive, negative, equations, ambiguous, units = _numeric_claims(converted, '分钟')
    # 秒产生的非整数分钟保留为完整量，不截取分子或分母。
    fractional = list(re.finditer(r'\(([-+]?\d+)/(\d+)\)分钟', converted))
    if fractional:
        return False, {'minutes': [Fraction(int(match[1]), int(match[2])) for match in fractional], 'denied': negative}
    matched = _decide(item['expected'], positive, negative)
    if ambiguous:
        matched = None
    if _equations_wrong(equations) or any(unit != '分钟' for unit in units):
        matched = False
    return matched, {'minutes': positive, 'denied': negative}


def _time(item, text, sources):
    positive, negative = [], []
    pattern = r'(?<![A-Za-z\d.:])(\d{1,2})(?::(\d{2})|点(?:整|半|[13]刻|(\d{1,2})分?)?)(?![\d.:整半刻分秒])'
    for clause in _clauses(text):
        for match in re.finditer(pattern, clause):
            hour, minute = int(match[1]), int(match[2] or match[3] or 0)
            if '半' in match.group():
                minute = 30
            elif '刻' in match.group():
                minute = 45 if '3刻' in match.group() else 15
            period = re.search(r'(下午|晚上|晚间|夜间|傍晚|上午|早上|凌晨|中午)\s*$', clause[:match.start()])
            if period and 1 <= hour <= 12:
                hour %= 12
                if period[1] in ('下午', '晚上', '晚间', '夜间', '傍晚', '中午'):
                    hour += 12
            value = hour * 60 + minute
            if not 0 <= hour < 24 or not 0 <= minute < 60:
                return False, {'minutes_since_midnight': [value]}
            (negative if _negative(clause, match.start(), match.end()) else positive).append(value)
    return _decide(item['expected'], positive, negative), {'minutes_since_midnight': positive, 'denied': negative}


def _record(item, text, sources):
    expected = sources[item['expected']]
    sites, counts, denied_sites, denied_counts, references, units = [], [], [], [], [], []
    for clause in _clauses(text):
        # 对其他站点的否定说明不改变当前资料的内容。
        clause = re.sub(r'(?:不是|并非)\s*L\d+.*?(?=而是|$)', '', clause, flags=re.I)
        for record in sources.values():
            for match in re.finditer(re.escape(record['site']), clause):
                (denied_sites if _negative(clause, match.start(), match.end()) else sites).append(record['site'])
        for value, match, unit in _target_numbers(clause, '台'):
            (denied_counts if _negative(clause, match.start(), match.end()) else counts).append(value)
            if unit:
                units.append(unit)
        references.extend(match.group().upper() for match in re.finditer(CITATION, clause, re.I)
                          if not _negative(clause, match.start(), match.end()))
    site_match = _decide(expected['site'], sites, denied_sites)
    count_match = _decide(expected['count'], counts, denied_counts)
    matched = _combine([site_match, count_match])
    if references and set(references) != {item['expected']}:
        matched = None if len(set(references)) > 1 else False
    if any(unit != '台' for unit in units):
        matched = False
    return matched, {'sites': sites, 'counts': counts, 'denied_sites': denied_sites,
                     'denied_counts': denied_counts, 'references': references, 'units': units}


EVALUATORS = {
    'number': _number, 'duration': _duration, 'time': _time,
    'name': _literal, 'version': _literal, 'citation': _literal, 'record': _record,
    **{kind: _polarity for kind in POLARITIES},
}


def _combine(values):
    """明确错误优先；其余歧义进入人工复核。"""
    if False in values:
        return False
    if None in values:
        return None
    return True


def _json_numbers(value):
    """把内部十进制数转换为 JSON 数值。"""
    if isinstance(value, (Decimal, Fraction)):
        return int(value) if value == int(value) else float(value)
    if isinstance(value, list):
        return [_json_numbers(entry) for entry in value]
    if isinstance(value, dict):
        return {key: _json_numbers(entry) for key, entry in value.items()}
    return value


def assess(turn, answer):
    """检查回答；passed 为 None 时必须人工复核。"""
    if not isinstance(answer, str):
        raise TypeError('answer must be text')
    text = _normalize(answer)
    # 只移除“题目引文的答案是”中的问题；直接问句进入人工复核。
    text = re.sub(r'["“‘「『][^"“”‘’「」『』\n]*[?？]["”’」』](?=\s*的(?:答案|回答)(?:是|为|:))',
                  '', text)
    sources = turn.get('sources', {})
    checks, warnings = [], []
    uncertain = bool(re.search(UNCERTAIN, text))
    for item in turn['require']:
        matched, observed = EVALUATORS[item['type']](item, text, sources)
        if uncertain:
            matched = None
        expected = sources[item['expected']] if item['type'] == 'record' else item['expected']
        checks.append({'kind': 'require', 'name': item['name'], 'expected': expected,
                       'observed': _json_numbers(observed), 'matched': matched})
    if sources:
        references, denied = [], []
        for match in re.finditer(CITATION, text, re.I):
            target = denied if re.search(NEGATION, text[:match.start()]) else references
            target.append(match.group().upper())
        unknown = sorted(set(references) - sources.keys())
        checks.append({'kind': 'require', 'name': '资料编号有效', 'expected': list(sources),
                       'observed': references, 'matched': not unknown})
        wanted = turn.get('format', {}).get('citations', [])
        if any(ref not in references for ref in wanted):
            warnings.append('资料编号不完整。')
        if any(item['type'] in ('record', 'citation') and item['expected'] not in references
               for item in turn['require']):
            warnings.append('回答未重复资料编号。')
    if '只回答' in turn['user']:
        # 输出长度和解释属于格式提示，不改变事实检查。
        concise = re.fullmatch(r'[-+]?\d+(?:\.\d+)?[。.]?|\d{1,2}:\d{2}|[\u4e00-\u9fff]+', text.strip())
        if concise is None:
            warnings.append('回答含额外单位、说明或其他格式。')
    if uncertain:
        warnings.append('回答包含不确定表述，需人工复核。')
    failures = [check for check in checks if check['matched'] is not True]
    return {'passed': _combine([check['matched'] for check in checks]),
            'checks': checks, 'failures': failures, 'answer_chars': len(answer),
            'assessment_version': ASSESSMENT_VERSION, 'format_warnings': warnings}


def planned_turns(cases):
    """返回计划轮次数。"""
    return sum(len(conversation['turns']) for conversation in cases)
