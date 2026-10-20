#!/usr/bin/env python3
"""生成合成诊断题目并执行隔离代码检查。"""
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from router_cases import CHILD_TIMEOUT, CPU_SECONDS, MEMORY_BYTES, GENERATED_ERRORS
from discovery_materials import build_long_cases

FAMILIES = ('stable_unique', 'window_sums', 'transpose_rect', 'interval_union')


def _case(case_id, category, task, facts, material=None, metadata=None):
    user = task
    if material is not None:
        user += '\n\n资料：\n' + material
    return {
        'case_id': case_id,
        'category': category,
        'messages': [
            {'role': 'system', 'content': '请依据任务和资料作答。资料均为虚构诊断材料。'},
            {'role': 'user', 'content': user},
        ],
        'required_facts': facts,
        'required_citations': [],
        'metadata': metadata or {'material_chars': len(material or '')},
    }


def _code_cases():
    cases = []
    specs = {
        'stable_unique': ('stable_unique(items)', '对可哈希元素保留首次出现顺序，返回新列表且不修改输入。', 'Return a new list of hashable items in first-seen order. Do not modify the input.'),
        'window_sums': ('window_sums(values, width)', '返回列表，包含所有完整连续窗口的和。width 必须是正整数且不能是 bool；否则抛出 ValueError。宽度大于输入长度时返回空列表。不得修改输入。', 'Return a list of sums for all complete consecutive windows. width must be a positive int and not bool, or raise ValueError. Return [] when width exceeds the input length. Do not modify the input.'),
        'transpose_rect': ('transpose_rect(rows)', '转置矩形列表并返回新嵌套列表。空输入或全空行返回 []；不等长行抛出 ValueError。不得修改输入。', 'Transpose a rectangular list into a new nested list. Return [] for empty input or all-empty rows. Raise ValueError for ragged rows. Do not modify the input.'),
        'interval_union': ('interval_union(intervals)', '返回二元 tuple 组成的有序列表，表示合并后的半开区间。合并重叠或接触区间，忽略零长度区间；反向区间抛出 ValueError。不得修改输入。', 'Return a sorted list of two-element tuples for merged half-open intervals. Merge overlap or contact. Ignore zero-length intervals. Raise ValueError for reversed intervals. Do not modify the input.'),
    }
    for family, (signature, zh, en) in specs.items():
        for language in ('zh', 'en'):
            for mode in ('none', 'en', 'zh'):
                if language == 'zh':
                    ending = ' 不要写注释或文档字符串。' if mode == 'none' else (' 写中文文档字符串，说明必要边界条件。' if mode == 'zh' else ' 写英文文档字符串，说明必要边界条件。')
                    task = '只输出纯 Python 源码，不要 imports、类或测试。实现 ' + signature + '。' + zh + ending
                else:
                    ending = ' Do not write comments or docstrings.' if mode == 'none' else (' Include a Chinese docstring with required edge cases.' if mode == 'zh' else ' Include an English docstring with required edge cases.')
                    task = 'Return only pure Python source. Do not use imports, classes, or tests. Implement ' + signature + '. ' + en + ending
                case_id = f'code_{family}_{language}_{mode}'
                case = _case(case_id, 'code', task, ['实现规定函数并满足边界条件', '不得修改输入'], metadata={
                    'family': family, 'prompt_language': language, 'doc_mode': mode, 'material_chars': 0})
                case['code_task'] = family
                cases.append(case)
    return cases


