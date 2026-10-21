#!/usr/bin/env python3
"""固定多轮题集的检查测试。"""
import unittest

import multi_turn_cases as cases


class CasesTest(unittest.TestCase):
    def test_fixed_set_shape(self):
        items = cases.read_cases()
        self.assertEqual(len(items), 6)
        self.assertEqual(cases.planned_turns(items), 24)
        identifiers = [c['conversation_id'] for c in items]
        self.assertEqual(len(set(identifiers)), len(identifiers))

    def test_read_cases_returns_a_copy(self):
        first = cases.read_cases()
        first[0]['turns'][0]['user'] = 'changed'
        self.assertNotEqual(cases.read_cases()[0]['turns'][0]['user'], 'changed')

    def test_correct_answers_pass(self):
        turn = cases.CONVERSATIONS[0]['turns'][0]
        result = cases.assess(turn, '合计 108 台。')
        self.assertTrue(result['passed'])
        self.assertEqual(len(result['failures']), 0)

    def test_wrong_number_fails(self):
        turn = cases.CONVERSATIONS[0]['turns'][0]
        result = cases.assess(turn, '合计 107 台。')
        self.assertFalse(result['passed'])
        self.assertEqual(result['failures'][0]['kind'], 'require')

    def test_number_match_rejects_longer_number(self):
        turn = cases.CONVERSATIONS[0]['turns'][0]
        self.assertFalse(cases.assess(turn, '合计 1080 台。')['passed'])

    def test_forbidden_pattern_fails(self):
        turn = cases.CONVERSATIONS[5]['turns'][0]
        self.assertFalse(cases.assess(turn, 'L01 写的是北岭站 48 台。')['passed'])

    def test_empty_answer_fails(self):
        turn = cases.CONVERSATIONS[1]['turns'][0]
        self.assertFalse(cases.assess(turn, '   ')['passed'])

    def test_state_turn_needs_earlier_fact(self):
        turn = cases.CONVERSATIONS[0]['turns'][3]
        self.assertFalse(cases.assess(turn, '共 109 台。')['passed'])
        self.assertTrue(cases.assess(turn, '共 109 台，负责人林岚。')['passed'])


if __name__ == '__main__':
    unittest.main()
