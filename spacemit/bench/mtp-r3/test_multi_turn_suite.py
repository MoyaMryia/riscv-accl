#!/usr/bin/env python3
"""多轮入口的隔离与门槛测试；不启动真实服务器。"""
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time
from unittest import mock
import unittest
import urllib.error

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
EXPECTED_CHECKS = {'site_totals': 5, 'inventory': 5, 'policy_versions': 4,
                   'meeting_gap': 4, 'duration_math': 4, 'doc_citations': 8}


def reply(answer, prompt_count, cache_prompt=False, finish='stop'):
    return {'payload': {}, 'prompt_count': prompt_count, 'response': {
        'answer': answer, 'ttft_s': 0.5, 'wall_s': 1.0, 'finish_reason': finish,
        'reasoning_text': '', 'server_slot': 0,
        'usage': {'prompt_tokens': prompt_count,
                  'completion_tokens': 8,
                  'prompt_tokens_details': {'cached_tokens': 0}},
        'timings': {'prompt_n': prompt_count, 'predicted_n': 8,
                    'prompt_ms': 100.0, 'predicted_ms': 200.0,
                    'draft_n': 0, 'draft_n_accepted': 0}}}


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
        self.assertEqual(summary['checks_passed'], sum(EXPECTED_CHECKS.values()))
        self.assertEqual(summary['checks_total'], sum(EXPECTED_CHECKS.values()))

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

    def test_rejects_drafts(self):
        response = reply('ok', 10)['response']
        for generated, accepted in ((1, 0), (3, 2), (0, 1), (False, 0), (0, -1)):
            with self.subTest(generated=generated, accepted=accepted):
                response['timings'].update(draft_n=generated, draft_n_accepted=accepted)
                with self.assertRaises(ValueError):
                    suite.validate_turn(response, 10, 1024, False)
        response['timings'].update(draft_n=0, draft_n_accepted=0)
        self.assertEqual(suite.validate_turn(response, 10, 1024, False), {
            'prompt_tokens': 10, 'completion_tokens': 8, 'cached_tokens': 0,
            'draft_n': 0, 'draft_n_accepted': 0})

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

    def complete(self, url, payload, timeout, display=True, guard=None, stream_path=None):
        return reply('ok', self.prompt_count)['response']


class FitTest(unittest.TestCase):
    def test_rejects_turn_that_cannot_fit(self):
        client = suite.HttpClient(FakeChat(12000), 'http://x', 'local', 1024, 10, 12288)
        with self.assertRaises(ValueError):
            client.ask([{'role': 'user', 'content': 'x'}])

    def test_accepts_turn_that_fits(self):
        client = suite.HttpClient(FakeChat(100), 'http://x', 'local', 1024, 10, 12288)
        self.assertEqual(client.ask([{'role': 'user', 'content': 'x'}])['prompt_count'], 100)


