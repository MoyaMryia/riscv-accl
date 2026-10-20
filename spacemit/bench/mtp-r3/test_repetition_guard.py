"""检查退化文本守卫与请求中止路径。"""
import importlib.util
from pathlib import Path
import unittest
from unittest import mock

import repetition_guard
import trace_cases

HERE = Path(__file__).resolve().parent
CHAT = HERE.parents[1] / 'serve/cached-document-chat.py'
LINE = '- 若输入区间列表包含任何区间，则返回非空列表，除非所有区间均为空。' * 1


class GuardTests(unittest.TestCase):
    def test_three_identical_lines_abort_and_two_do_not(self):
        guard = repetition_guard.RepeatGuard(window=3, min_chars=20)
        guard.feed(LINE + '\n')
        guard.feed(LINE + '\n')
        with self.assertRaises(repetition_guard.DegenerateOutput):
            guard.feed(LINE + '\n')

    def test_alternating_lines_abort(self):
        guard = repetition_guard.RepeatGuard(window=3, min_chars=20)
        a = 'if not all(interval[0] <= interval[1] for interval in intervals):'
        b = 'raise ValueError("Each interval must be non-empty")'
        guard.feed((a + '\n' + b + '\n') * 2)
        with self.assertRaises(repetition_guard.DegenerateOutput):
            guard.feed(a + '\n' + b + '\n')

    def test_three_line_block_aborts(self):
        guard = repetition_guard.RepeatGuard(window=3, min_chars=20)
        block = ['first long line of the block', 'second long line of the block',
                 'third long line of the block']
        guard.feed('\n'.join(block * 2) + '\n')
        with self.assertRaises(repetition_guard.DegenerateOutput):
            guard.feed('\n'.join(block) + '\n')

    def test_short_lines_and_changes_reset_the_count(self):
        guard = repetition_guard.RepeatGuard(window=3, min_chars=20)
        guard.feed('return x\n' * 5)
        guard.feed(LINE + '\n')
        guard.feed('other line here that differs\n')
        guard.feed(LINE + '\n')
        guard.feed(LINE + '\n')

    def test_invalid_settings_are_rejected(self):
        for window, min_chars in ((1, 20), (3, 3), (True, 20), (3, '20')):
            with self.subTest(window=window, min_chars=min_chars):
                with self.assertRaises(ValueError):
                    repetition_guard.RepeatGuard(window=window, min_chars=min_chars)

    def test_chat_stops_streaming_when_guard_trips(self):
        spec = importlib.util.spec_from_file_location('guard_chat', CHAT)
        chat = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(chat)
        def events():
            for _ in range(5):
                yield ('data: ' + '{"choices":[{"delta":{"content":"' + LINE.replace('"', '') + '\\n"}}]}' + '\n').encode()
            yield b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n'
            yield b'data: [DONE]\n'
        class Sock:
            def __init__(self): self.shutdowns = []
            def shutdown(self, how): self.shutdowns.append(how)
        class Raw:
            def __init__(self): self._sock = Sock()
        class Response:
            headers = {'X-Decode-Route': 'direct'}
            closed = False
            def __init__(self): self.fp = type('Fp', (), {'raw': Raw()})()
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def __iter__(self): return iter(events())
            def close(self): self.closed = True
        response = Response()
        guard = repetition_guard.RepeatGuard(window=3, min_chars=20)
        with mock.patch.object(chat.urllib.request, 'urlopen', return_value=response):
            with self.assertRaises(repetition_guard.DegenerateOutput):
                chat.complete('http://unit', {'messages': []}, 1, display=False, guard=guard)
        self.assertEqual(response.fp.raw._sock.shutdowns, [chat.socket.SHUT_RDWR])
        self.assertTrue(response.closed)

    def test_plan_validation_accepts_and_rejects_guard(self):
        plan = {'prefix_rows': 65536, 'stages': [
            {'category': name, 'repeats': 1} for name in trace_cases.CATEGORIES]}
        self.assertEqual(trace_cases.validate_plan(plan)['prefix_rows'], 65536)
        accepted = dict(plan, repeat_guard={'window': 3, 'min_chars': 20})
        self.assertEqual(trace_cases.validate_plan(accepted)['repeat_guard']['window'], 3)
        for bad in ({'window': 1, 'min_chars': 20}, {'window': 3, 'min_chars': 2},
                    {'window': 3}, {'window': 3, 'min_chars': 20, 'extra': 1}):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    trace_cases.validate_plan(dict(plan, repeat_guard=bad))


if __name__ == '__main__':
    unittest.main()
