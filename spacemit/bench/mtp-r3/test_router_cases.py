#!/usr/bin/env python3
"""验证固定题目、材料和代码题独立 gold。"""
from pathlib import Path
import unittest

import router_cases

QUALITY_PATH = Path(__file__).resolve().parents[2] / 'release-candidate/tests/quality.py'


class RouterCasesTest(unittest.TestCase):
    def test_case_shape_and_independence(self):
        cases = router_cases.build_cases()
        self.assertEqual(len(cases), 12)
        self.assertEqual(len({case['case_id'] for case in cases}), 12)
        for category in ('code', 'chinese', 'qa', 'long_document'):
            self.assertEqual(len([case for case in cases if case['category'] == category]), 3)
        for case in cases:
            self.assertEqual([message['role'] for message in case['messages']], ['system', 'user'])
            self.assertIsInstance(case['required_facts'], list)
            self.assertEqual(case['required_citations'], [])
            self.assertIn('evidence', case['metadata'])
            self.assertEqual('code_task' in case, case['category'] == 'code')
            if case['category'] == 'code':
                self.assertEqual(case['code_task'], case['case_id'])
            else:
                self.assertIn('资料：', case['messages'][1]['content'])
                assessed = router_cases.assess(case, '任意回答', QUALITY_PATH)
                self.assertIsNone(assessed['passed'])
                self.assertEqual(assessed['facts'], case['required_facts'])
                self.assertEqual(assessed['citations'], [])
            if case['category'] == 'chinese':
                self.assertIn('约 200~350 汉字', case['messages'][1]['content'])
        for case in cases:
            if case['category'] == 'long_document':
                material = case['messages'][1]['content'].split('资料：\n', 1)[1]
                self.assertGreaterEqual(len(material), 3000)
                self.assertLessEqual(len(material), 4500)
                self.assertLess(len(material) + 2048, 12288)

    def test_gold_arithmetic_and_evidence(self):
        cases = {case['case_id']: case for case in router_cases.build_cases()}
        self.assertEqual(8.4 + 15.1, 23.5)
        self.assertEqual(168 - 29 - 18, 121)
        self.assertEqual((11 * 60) + 30 - (10 * 60 + 15), 75)
        archive = cases['long_archive']['messages'][1]['content']
        for text in ('1,002 件', '1,136 件', '1,238 件', '1,354 件', '已包含后补确认的 4 件', '不再增加财务确认数', '复核状态'):
            self.assertIn(text, archive)
        self.assertEqual(1002 + 1136 + 1238 + 1354, 4730)
        water = cases['long_water']['messages'][1]['content']
        for text in ('8、14、16、12', '季度样本数均为 120', '减去 0.2'):
            self.assertIn(text, water)
        self.assertEqual(120 * 4, 480)
        self.assertEqual((8 + 14 + 16 + 12) / 4, 12.5)
        library = cases['long_library']['messages'][1]['content']
        for text in ('880 册', '910 册', '960 册', '970 册', 'L-204', '按实体交还时间确定', '包含 25 册自助柜离线归还和 6 册跨年扫描记录'):
            self.assertIn(text, library)
        self.assertEqual(880 + 910 + 960 + 970, 3720)

    def test_code_assessment_gold_results(self):
        good = {
            'clamp_values': 'def clamp_values(values, lower, upper):\n    if lower > upper: raise ValueError()\n    return [max(lower, min(value, upper)) for value in values]\n',
            'count_items': 'def count_items(items):\n    result = {}\n    for item in items: result[item] = result.get(item, 0) + 1\n    return result\n',
            'pairwise_deltas': 'def pairwise_deltas(values):\n    return [values[i + 1] - values[i] for i in range(len(values) - 1)]\n',
        }
        bad = {
            'clamp_values': 'def clamp_values(values, lower, upper):\n    return values\n',
            'count_items': 'def count_items(items):\n    return {}\n',
            'pairwise_deltas': 'def pairwise_deltas(values):\n    return [values[i] - values[i + 1] for i in range(len(values) - 1)]\n',
        }
        cases = {case['case_id']: case for case in router_cases.build_cases()}
        for case_id in good:
            result = router_cases.assess(cases[case_id], good[case_id], QUALITY_PATH)
            self.assertTrue(result['passed'], (case_id, result))
            self.assertEqual(result['result']['checks'], 15 if case_id == 'clamp_values' else 14)
            result = router_cases.assess(cases[case_id], bad[case_id], QUALITY_PATH)
            self.assertFalse(result['passed'], (case_id, result))
            self.assertGreaterEqual(result['result']['checks'], 12)

    def test_generated_assertion_and_default_expression_are_quality_failures(self):
        cases = {case['case_id']: case for case in router_cases.build_cases()}
        for case_id, source in (
            ('count_items', 'def count_items(items):\n    assert False\n'),
            ('pairwise_deltas', 'def pairwise_deltas(values, extra=1/0):\n    return []\n')):
            self.assertFalse(router_cases.assess(cases[case_id], source, QUALITY_PATH)['passed'])

    def test_worker_internal_error_propagates(self):
        case = {'case_id': 'unknown_internal_bug', 'category': 'code'}
        with self.assertRaisesRegex(RuntimeError, '子进程异常退出'):
            router_cases.assess(case, 'def unused(): pass', QUALITY_PATH)

    def test_missing_sandbox_does_not_fall_back(self):
        case = {'case_id': 'clamp_values', 'category': 'code'}
        with self.assertRaisesRegex(RuntimeError, '子进程异常退出'):
            router_cases.assess(case, 'def unused(): pass', QUALITY_PATH / 'missing.py')


if __name__ == '__main__':
    unittest.main()