def _text_cases():
    groups = []
    chinese = [
        ('chinese_notice', '请根据资料写一则中文通知，说明变更时间、影响和处理办法。', ['维护时间为 8 月 12 日 20:00 至 20:30', '期间导出暂停，已保存的记录不变', '20:40 后可重新导出'], '青禾档案系统将于 8 月 12 日 20:00 至 20:30维护。维护期间，报表导出暂停，已保存的记录不变。维护结束后，用户可在 20:40 后重新导出。异常请联系值班台，提供任务编号 Q-31。'),
        ('chinese_rewrite', '请把资料改写为简明的内部交接记录，区分已完成和待办。', ['收到 36 份申请', '已核对 32 份', '4 份待补签名', '周五由顾宁复核'], '周三收到申请 36 份。档案组已经核对并通过 32 份。其余编号 A-14、A-19、A-27、A-33 共 4 份缺少签名，暂未通过。周五由顾宁复核补交材料。复核后更新登记表版本 5，不要先把待补项标为完成。'),
        ('chinese_explain', '请向新同事解释资料中的计费规则，并用给定数据算出金额。', ['基础费 18 元', '每页 2 元', '7 页共 32 元', '少于 5 页免基础费的规则不适用'], '本服务按页计费。少于 5 页时免收 18 元基础费；达到 5 页时收取 18 元基础费，每页另收 2 元。此次扫描 7 页，适用基础费规则，金额为 18 加 7 乘 2，即 32 元。付款后系统生成编号 P-208。'),
        ('chinese_summary', '请整理资料中的库存变化和责任人，不要推测缺失数据。', ['期初 90 箱', '入库 24 箱', '发出 31 箱', '结余 83 箱由韩梅盘点'], '仓库 4 月 1 日期初有 90 箱滤芯。4 月 3 日入库 24 箱，单号 R-62；4 月 8 日发出 31 箱，单号 O-17。按账面计算结余 83 箱。韩梅于 4 月 9 日盘点，实点数也是 83 箱。'),
        ('chinese_reply', '请根据资料写客服回复，回答退款时间和查询渠道。', ['退款于 3 个工作日内原路返回', '订单号为 T-5502', '超过期限联系支付组'], '客户订单 T-5502 于 11 月 6 日取消。系统在当日 16:20 提交退款，款项按原支付路径退回，处理时限为 3 个工作日。客户可在订单页查看退款状态；超过时限仍未到账时，联系支付组并提供订单号。'),
        ('chinese_steps', '请按先后顺序整理设备报修流程。', ['先断开电源并贴停用标签', '记录设备号 M-08 和故障时间 09:15', '维修组签收后方可移交'], '设备 M-08 于 09:15 出现异响。操作员先断开电源并贴上停用标签，再登记故障现象和时间。维修组签收工单后，仓管员才能移交设备。维修完成后由操作员复测并在工单记录结果。'),
        ('chinese_compare', '请比较两个班次的产量和差值。', ['甲班 148 件', '乙班 163 件', '乙班多 15 件'], '周二甲班完成 148 件，乙班完成 163 件。两班使用同一批次原料和同一验收标准。统计表按合格品计数，不包含返工中的 6 件。乙班比甲班多 15 件。'),
        ('chinese_policy', '请写一段规则说明，列出适用条件、例外和审批岗位。', ['单笔不超过 500 元可由组长审批', '超过 500 元交部门经理', '紧急采购仍须补录凭证'], '办公耗材单笔采购金额不超过 500 元时，由组长审批；金额超过 500 元时，交部门经理审批。紧急采购可以先电话确认，但经办人须在下一个工作日补录发票和用途。设备资产不适用本规则，应走资产采购流程。'),
    ]
    for x in chinese: groups.append(_case('discover_' + x[0], 'chinese', x[1], x[2], material=x[3]))
    qa = [
        ('qa_route', '计算车辆全程里程并写出算式。', ['全程 36.5 千米'], '车辆从库房到站点行驶 12.8 千米，从站点到客户处行驶 23.7 千米。不计返程。'),
        ('qa_balance', '计算结账后的余额，列出加减过程。', ['余额 146 元'], '账户原有 215 元，收到退款 36 元，支付餐费 72 元，支付车费 33 元。'),
        ('qa_duration', '计算活动总时长，单位为分钟。', ['总时长 85 分钟'], '活动从 13:25 开始，到 15:00 结束。中间休息 10 分钟，题目要求扣除休息。'),
        ('qa_workers', '计算 6 名人员平均分配后的单人数。', ['每人 14 件'], '待检物品 84 件，由 6 名检验员平均分配，每件只检查一次。'),
        ('qa_calendar', '计算租用天数和总费用。', ['租用 4 天', '总费用 180 元'], '设备在 3 月 10 日上午交付，3 月 14 日上午归还。每天租金 45 元，按完整日计费。'),
        ('qa_logic', '判断哪位员工负责周四值班，并给出推理。', ['林负责周四'], '林、周、陈分别值周二、周四、周六中的一天。林不值周二或周六，陈不值周四或周六。每人一天。'),
        ('qa_stock', '计算发货后未预留的可用件数。', ['可用 57 件'], '库存 100 件，预留 18 件，今天发出 25 件。预留数量未包含在发货数中。'),
        ('qa_split', '计算每份金额和余款。', ['每份 27 元', '余 2 元'], '总额 110 元，平均分给 4 人，整数金额平分，余款保留。'),
    ]
    for case_id, task, facts, material in qa: groups.append(_case('discover_' + case_id, 'qa', task, facts, material))
    return groups


def build_cases():
    return _code_cases() + _text_cases() + build_long_cases()


