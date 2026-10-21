#!/usr/bin/env python3
"""用独立答案、历史错误和构造反例检查 v2 判定器。"""
import copy
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import multi_turn_cases as cases

FROZEN = Path(os.environ.get(
    'MULTI_TURN_V1_FIXTURE',
    Path(__file__).resolve().parents[2] / 'reports/raw/delivery-multiturn-20261021-115000-r2'))
# 答案和数值来自题面运算；不读取实现中的期望值。
ANSWERS = [
    ('site_totals', ['108', '109', '林岚', '当前共 109 台，负责人是林岚。']),
    ('inventory', ['70', '不需要', '53', '需要补货，库存 53 件。']),
    ('policy_versions', ['15', '30', '不符合', 'V2.0']),
    ('meeting_gap', ['30', '冲突', '冲突', '10:00']),
    ('duration_math', ['150', '3 小时 15 分钟', '195', '4']),
    ('doc_citations', ['南湾站有 36 台设备。', '108', 'L03', '合计 108 台，引用 L01、L02、L03。']),
]
SCALARS = [
    ('site_totals', 0, 108), ('site_totals', 1, 109), ('inventory', 0, 70),
    ('inventory', 2, 53), ('policy_versions', 0, 15), ('policy_versions', 1, 30),
    ('duration_math', 0, 150), ('duration_math', 2, 195), ('duration_math', 3, 4),
]