class HttpEvidenceTest(unittest.TestCase):
    """使用聊天模块解析测试流，检查失败证据。"""

    def setUp(self):
        chat_path = Path(os.environ.get(
            'MULTI_TURN_CHAT_PATH', Path(suite.__file__).resolve().parents[2]
            / 'serve/cached-document-chat.py'))
        self.chat = suite.base.load_module('test_suite_chat', chat_path)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.messages = [{'role': 'user', 'content': '设备合计？'}]
        self.client = suite.HttpClient(self.chat, 'http://x', 'local', 1024, 10,
                                       12288, evidence_root=self.root)
        self.original_handler = signal.getsignal(signal.SIGALRM)

    def stream(self, *, finish='stop', predicted_n=8, ending=b'data: [DONE]\n\n'):
        response = reply('108', 10, finish=finish)['response']
        response['timings']['predicted_n'] = predicted_n
        event = {'choices': [{'delta': {'content': '108'}, 'finish_reason': finish}],
                 'usage': response['usage'], 'timings': response['timings'],
                 '__verbose': {'id_slot': 0}}
        return b'data: ' + json.dumps(event).encode() + b'\n\n' + ending

    def assert_timer_clear(self):
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0.0, 0.0))
        self.assertIs(signal.getsignal(signal.SIGALRM), self.original_handler)

    def http(self, raw, *, count_error=None, stream_error=None):
        def open_request(request, timeout):
            saved = json.loads((self.root / f'turn-{self.client.turn}' / 'request.json').read_text())
            self.assertEqual(json.loads(request.data), saved)
            self.assertEqual(saved['messages'], self.messages)
            self.assertEqual(saved['max_tokens'], 1024)
            self.assertEqual(saved['id_slot'], 0)
            self.assertFalse(saved['cache_prompt'])
            self.assertEqual(saved['stream_options'], {'include_usage': True})
            self.assertTrue(saved['verbose'])
            if request.full_url.endswith('/input_tokens'):
                if count_error is not None:
                    raise count_error
                return io.BytesIO(b'{"input_tokens": 10}')
            if stream_error is not None:
                raise stream_error
            response = io.BytesIO(raw)
            response.headers = {'Content-Type': 'text/event-stream'}
            return response
        return mock.patch.object(self.chat.urllib.request, 'urlopen', side_effect=open_request)

    def test_partial_stream_and_error_keep_request_and_sse(self):
        for ending in (b'', b'data: {"error": "injected error"}\n'):
            with self.subTest(ending=ending):
                raw = self.stream(ending=ending)
                with self.http(raw):
                    with self.assertRaises(RuntimeError):
                        self.client.ask(self.messages)
                folder = self.root / f'turn-{self.client.turn}'
                self.assertEqual((folder / 'stream.sse').read_bytes(), raw)
                self.assertFalse((folder / 'answer.json').exists())
                self.assert_timer_clear()
        self.assertEqual(self.client.turn, 2)

    def test_http_errors_keep_preexisting_request(self):
        for stage in ('count_error', 'stream_error'):
            with self.subTest(stage=stage):
                with self.http(b'', **{stage: urllib.error.URLError('injected error')}):
                    with self.assertRaises(urllib.error.URLError):
                        self.client.ask(self.messages)
                folder = self.root / f'turn-{self.client.turn}'
                self.assertEqual(json.loads((folder / 'request.json').read_text())['max_tokens'], 1024)
                self.assertEqual((folder / 'stream.sse').exists(), stage == 'stream_error')
                if stage == 'stream_error':
                    self.assertEqual((folder / 'stream.sse').stat().st_size, 0)
                self.assert_timer_clear()

    def test_available_response_precedes_validation(self):
        for finish, predicted_n in (('length', 8), ('stop', 9)):
            with self.subTest(finish=finish, predicted_n=predicted_n):
                raw = self.stream(finish=finish, predicted_n=predicted_n)
                with self.http(raw):
                    result = self.client.ask(self.messages)
                folder = self.root / f'turn-{self.client.turn}'
                saved = json.loads((folder / 'answer.json').read_text())
                self.assertEqual(saved['answer'], '108')
                self.assertEqual(saved['finish_reason'], finish)
                self.assertEqual(saved['usage']['completion_tokens'], 8)
                self.assertEqual(saved['timings']['predicted_n'], predicted_n)
                self.assertEqual(saved['http_headers']['content-type'], 'text/event-stream')
                self.assertEqual((folder / 'answer.txt').read_text(), '108')
                self.assertEqual((folder / 'stream.sse').read_bytes(), raw)
                with self.assertRaises(ValueError):
                    suite.validate_turn(result['response'], result['prompt_count'], 1024, False)
                self.assert_timer_clear()

    def test_internal_error_propagates_with_request(self):
        self.messages = [{'role': 'system', 'content': cases.SYSTEM},
                         {'role': 'user', 'content': cases.read_cases()[0]['turns'][0]['user']}]
        with self.http(b'', count_error=KeyError('internal')):
            with self.assertRaises(KeyError):
                suite.run_conversation(self.client, cases.read_cases()[0])
        self.assertEqual(json.loads((self.root / 'turn-1/request.json').read_text())['max_tokens'], 1024)
        self.assert_timer_clear()


class DeadlineTest(unittest.TestCase):
    """用真实信号中断延迟，检查总期限和清理。"""

    def test_tokenize_and_complete_share_deadline(self):
        chat = FakeChat(10)
        count = chat.count_prompt_tokens
        complete = chat.complete
        phases = []

        def delayed_count(*args):
            phases.append('count')
            time.sleep(0.15)
            return count(*args)

        def delayed_complete(*args, **kwargs):
            phases.append('complete')
            time.sleep(0.20)
            return complete(*args, **kwargs)

        chat.count_prompt_tokens = delayed_count
        chat.complete = delayed_complete
        client = suite.HttpClient(chat, 'http://x', 'local', 1024, 0.30, 12288)
        previous = signal.getsignal(signal.SIGALRM)
        started = time.monotonic()
        result = suite.run_conversation(client, cases.read_cases()[0])
        elapsed = time.monotonic() - started
        self.assertEqual(result['status'], 'incomplete')
        self.assertEqual(result['turns_completed'], 0)
        self.assertEqual(result['checks_total'], 0)
        self.assertEqual(result['failure']['turn'], 1)
        self.assertIn('TimeoutError', result['failure']['error'])
        self.assertEqual(phases, ['count', 'complete'])
        self.assertGreaterEqual(elapsed, 0.28)
        self.assertLess(elapsed, 0.60)
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0.0, 0.0))
        self.assertIs(signal.getsignal(signal.SIGALRM), previous)
        chat.count_prompt_tokens = count
        chat.complete = complete
        success = client.ask([{'role': 'user', 'content': 'x'}])
        self.assertEqual(success['prompt_count'], 10)
        self.assertEqual(success['response']['usage']['completion_tokens'], 8)
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0.0, 0.0))
        self.assertIs(signal.getsignal(signal.SIGALRM), previous)

    def test_deadline_interrupts_tokenize(self):
        chat = FakeChat(10)
        chat.count_prompt_tokens = mock.Mock(side_effect=lambda *args: time.sleep(1))
        chat.complete = mock.Mock()
        client = suite.HttpClient(chat, 'http://x', 'local', 1024, 0.05, 12288)
        previous = signal.getsignal(signal.SIGALRM)
        started = time.monotonic()
        with self.assertRaises(TimeoutError):
            client.ask([{'role': 'user', 'content': 'x'}])
        self.assertLess(time.monotonic() - started, 0.5)
        self.assertEqual(chat.count_prompt_tokens.call_count, 1)
        chat.complete.assert_not_called()
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0.0, 0.0))
        self.assertIs(signal.getsignal(signal.SIGALRM), previous)


