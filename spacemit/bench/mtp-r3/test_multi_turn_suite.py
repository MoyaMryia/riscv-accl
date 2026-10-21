#!/usr/bin/env python3
"""多轮入口的隔离与门槛测试；不启动真实服务器。"""
import unittest

import multi_turn_cases as cases
import multi_turn_suite as suite

ANSWERS = {
    'site_totals': ['108', '109', '林岚', '共 109 台，负责人林岚。'],
    'inventory': ['70', '不需要', '53', '需要，库存 53 件。'],
    'policy_versions': ['15', '30', '不符合', 'V2.0'],
    'meeting_gap': ['30', '冲突', '冲突', '10:00'],
    'duration_math': ['150', '3 小时 15 分钟', '195', '4'],
    'doc_citations': ['南湾站 36 台，L02。', '108', 'L03', '合计 108 台，引用 L01 至 L03。'],
}


def reply(answer, prompt_count, cache_prompt=False, finish='stop'):
    return {'payload': {}, 'prompt_count': prompt_count, 'response': {
        'answer': answer, 'ttft_s': 0.5, 'wall_s': 1.0, 'finish_reason': finish,
        'reasoning_text': '', 'server_slot': 0,
        'usage': {'prompt_tokens': prompt_count,
                  'completion_tokens': 8,
                  'prompt_tokens_details': {'cached_tokens': 0}},
        'timings': {'prompt_n': prompt_count, 'predicted_n': 8,
                    'prompt_ms': 100.0, 'predicted_ms': 200.0}}}


class FakeClient:
    """按预设答案回答固定多轮会话。"""

    def __init__(self, conversation_id, fail_at=None, error_at=None):
        self.max_tokens = 1024
        self.cache_prompt = False
        self.answers = list(ANSWERS[conversation_id])
        self.fail_at = fail_at
        self.error_at = error_at
        self.calls = 0

    def ask(self, messages):
        self.calls += 1
        if self.error_at == self.calls:
            raise RuntimeError('injected worker failure')
        index = self.calls - 1
        answer = self.answers[index]
        if self.fail_at == self.calls:
            answer = '错误回答'
        prompt_count = sum(len(m['content']) for m in messages)
        return reply(answer, prompt_count)


class ConversationTest(unittest.TestCase):
    def setUp(self):
        self.cases = cases.read_cases()

    def test_all_answers_pass(self):
        results = [suite.run_conversation(FakeClient(c['conversation_id']), c)
                   for c in self.cases]
        summary = suite.summarize(results)
        self.assertTrue(summary['gate_passed'])
        self.assertEqual(summary['counts'], {'passed': 6, 'failed': 0, 'incomplete': 0})
        self.assertEqual(summary['turns_completed'], 24)
        self.assertEqual(summary['checks_passed'], summary['checks_total'])

    def test_failed_turn_stops_only_that_conversation(self):
        client = FakeClient('site_totals', fail_at=2)
        result = suite.run_conversation(client, self.cases[0])
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['turns_completed'], 2)
        self.assertEqual(client.calls, 2)
        self.assertEqual(result['failure']['turn'], 2)
        other = suite.run_conversation(FakeClient('inventory'), self.cases[1])
        self.assertEqual(other['status'], 'passed')
        summary = suite.summarize([result, other])
        self.assertFalse(summary['gate_passed'])
        self.assertEqual(summary['counts'], {'passed': 1, 'failed': 1, 'incomplete': 0})

    def test_worker_error_marks_incomplete(self):
        client = FakeClient('inventory', error_at=1)
        result = suite.run_conversation(client, self.cases[1])
        self.assertEqual(result['status'], 'incomplete')
        self.assertEqual(result['turns_completed'], 0)
        self.assertIn('injected worker failure', result['failure']['error'])
        self.assertEqual(client.calls, 1)

    def test_summary_requires_every_conversation(self):
        passed = suite.run_conversation(FakeClient('site_totals'), self.cases[0])
        incomplete = {'conversation_id': 'other', 'status': 'incomplete',
                      'turns_planned': 4, 'turns_completed': 0,
                      'checks_passed': 0, 'checks_total': 0}
        self.assertFalse(suite.summarize([passed, incomplete])['gate_passed'])


class ValidateTurnTest(unittest.TestCase):
    def test_accepts_natural_stop(self):
        metrics = suite.validate_turn(reply('ok', 10)['response'], 10, 1024, False)
        self.assertEqual(metrics['completion_tokens'], 8)

    def test_rejects_output_limit(self):
        with self.assertRaises(ValueError):
            suite.validate_turn(reply('ok', 10, finish='length')['response'], 10, 1024, False)

    def test_rejects_cache_reuse_when_disabled(self):
        response = reply('ok', 10)['response']
        response['usage']['prompt_tokens_details']['cached_tokens'] = 7
        with self.assertRaises(ValueError):
            suite.validate_turn(response, 10, 1024, False)
        self.assertEqual(suite.validate_turn(response, 10, 1024, True)['cached_tokens'], 7)

    def test_rejects_count_mismatch(self):
        with self.assertRaises(ValueError):
            suite.validate_turn(reply('ok', 10)['response'], 11, 1024, False)


class FakeChat:
    def __init__(self, prompt_count):
        self.prompt_count = prompt_count

    def request_body(self, messages, model, slot, max_tokens):
        return {'messages': messages}

    def count_prompt_tokens(self, url, payload, timeout):
        return self.prompt_count

    def complete(self, url, payload, timeout, display=True, guard=None):
        return reply('ok', self.prompt_count)['response']


class FitTest(unittest.TestCase):
    def test_rejects_turn_that_cannot_fit(self):
        client = suite.HttpClient(FakeChat(12000), 'http://x', 'local', 1024, 10, 12288)
        with self.assertRaises(ValueError):
            client.ask([{'role': 'user', 'content': 'x'}])

    def test_accepts_turn_that_fits(self):
        client = suite.HttpClient(FakeChat(100), 'http://x', 'local', 1024, 10, 12288)
        self.assertEqual(client.ask([{'role': 'user', 'content': 'x'}])['prompt_count'], 100)


if __name__ == '__main__':
    unittest.main()