class CasesTest(unittest.TestCase):
    def setUp(self):
        self.items = cases.read_cases()
        self.turns = {item['conversation_id']: item['turns'] for item in self.items}

    def assess(self, identifier, index, answer):
        result = cases.assess(self.turns[identifier][index], answer)
        self.assertEqual(result['assessment_version'], 'v2')
        self.assertIsInstance(result['format_warnings'], list)
        for check in result['checks']:
            self.assertEqual(check['kind'], 'require')
            self.assertIn('name', check)
            self.assertIn('expected', check)
            self.assertIn('observed', check)
            self.assertTrue(any(check['matched'] is value for value in (True, False, None)))
        self.assertEqual(result['failures'], [check for check in result['checks'] if check['matched'] is not True])
        json.dumps(result, ensure_ascii=False, allow_nan=False)
        return result

    def test_fixed_set_and_all_prompt_bytes(self):
        original = json.loads((FROZEN / 'cases.json').read_text())
        self.assertEqual(len(self.items), 6)
        self.assertEqual(cases.planned_turns(self.items), 24)
        self.assertEqual(len({item['conversation_id'] for item in self.items}), 6)
        self.assertEqual(len(self.items), len(original))
        for current, frozen in zip(self.items, original):
            self.assertEqual(current['conversation_id'], frozen['conversation_id'])
            self.assertEqual(len(current['turns']), len(frozen['turns']))
            for turn, previous in zip(current['turns'], frozen['turns']):
                self.assertEqual(turn['user'].encode(), previous['user'].encode())

    def test_read_cases_returns_a_copy(self):
        self.items[0]['turns'][0]['user'] = 'changed'
        self.items[5]['turns'][0]['sources']['L02']['count'] = 999
        fresh = cases.read_cases()
        self.assertNotEqual(fresh[0]['turns'][0]['user'], 'changed')
        self.assertEqual(fresh[5]['turns'][0]['sources']['L02']['count'], 36)

    def test_all_24_independent_correct_answers(self):
        count = 0
        for identifier, answers in ANSWERS:
            for index, answer in enumerate(answers):
                with self.subTest(identifier=identifier, index=index):
                    result = self.assess(identifier, index, answer)
                    self.assertIs(result['passed'], True, result)
                    self.assertEqual(result['failures'], [])
                    count += 1
        self.assertEqual(count, 24)

    def test_five_verified_probes(self):
        probes = [
            ('meeting_gap', 1, '不冲突', False),
            ('meeting_gap', 2, '不冲突', False),
            ('inventory', 3, '不需要补货，库存 53 件。', False),
            ('doc_citations', 0, '南湾站有 36 台设备。', True),
            ('doc_citations', 0, 'L02 是南湾站，有 36 台；不是 L01 北岭站，也不是 L03 东港站。', True),
        ]
        for identifier, index, answer, expected in probes:
            with self.subTest(answer=answer):
                self.assertIs(self.assess(identifier, index, answer)['passed'], expected)

    def test_original_six_actual_errors(self):
        records = [('2b', 'site_totals', 1), ('2b', 'inventory', 2),
                   ('2b', 'meeting_gap', 1), ('2b', 'doc_citations', 1),
                   ('4b', 'inventory', 1), ('4b', 'duration_math', 2)]
        for model, identifier, index in records:
            with self.subTest(model=model, identifier=identifier):
                path = (FROZEN / f'batch/attempts/{model}-{identifier}/result/conversations'
                        / identifier / f'turn-{index}/answer.txt')
                result = self.assess(identifier, index - 1, path.read_text())
                if identifier == 'doc_citations':
                    self.assertIsNot(result['passed'], True)
                else:
                    self.assertIs(result['passed'], False, result)
        result = self.assess('duration_math', 1, '2 小时 15 分钟')
        self.assertEqual(result['checks'][0]['observed']['minutes'], [135])
        self.assertEqual(result['checks'][0]['expected'], 195)

    def test_scalar_values_and_equivalent_notation(self):
        for identifier, index, value in SCALARS:
            for answer in (str(value), f'{value}.0', f'合计：{value}。', f'**{value}**'):
                with self.subTest(value=value, answer=answer):
                    result = self.assess(identifier, index, answer)
                    self.assertIs(result['passed'], True, result)
                    self.assertEqual(result['checks'][0]['observed']['values'], [value])
                    self.assertEqual(result['checks'][0]['expected'], value)
        for answer in ('一百零八', '一百零八台', '１０８．０', '108 台。'):
            result = self.assess('site_totals', 0, answer)
            self.assertIs(result['passed'], True, result)
            self.assertEqual(result['checks'][0]['observed']['values'], [108])

    def test_scalar_boundaries_and_wrong_values(self):
        for identifier, index, value in SCALARS:
            for answer, observed in ((str(value * 10), value * 10), (str(-value), -value),
                                     (f'{value}.5', value + .5), (str(value + 1), value + 1)):
                with self.subTest(value=value, answer=answer):
                    result = self.assess(identifier, index, answer)
                    self.assertIs(result['passed'], False, result)
                    self.assertEqual(result['checks'][0]['observed']['values'], [observed])
        for answer in ('A108', '108A', '108.01', '负一百零八', '不是108', '108台不是总数'):
            self.assertIsNot(self.assess('site_totals', 0, answer)['passed'], True)
        self.assertIs(self.assess('policy_versions', 0, '15小时')['passed'], False)
        result = self.assess('policy_versions', 0, '0.25小时')
        self.assertIs(result['passed'], True)
        self.assertEqual(result['checks'][0]['observed']['values'], [15])
        self.assertIs(self.assess('site_totals', 0, '108件')['passed'], False)
        for answer in ('约108台', '估计108', '108台左右'):
            self.assertIs(self.assess('site_totals', 0, answer)['passed'], None)

    def test_scalar_context_and_conflicting_final_answers(self):
        for identifier, index, value in SCALARS:
            with self.subTest(value=value):
                copied = self.assess(identifier, index, f'题面给出的值是 {value}。')
                self.assertIsNot(copied['passed'], True)
                self.assertEqual(copied['checks'][0]['observed']['values'], [])
                for answer in (f'答案为 {value}。最终答案为 {value + 1}。',
                               f'答案是 {value}，但答案不是 {value}。'):
                    result = self.assess(identifier, index, answer)
                    self.assertIs(result['passed'], None, result)
                result = self.assess(identifier, index, f'题面含有 {value}，无法确定答案。')
                self.assertIs(result['passed'], None)

        self.assertIs(self.assess('site_totals', 0, '108。资料明确合计为107。')['passed'], None)
        self.assertIs(self.assess('site_totals', 0, '根据资料合计108台。')['passed'], True)

    def test_arithmetic_results_are_computed(self):
        matrix = [
            ('site_totals', 0, '48+36+24=108', 108),
            ('site_totals', 1, '108+3-2=109', 109),
            ('inventory', 0, '80+24-31-3=70', 70),
            ('inventory', 2, '80+24-31-20=53', 53),
            ('duration_math', 0, '2.5×60=150', 150),
            ('duration_math', 2, '3×60+15=195', 195),
            ('duration_math', 3, '(195-15)/45=4', 4),
        ]
        for identifier, index, answer, value in matrix:
            with self.subTest(answer=answer):
                result = self.assess(identifier, index, answer)
                self.assertIs(result['passed'], True, result)
                observed = result['checks'][0]['observed']
                self.assertEqual(observed['values'], [value])
                self.assertEqual(observed['equations'], [{'computed': value, 'claimed': value}])
        result = self.assess('site_totals', 0, '48+36+25=108')
        self.assertIs(result['passed'], False)
        self.assertEqual(result['checks'][0]['observed']['equations'], [{'computed': 109, 'claimed': 108}])
        for answer in ('1/0=108', '48+36+24==108', 'x=108', 'x+108=108', '108=108abc'):
            self.assertIs(self.assess('site_totals', 0, answer)['passed'], None)
        result = self.assess('site_totals', 0, '(1/3)*324=108')
        self.assertIs(result['passed'], True)
        self.assertEqual(result['checks'][0]['observed']['equations'], [{'computed': 108, 'claimed': 108}])
        result = self.assess('site_totals', 0, '108.00000000000000001=108')
        self.assertIs(result['passed'], False)
        self.assertIs(self.assess('site_totals', 0, '不是48+36+24=108')['passed'], False)

    def test_negation_and_polarity(self):
        self.assertIs(self.assess('meeting_gap', 1, '没有任何冲突')['passed'], None)
        for index in (1, 2):
            for answer in ('不冲突', '无重叠', '没有冲突', '不会冲突', '没有重叠'):
                result = self.assess('meeting_gap', index, answer)
                self.assertIs(result['passed'], False, result)
                self.assertEqual(result['checks'][0]['observed']['values'], [False])
        for answer in ('不需要补货', '无需补货', '不用补货'):
            result = self.assess('inventory', 3, answer + '，库存53件')
            self.assertIs(result['passed'], False, result)
            self.assertEqual(result['checks'][0]['observed']['values'], [False])
            self.assertIs(self.assess('inventory', 1, answer)['passed'], True)
        for answer in ('冲突，但不冲突', '没有重叠，同时有冲突', '不冲突；冲突'):
            self.assertIs(self.assess('meeting_gap', 1, answer)['passed'], None)
        self.assertIs(self.assess('inventory', 3, '需要补货，但无需补货，库存53件')['passed'], None)
        for answer in ('不一定冲突', '冲突的说法不成立', '冲突，但这不是最终答案',
                       '冲突并不存在', '冲突不存在', '重叠并没有发生'):
            self.assertIs(self.assess('meeting_gap', 1, answer)['passed'], None)
        self.assertIs(self.assess('policy_versions', 2, '符合')['passed'], False)
        self.assertIs(self.assess('policy_versions', 2, '不符合，但符合')['passed'], None)

    def test_short_yes_no_and_ordinal_expressions(self):
        for answer in ('是', '是的', '会', '有'):
            self.assertIs(self.assess('meeting_gap', 1, answer)['passed'], True)
        for answer in ('否', '不是', '不会', '没有'):
            self.assertIs(self.assess('meeting_gap', 1, answer)['passed'], False)
        self.assertIs(self.assess('inventory', 1, '否')['passed'], True)
        for answer in ('第三条', '第3条', 'L03'):
            self.assertIs(self.assess('doc_citations', 2, answer)['passed'], True)
        for answer in ('第四条', '第4条', 'L04'):
            self.assertIs(self.assess('doc_citations', 2, answer)['passed'], False)

    def test_short_name_and_version_expressions(self):
        for answer in ('林岚', '是林岚', '答案是林岚', '负责人为林岚'):
            with self.subTest(answer=answer):
                self.assertIs(self.assess('site_totals', 2, answer)['passed'], True)
        for answer in ('V2.0', 'V2', '2.0', '版本为 2.0', '现行版本 V2.0.0'):
            with self.subTest(answer=answer):
                result = self.assess('policy_versions', 3, answer)
                self.assertIs(result['passed'], True, result)
        for answer in ('V2.01', 'V20', 'V1.2'):
            self.assertIs(self.assess('policy_versions', 3, answer)['passed'], False)

    def test_duration_equivalents_and_computed_minutes(self):
        for answer in ('3小时15分钟', '3 个小时 15 分钟', '195分钟', '3.25小时',
                       '三小时十五分钟', '三点二五小时', '3小时15分'):
            result = self.assess('duration_math', 1, answer)
            self.assertIs(result['passed'], True, result)
            self.assertEqual(result['checks'][0]['observed']['minutes'], [195])
        for answer, value in (('2小时15分钟', 135), ('3小时150分钟', 330),
                              ('1950分钟', 1950), ('-195分钟', -195), ('195.5分钟', 195.5),
                              ('3小时15分钟30秒', 195.5)):
            result = self.assess('duration_math', 1, answer)
            self.assertIs(result['passed'], False, result)
            self.assertEqual(result['checks'][0]['observed']['minutes'], [value])
        self.assertIs(self.assess('duration_math', 1, '195分钟，最终答案是2小时15分钟')['passed'], None)
        self.assertIs(self.assess('duration_math', 1, '3小时15分钟。最后答案为200。')['passed'], None)
        self.assertIs(self.assess('duration_math', 1, '195天')['passed'], False)

    def test_saved_explanations_with_independent_facts(self):
        samples = [
            ('duration_math', 1, '150 + 45 = 195（分钟）\n195 分钟 = 3 小时 15 分钟\n\n合计：3 小时 15 分钟',
             'minutes', [195, 195, 195]),
            ('duration_math', 3, '195 ÷ 45 = 4 余 15\n195 分钟最多能排 4 节完整的课。',
             'values', [4, 4]),
            ('doc_citations', 0, '根据资料片段：\n- L02 南湾站有 36 台设备。\n\n'
             '因此，"L02 写的是哪个站的多少台设备？”的答案是：**南湾站的 36 台设备**。',
             'counts', [36, 36]),
            ('doc_citations', 3, '根据资料编号 L01、L02 和 L03 中关于北岭站、南湾站和东港站的设备数量，'
             '三个站合计为 108 台设备。', 'values', [108]),
        ]
        for identifier, index, answer, key, values in samples:
            with self.subTest(identifier=identifier, index=index):
                result = self.assess(identifier, index, answer)
                self.assertIs(result['passed'], True, result)
                self.assertEqual(result['checks'][0]['observed'][key], values)

    def test_duration_equations_and_unit_dimensions(self):
        for answer in ('150分钟 + 45分钟 = 195分钟', '195分钟 = 3小时15分钟',
                       '3.25小时 = 195（分钟）', '3小时 + 15分钟 = 195分钟',
                       '3 * 60分钟 + 15分钟 = 195分钟',
                       '195分钟 / 45分钟 * 45分钟 = 195分钟'):
            with self.subTest(answer=answer):
                result = self.assess('duration_math', 1, answer)
                self.assertIs(result['passed'], True, result)
                self.assertEqual(result['checks'][0]['observed']['minutes'], [195])
        for answer in ('150 + 44 = 195（分钟）', '195分钟 = 195秒',
                       '195小时 = 195分钟', '195件 = 3小时15分钟',
                       '3小时15秒 = 195分钟', '150分钟 + 45秒 = 195分钟',
                       '3分钟 * 65分钟 = 195分钟', '195分钟 / 1分钟 = 195分钟',
                       '194分钟 + 1分钟 / 1分钟 = 195分钟'):
            with self.subTest(answer=answer):
                self.assertIs(self.assess('duration_math', 1, answer)['passed'], False)
        for answer in ('195分钟=3小时15分钟。最终答案是200分钟。',
                       '195分钟=3小时15分钟。合计不是195分钟。'):
            self.assertIs(self.assess('duration_math', 1, answer)['passed'], None)

    def test_integer_quotient_and_remainder_are_independent(self):
        for answer, quotient, remainder, expected in (
                ('195 ÷ 45 = 4 余 15', 4, 15, True),
                ('195分钟 ÷ 45分钟 = 4节余15分钟', 4, 15, True),
                ('195 ÷ 45 = 4 余 14。最多能排4节。', 4, 14, False),
                ('195 ÷ 45 = 5 余 15。最多能排4节。', 5, 15, False),
                ('195 ÷ 45 = 5 余 -30', 5, -30, False),
                ('195 ÷ 45 = 4 余 15节', 4, 15, False),
                ('195台 ÷ 45分钟 = 4节余15分钟', 4, 15, False)):
            with self.subTest(answer=answer):
                result = self.assess('duration_math', 3, answer)
                self.assertIs(result['passed'], expected, result)
                observed = result['checks'][0]['observed']
                self.assertEqual(observed['values'][0], quotient)
                equation = observed['equations'][0]
                self.assertEqual(equation['quotient'], quotient)
                self.assertEqual(equation['remainder'], remainder)
                self.assertEqual(equation['computed'], 4)
                self.assertEqual(equation['computed_remainder'], 15)
        self.assertIs(self.assess('duration_math', 3, '195÷45=4')['passed'], False)
        self.assertIs(self.assess('duration_math', 3, '195÷45=4余15。最终答案为5节。')['passed'], None)

    def test_input_quantities_and_target_units(self):
        for answer in ('195分钟最多能排4节完整的课。', '195分钟，最多能排4节。',
                       '每节45分钟，共195分钟。答案为4节。'):
            with self.subTest(answer=answer):
                result = self.assess('duration_math', 3, answer)
                self.assertIs(result['passed'], True, result)
                self.assertEqual(result['checks'][0]['observed']['values'], [4])
        for answer in ('三个站合计108台。', '3个站，共108台。'):
            result = self.assess('doc_citations', 3, answer)
            self.assertIs(result['passed'], True, result)
            self.assertEqual(result['checks'][0]['observed']['values'], [108])
        for identifier, index, answer in (
                ('doc_citations', 3, '三个站合计108件。'),
                ('doc_citations', 0, 'L02 南湾站36件设备。'),
                ('duration_math', 3, '答案为4分钟。'),
                ('duration_math', 3, '答案为4分钟。最多排4节。')):
            self.assertIs(self.assess(identifier, index, answer)['passed'], False)
        for identifier, index, answer in (
                ('doc_citations', 3, '三个站合计108台。最终合计107台。'),
                ('duration_math', 3, '195分钟最多排4节。最终答案为5节。')):
            self.assertIs(self.assess(identifier, index, answer)['passed'], None)

    def test_quoted_question_and_direct_questions(self):
        quoted = '“L02写的是哪个站的多少台设备？”的答案是：南湾站36台。'
        self.assertIs(self.assess('doc_citations', 0, quoted)['passed'], True)
        for answer in ('南湾站有36台设备吗？', '“南湾站有36台设备？”',
                       '南湾站36台。难道不是北岭站48台吗？',
                       quoted + '南湾站35台。', quoted + '南湾站不是36台。'):
            with self.subTest(answer=answer):
                self.assertIs(self.assess('doc_citations', 0, answer)['passed'], None)

    def test_all_32_saved_answers_against_manual_reference(self):
        errors = {('2b', 'site_totals', 0), ('2b', 'inventory', 1),
                  ('2b', 'meeting_gap', 0), ('2b', 'doc_citations', 0),
                  ('4b', 'inventory', 0), ('4b', 'duration_math', 1)}
        paths = sorted((FROZEN / 'batch/attempts').glob('*/result/conversations/*/turn-*/answer.txt'))
        self.assertEqual(len(paths), 32)
        correct_count, error_count = 0, 0
        for path in paths:
            identifier = path.parent.parent.name
            model = path.parents[4].name.split('-')[0]
            index = int(path.parent.name.removeprefix('turn-')) - 1
            with self.subTest(model=model, identifier=identifier, index=index):
                result = self.assess(identifier, index, path.read_text())
                if (model, identifier, index) in errors:
                    self.assertIsNot(result['passed'], True, result)
                    error_count += 1
                else:
                    self.assertIs(result['passed'], True, result)
                    correct_count += 1
        self.assertEqual((correct_count, error_count), (26, 6))

    def test_time_equivalents_and_boundaries(self):
        for answer in ('10:00', '１０：００', '十点', '10点整', '最早10:00开始'):
            result = self.assess('meeting_gap', 3, answer)
            self.assertIs(result['passed'], True, result)
            self.assertEqual(result['checks'][0]['observed']['minutes_since_midnight'], [600])
        for answer in ('110:00', '10:000', '10:01', '10:60', '24:00', '不是10:00',
                       '10:00:01', '10点整30分', '10点半', '晚上10:00'):
            self.assertIs(self.assess('meeting_gap', 3, answer)['passed'], False)
        self.assertIs(self.assess('meeting_gap', 3, '10:00或者11:00')['passed'], None)

    def test_name_version_and_citation_negation_boundaries(self):
        for answer in ('林岚是项目负责人', '林岚担任项目负责人', '项目由林岚负责'):
            self.assertIs(self.assess('site_totals', 2, answer)['passed'], True)
        for answer in ('不是林岚', '负责人不是林岚', '林岚不是负责人'):
            self.assertIsNot(self.assess('site_totals', 2, answer)['passed'], True)
        self.assertIs(self.assess('site_totals', 2, '负责人是林岚，负责人是陈晨')['passed'], None)
        self.assertIs(self.assess('site_totals', 2, '陈林岚')['passed'], False)
        for answer in ('林岚和陈晨', '林岚。陈晨才是负责人。'):
            self.assertIs(self.assess('site_totals', 2, answer)['passed'], None)
        for answer in ('V2.01', 'V20', '非现行版本V2.0', 'V2.0不是现行版本', '不是V2.0', '旧版是V2.0'):
            self.assertIs(self.assess('policy_versions', 3, answer)['passed'], False)
        self.assertIs(self.assess('policy_versions', 3, 'V2.0；现行版本V2.01')['passed'], None)
        for answer in ('L030', 'L04', '不是L03'):
            self.assertIs(self.assess('doc_citations', 2, answer)['passed'], False)
        self.assertIs(self.assess('doc_citations', 2, 'L03，但不是L03')['passed'], None)

    def test_sources_and_format_warnings(self):
        result = self.assess('doc_citations', 0, '南湾站36台')
        self.assertIs(result['passed'], True)
        self.assertEqual(result['checks'][0]['expected'], {'site': '南湾', 'count': 36})
        self.assertEqual(result['checks'][0]['observed']['counts'], [36])
        self.assertTrue(result['format_warnings'])
        for answer in ('108', '合计108台，引用L01。'):
            result = self.assess('doc_citations', 3, answer)
            self.assertIs(result['passed'], True, result)
            self.assertTrue(result['format_warnings'])
        for answer in ('合计108台，引用L04', '合计108台，引用L01、L02、L03、L04'):
            self.assertIs(self.assess('doc_citations', 3, answer)['passed'], False)
        self.assertIs(self.assess('doc_citations', 0, '南湾36台，引用L04')['passed'], False)
        self.assertIs(self.assess('doc_citations', 3, '合计108台，引用的是L04不是L03。')['passed'], False)
        self.assertIs(self.assess('doc_citations', 0, '南湾站36台。不是L01而是北岭站48台。')['passed'], None)
        result = self.assess('doc_citations', 2, '东港站有24台设备的那条资料')
        self.assertIs(result['passed'], True)
        self.assertEqual(result['checks'][0]['observed']['resolved_from_content']['citation'], 'L03')
        self.assertTrue(result['format_warnings'])
        self.assertIs(self.assess('doc_citations', 0, 'L01是南湾站36台')['passed'], False)
        self.assertIs(self.assess('doc_citations', 0, 'L02南湾站不是36台')['passed'], False)
        self.assertIs(self.assess('doc_citations', 0, 'L02南湾站36台不是L01或L03')['passed'], True)
        self.assertIs(self.assess('doc_citations', 0, 'L01北岭48台，L02南湾36台，L03东港24台')['passed'], None)
        result = self.assess('site_totals', 0, '合计108台，计算完毕。')
        self.assertIs(result['passed'], True)
        self.assertTrue(result['format_warnings'])
        self.assertIs(self.assess('site_totals', 0, '   ')['passed'], False)
        self.assertIs(self.assess('site_totals', 3, '共109台')['passed'], False)

    def test_schema_rejects_external_input_once(self):
        mutations = [
            lambda items: items[0]['turns'][0].update(require=['108']),
            lambda items: items[0]['turns'][0]['require'][0].update(type='regex'),
            lambda items: items[0]['turns'][0]['require'][0].update(expected=True),
            lambda items: items[1]['turns'][1]['require'][0].update(expected=1),
            lambda items: items[5]['turns'][0]['sources']['L02'].update(count='36'),
            lambda items: items[5]['turns'][0]['require'][0].update(expected='L04'),
            lambda items: items[5]['turns'][3].update(format={'citations': ['L04']}),
        ]
        for mutate in mutations:
            items = copy.deepcopy(self.items)
            mutate(items)
            with patch.object(cases, 'CONVERSATIONS', items), self.assertRaises(ValueError):
                cases.read_cases()
        with self.assertRaisesRegex(TypeError, 'answer must be text'):
            cases.assess(self.turns['site_totals'][0], None)


if __name__ == '__main__':
    unittest.main()