class MainTest(unittest.TestCase):
    """检查会话选择、服务器目录和启动失败记录。"""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / 'output'
        self.argv = []
        for name in ('output', 'server', 'models', 'spert', 'tcm', 'manifest',
                     'build-receipt', 'chat', 'quality', 'effective', 'tool-receipt'):
            self.argv += ['--' + name, str(self.output if name == 'output' else self.root / name)]
        self.addCleanup(signal.signal, signal.SIGTERM, signal.getsignal(signal.SIGTERM))
        self.processes = []

    def process(self, *args, **kwargs):
        process = mock.Mock(returncode=None)
        process.poll.side_effect = lambda: process.returncode
        process.terminate.side_effect = lambda: setattr(process, 'returncode', -15)
        self.processes.append(process)
        return process

    def read(self, name):
        return json.loads((self.output / name).read_text())

    def run_main(self, extra=(), *, startup_error=None, internal_error=False):
        chat = FakeChat(10)

        def complete(url, payload, timeout, **kwargs):
            messages = payload['messages']
            conversation_id = next(c['conversation_id'] for c in cases.read_cases()
                                   if c['turns'][0]['user'] == messages[1]['content'])
            answer = ANSWERS[conversation_id][len(messages) // 2 - 1]
            return reply(answer, 10)['response']

        chat.complete = complete
        if internal_error:
            chat.count_prompt_tokens = mock.Mock(side_effect=KeyError('internal'))
        props = {'total_slots': 1, 'default_generation_settings': {'n_ctx': 12288}}
        with mock.patch.dict(os.environ, {'TMUX': 'test'}), \
                mock.patch.object(suite.base, 'verify_inputs', return_value=({'2B': self.root / 'model'}, {})), \
                mock.patch.object(suite.base, 'load_module', return_value=chat), \
                mock.patch.object(suite.subprocess, 'Popen', side_effect=self.process) as popen, \
                mock.patch.object(suite.base, 'wait_ready', side_effect=startup_error), \
                mock.patch.object(suite.urllib.request, 'urlopen',
                                  side_effect=lambda *a, **k: io.BytesIO(json.dumps(props).encode())):
            code = suite.main(self.argv + list(extra))
        return code, popen

    def test_default_runs_six_conversations_on_same_port(self):
        code, popen = self.run_main()
        self.assertEqual(code, 0)
        summary = self.read('summary.json')
        self.assertEqual(summary['counts'], {'passed': 6, 'failed': 0, 'incomplete': 0})
        self.assertEqual(summary['turns_completed'], 24)
        self.assertEqual(summary['checks_passed'], sum(EXPECTED_CHECKS.values()))
        self.assertEqual(summary['checks_total'], sum(EXPECTED_CHECKS.values()))
        self.assertTrue(summary['gate_passed'])
        self.assertEqual(popen.call_count, 6)
        ports = [call.args[0][call.args[0].index('--port') + 1] for call in popen.call_args_list]
        self.assertEqual(ports, ['18088'] * 6)
        folders = sorted((self.output / 'servers').glob('*/server-18088'))
        self.assertEqual(len(folders), 6)
        for folder in folders:
            self.assertEqual(json.loads((folder / 'properties.json').read_text())['total_slots'], 1)
            self.assertEqual(json.loads((folder / 'exit.json').read_text())['returncode'], -15)
        for process in self.processes:
            process.terminate.assert_called_once()
            process.wait.assert_called_once_with(timeout=30)
        self.assertEqual(self.read('progress.json')['settled'], 6)

    def test_selects_single_conversation(self):
        code, popen = self.run_main(['--conversation', 'inventory'])
        self.assertEqual(code, 0)
        self.assertEqual(popen.call_count, 1)
        self.assertEqual(self.read('summary.json')['conversations'], {'inventory': 'passed'})
        self.assertEqual(self.read('summary.json')['turns_completed'], 4)
        self.assertEqual(self.read('protocol.json')['conversations'], 1)
        self.assertEqual(self.read('protocol.json')['turns'], 4)
        self.assertEqual([c['conversation_id'] for c in self.read('cases.json')], ['inventory'])
        self.assertEqual(self.read('conversations/inventory/result.json')['checks_passed'],
                         EXPECTED_CHECKS['inventory'])
        self.assertEqual(self.read('summary.json')['checks_total'], EXPECTED_CHECKS['inventory'])

    def test_rejects_unknown_conversation(self):
        with mock.patch.object(suite.base, 'verify_inputs') as verify, \
                mock.patch('sys.stderr', new_callable=io.StringIO):
            with self.assertRaises(SystemExit) as raised:
                suite.main(self.argv + ['--conversation', 'unknown'])
        self.assertEqual(raised.exception.code, 2)
        verify.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_rejects_disabled_deadline(self):
        for timeout in ('0', '-1'):
            with self.subTest(timeout=timeout), \
                    mock.patch.dict(os.environ, {'TMUX': 'test'}), \
                    mock.patch.object(suite.base, 'verify_inputs') as verify, \
                    mock.patch('sys.stderr', new_callable=io.StringIO) as stderr:
                with self.assertRaises(SystemExit) as raised:
                    suite.main(self.argv + ['--timeout', timeout])
                self.assertEqual(raised.exception.code, 2)
                self.assertIn('timeout must be positive', stderr.getvalue())
                verify.assert_not_called()
                self.assertFalse(self.output.exists())

    def test_startup_failure_has_conversation_result(self):
        code, popen = self.run_main(['--conversation', 'inventory'],
                                    startup_error=RuntimeError('injected startup failure'))
        self.assertEqual(code, 2)
        self.assertEqual(popen.call_count, 1)
        result = self.read('conversations/inventory/result.json')
        self.assertEqual(result['status'], 'incomplete')
        self.assertEqual(result['turns_completed'], 0)
        self.assertEqual(result['turns_planned'], 4)
        self.assertEqual(result['checks_passed'], 0)
        self.assertEqual(result['checks_total'], 0)
        self.assertEqual(result['failure']['turn'], 0)
        self.assertIn('injected startup failure', result['failure']['error'])
        self.assertEqual(self.read('progress.json')['settled'], 1)
        self.assertFalse(self.read('summary.json')['gate_passed'])
        self.assertEqual(self.read('servers/inventory/server-18088/exit.json')['returncode'], -15)
        self.processes[0].terminate.assert_called_once()

    def test_startup_failure_continues_other_conversations(self):
        code, popen = self.run_main(startup_error=[RuntimeError('startup'), None, None, None, None, None])
        self.assertEqual(code, 2)
        self.assertEqual(popen.call_count, 6)
        self.assertEqual(self.read('summary.json')['counts'],
                         {'passed': 5, 'failed': 0, 'incomplete': 1})
        self.assertEqual(self.read('summary.json')['turns_completed'], 20)
        self.assertEqual(self.read('progress.json')['settled'], 6)
        self.assertEqual(self.read('conversations/site_totals/result.json')['turns_completed'], 0)
        self.assertEqual(self.read('conversations/inventory/result.json')['status'], 'passed')
        self.assertFalse(self.read('summary.json')['gate_passed'])

    def test_internal_error_stops_worker_and_server(self):
        with self.assertRaises(KeyError):
            self.run_main(['--conversation', 'inventory'], internal_error=True)
        self.processes[0].terminate.assert_called_once()
        self.processes[0].wait.assert_called_once_with(timeout=30)
        self.assertEqual(self.read('servers/inventory/server-18088/exit.json')['returncode'], -15)
        self.assertFalse((self.output / 'summary.json').exists())


class StopServerTest(unittest.TestCase):
    def test_kills_server_after_stop_timeout(self):
        process = mock.Mock(returncode=-9)
        process.poll.return_value = None
        process.wait.side_effect = [subprocess.TimeoutExpired('server', 30), -9]
        suite.stop_server(process)
        process.terminate.assert_called_once()
        process.kill.assert_called_once()
        self.assertEqual(process.wait.call_args_list, [mock.call(timeout=30), mock.call()])
        self.assertEqual(process.returncode, -9)


if __name__ == '__main__':
    unittest.main()