def assess(case, answer, sandbox_path):
    if case['category'] != 'code':
        return {'passed': None, 'facts': case['required_facts'], 'citations': []}
    payload = json.dumps({'source': answer}, ensure_ascii=False)
    command = [sys.executable, '-I', str(Path(__file__).resolve()), '--worker', case['code_task'], str(Path(sandbox_path))]
    import signal
    try:
        completed = subprocess.run(command, input=payload, text=True, capture_output=True, timeout=CHILD_TIMEOUT)
    except subprocess.TimeoutExpired:
        return {'passed': False, 'result': {'checks': 0, 'detail': '资源时限'}}
    if completed.returncode in (-signal.SIGXCPU, -signal.SIGKILL):
        return {'passed': False, 'result': {'checks': 0, 'detail': '资源限制'}}
    if completed.returncode != 0:
        raise RuntimeError('质量检查子进程异常退出：' + str(completed.returncode) + ' ' + completed.stderr[:300])
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError('质量检查子进程输出无效 JSON。') from error
    if not isinstance(result, dict) or not isinstance(result.get('passed'), bool):
        raise RuntimeError('质量检查子进程结果结构无效。')
    return {'passed': result['passed'], 'result': result}


def _worker(family, quality_path):
    import builtins
    import importlib.util
    import resource
    spec = importlib.util.spec_from_file_location('quality_checker', quality_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = json.load(sys.stdin)['source']
    try:
        source = module.extract_code(source)
        tree = module.checked_tree(source)
    except (SyntaxError, ValueError, TypeError) as error:
        print(json.dumps({'passed': False, 'checks': 0, 'detail': type(error).__name__}, ensure_ascii=False))
        return
    resource.setrlimit(resource.RLIMIT_CPU, (CPU_SECONDS, CPU_SECONDS))
    resource.setrlimit(resource.RLIMIT_AS, (MEMORY_BYTES, MEMORY_BYTES))
    namespace = {'__builtins__': {name: getattr(builtins, name) for name in module.SAFE_BUILTINS}}
    try:
        exec(compile(tree, '<generated-source>', 'exec'), namespace)
    except GENERATED_ERRORS as error:
        print(json.dumps({'passed': False, 'checks': 0, 'detail': type(error).__name__}, ensure_ascii=False))
        return
    fn = namespace.get(family)
    if not callable(fn):
        print(json.dumps({'passed': False, 'checks': 0, 'detail': '缺少生成函数'}, ensure_ascii=False))
        return
    import copy
    checks = 0
    passed = True
    def check(args, expected):
        nonlocal checks, passed
        snapshot = copy.deepcopy(args[0])
        checks += 1
        try:
            actual = fn(*args)
        except GENERATED_ERRORS:
            passed = False
            return
        good = actual == expected and args[0] == snapshot and actual is not args[0]
        if good and family == 'transpose_rect':
            good = all(out is not original for out in actual for original in args[0])
        passed = passed and good
    def reject(args):
        nonlocal checks, passed
        snapshot = copy.deepcopy(args[0])
        checks += 1
        try:
            fn(*args)
        except ValueError:
            rejected = True
        except GENERATED_ERRORS:
            rejected = False
        else:
            rejected = False
        passed = passed and rejected and args[0] == snapshot
    if family == 'stable_unique':
        for values, expected in [([3, 1, 3, 2, 1], [3, 1, 2]), ([], []), (['b', 'a', 'b'], ['b', 'a']), ([0, 0, -1], [0, -1]), ([None, 2, None], [None, 2]), ([(1, 2), (1, 2), (0,)], [(1, 2), (0,)])]:
            check((values,), expected)
    elif family == 'window_sums':
        for values, width, expected in [([1, 2, 3, 4], 2, [3, 5, 7]), ([], 1, []), ([5], 1, [5]), ([2, -1, 4], 3, [5]), ([1, 2], 4, []), ([0, 0, 0], 2, [0, 0]), ([0.5, 1.25, -0.25], 2, [1.75, 1.0])]:
            check((values, width), expected)
        for width in (0, -1, True, 1.5, '2', None):
            reject(([1, 2], width))
    elif family == 'transpose_rect':
        for rows, expected in [([[1, 2, 3], [4, 5, 6]], [[1, 4], [2, 5], [3, 6]]), ([], []), ([[], []], []), ([[7]], [[7]]), ([[1, 2], [3, 4], [5, 6]], [[1, 3, 5], [2, 4, 6]]), ([['a', 'b'], ['c', 'd']], [['a', 'c'], ['b', 'd']])]:
            check((rows,), expected)
        reject(([[1, 2], [3]],))
        reject(([[1], []],))
    else:
        for intervals, expected in [([(3, 5), (1, 3)], [(1, 5)]), ([], []), ([(2, 2)], []), ([(5, 8), (1, 4), (3, 6)], [(1, 8)]), ([(0, 1), (2, 3)], [(0, 1), (2, 3)]), ([(-3, 0), (-1, 2)], [(-3, 2)])]:
            check((intervals,), expected)
        reject(([(4, 2)],))
        reject(([[1, 3], [5, 4]],))
    print(json.dumps({'passed': passed, 'checks': checks, 'detail': '固定独立 gold 检查'}, ensure_ascii=False))


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == '--worker':
    _worker(sys.argv[2], sys.argv[3])
