#!/usr/bin/env python3
"""验证合成诊断题目和独立代码 gold。"""
from pathlib import Path
import re
import unittest

import discovery_cases

QUALITY_PATH = Path(__file__).resolve().parents[2] / 'release-candidate/tests/quality.py'


class DiscoveryCasesTest(unittest.TestCase):
    def test_counts_combinations_ids_and_material(self):
        cases = discovery_cases.build_cases()
        self.assertEqual(len(cases), 48)
        counts = {category: sum(case['category'] == category for case in cases)
                  for category in ('code', 'chinese', 'qa', 'long_document')}
        self.assertEqual(counts, {'code': 24, 'chinese': 8, 'qa': 8, 'long_document': 8})
        ids = [case['case_id'] for case in cases]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(re.fullmatch('[a-z0-9]+(?:_[a-z0-9]+)*', item) for item in ids))
        code = [case for case in cases if case['category'] == 'code']
        combos = {(case['metadata']['family'], case['metadata']['prompt_language'], case['metadata']['doc_mode']) for case in code}
        self.assertEqual(len(combos), 24)
        self.assertEqual({case['code_task'] for case in code}, set(discovery_cases.FAMILIES))
        for case in cases:
            self.assertEqual([item['role'] for item in case['messages']], ['system', 'user'])
            self.assertEqual(case['required_citations'], [])
            self.assertIsInstance(case['required_facts'], list)
            material = case['messages'][1]['content'].split('资料：\n', 1)[-1] if case['category'] != 'code' else ''
            if case['category'] != 'code':
                self.assertEqual(case['metadata']['material_chars'], len(material))
            if case['category'] == 'long_document':
                self.assertGreaterEqual(len(material), 500)
                self.assertLessEqual(len(material), 2600)
        lengths = sorted(len(case['messages'][1]['content'].split('资料：\n', 1)[1]) for case in cases if case['category'] == 'long_document')
        self.assertGreaterEqual(lengths[0], 500)
        self.assertGreaterEqual(lengths[3], 1200)
        self.assertGreaterEqual(lengths[-1], 2400)
        normalized = [re.sub(r'\s+', ' ', case['messages'][1]['content']).strip() for case in cases]
        self.assertEqual(len(normalized), len(set(normalized)))

    def test_non_code_assessment_is_unscored(self):
        for case in discovery_cases.build_cases():
            if case['category'] != 'code':
                result = discovery_cases.assess(case, '随意回答', QUALITY_PATH)
                self.assertIsNone(result['passed'])
                self.assertEqual(result['facts'], case['required_facts'])
                self.assertEqual(result['citations'], [])

    def test_reference_implementations_pass_and_wrong_ones_fail(self):
        sources = {
            'stable_unique': 'def stable_unique(items):\n    result = []\n    for item in items:\n        if item not in result: result.append(item)\n    return result\n',
            'window_sums': 'def window_sums(values, width):\n    if not isinstance(width, int) or isinstance(width, bool) or width <= 0: raise ValueError()\n    return [sum(values[i:i + width]) for i in range(len(values) - width + 1)]\n',
            'transpose_rect': 'def transpose_rect(rows):\n    if not rows or not rows[0]:\n        if any(rows): raise ValueError()\n        return []\n    if any(len(row) != len(rows[0]) for row in rows): raise ValueError()\n    return [[row[i] for row in rows] for i in range(len(rows[0]))]\n',
            'interval_union': 'def interval_union(intervals):\n    result = []\n    for start, end in sorted(intervals):\n        if start > end: raise ValueError()\n        if start == end: continue\n        if result and start <= result[-1][1]: result[-1] = (result[-1][0], max(result[-1][1], end))\n        else: result.append((start, end))\n    return result\n',
        }
        wrong = {
            'stable_unique': 'def stable_unique(items):\n    return sorted(set(items))\n',
            'window_sums': 'def window_sums(values, width):\n    return [sum(values[i:i + width]) for i in range(len(values) - width + 1)]\n',
            'transpose_rect': 'def transpose_rect(rows):\n    return [list(row) for row in rows]\n',
            'interval_union': 'def interval_union(intervals):\n    return list(intervals)\n',
        }
        cases = {case['code_task']: case for case in discovery_cases.build_cases() if case['category'] == 'code' and case['metadata']['prompt_language'] == 'zh' and case['metadata']['doc_mode'] == 'none'}
        expected_checks = {'stable_unique': 6, 'window_sums': 13, 'transpose_rect': 8, 'interval_union': 8}
        for family, source in sources.items():
            result = discovery_cases.assess(cases[family], source, QUALITY_PATH)
            self.assertTrue(result['passed'], (family, result))
            self.assertEqual(result['result']['checks'], expected_checks[family])
            self.assertFalse(discovery_cases.assess(cases[family], wrong[family], QUALITY_PATH)['passed'])
        stable_unique_variants = [
            'def stable_unique(items):\n    seen = set()\n    result = []\n    for item in items:\n        if item not in seen:\n            seen.add(item)\n            result.append(item)\n    return result\n',
            'def stable_unique(items):\n    return list(dict.fromkeys(items))\n',
            'def stable_unique(items):\n    if not items:\n        return []\n    try:\n        hash(items[0])\n    except TypeError:\n        raise TypeError("unhashable")\n    seen = set()\n    result = []\n    for item in items:\n        if item not in seen:\n            seen.add(item)\n            result.append(item)\n    return result\n',
        ]
        for source in stable_unique_variants:
            result = discovery_cases.assess(cases['stable_unique'], source, QUALITY_PATH)
            self.assertTrue(result['passed'], result)
            self.assertEqual(result['result']['checks'], 6)
        self.assertFalse(discovery_cases.assess(cases['stable_unique'], wrong['stable_unique'], QUALITY_PATH)['passed'])
        self.assertFalse(discovery_cases.assess(cases['stable_unique'],
            'def stable_unique(items):\n    return items.__class__\n', QUALITY_PATH)['passed'])
        self.assertFalse(discovery_cases.assess(cases['stable_unique'],
            'import os\ndef stable_unique(items):\n    return list(items)\n', QUALITY_PATH)['passed'])
        self.assertFalse(discovery_cases.assess(cases['stable_unique'],
            'def stable_unique(items):\n    seen = set()\n    result = []\n    for item in items:\n        if not hash(item):\n            raise TypeError("bad")\n        if item not in seen:\n            seen.add(item)\n            result.append(item)\n    return result\n', QUALITY_PATH)['passed'])
        self.assertFalse(discovery_cases.assess(cases['stable_unique'], 'def stable_unique(:\n pass', QUALITY_PATH)['passed'])
        self.assertFalse(discovery_cases.assess(cases['stable_unique'], 'def stable_unique(items):\n return missing_name\n', QUALITY_PATH)['passed'])
        self.assertFalse(discovery_cases.assess(cases['stable_unique'], 'def stable_unique(items):\n return stable_unique(items)\n', QUALITY_PATH)['passed'])
        alias = sources['transpose_rect'].replace('    if not rows or not rows[0]:',
            '    if rows == [[7]]: return rows[:]\n    if not rows or not rows[0]:')
        self.assertFalse(discovery_cases.assess(cases['transpose_rect'], alias, QUALITY_PATH)['passed'])
        mutating = sources['window_sums'].replace('raise ValueError()', 'values.append(0); raise ValueError()')
        self.assertFalse(discovery_cases.assess(cases['window_sums'], mutating, QUALITY_PATH)['passed'])


if __name__ == '__main__':
    unittest.main()
