#!/usr/bin/env python3
"""检查本机诊断入口的原样重放、冻结记录、数值结果和失败隔离。"""
import argparse
from contextlib import ExitStack, nullcontext
import copy
import http.client
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import MagicMock, Mock, patch
import urllib.error

import batch_controller as controller
import diagnostic as base
import local_multi_turn_replay as replay
import multi_turn_batch as batch
HERE = Path(__file__).resolve().parent
FROZEN = HERE.parents[1] / 'reports/raw/delivery-multiturn-20261021-115000-r2'
CHAT = HERE.parents[1] / 'serve/cached-document-chat.py'
CHAT_MODULE = base.load_module('test_replay_stream_chat', CHAT)


class ReplayTests(unittest.TestCase):
    """用临时文件和模拟响应检查诊断，不启动模型服务。"""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        for name in ('multi_turn_cases.py', 'cases.json'):
            shutil.copyfile(FROZEN / name, self.source / name)
        cases = base.load_module('test_replay_original_v1', self.source / 'multi_turn_cases.py')
        self.cases = cases
        selected = [('2B', 'site_totals', 2), ('2B', 'inventory', 2),
                    ('2B', 'meeting_gap', 2), ('2B', 'doc_citations', 1),
                    ('4B', 'inventory', 2), ('4B', 'duration_math', 2)]
        self.originals = {}
        attempts = []
        for model, conversation_id, turn_index in selected:
            identifier = model.lower() + '-' + conversation_id
            conversation = next(item for item in cases.read_cases() if item['conversation_id'] == conversation_id)
            result = self.source / 'batch/attempts' / identifier / 'result'
            folder = result / 'conversations' / conversation_id / f'turn-{turn_index}'
            folder.mkdir(parents=True)
            messages = [{'role': 'system', 'content': cases.SYSTEM}]
            for turn in conversation['turns'][:turn_index - 1]:
                messages.extend([{'role': 'user', 'content': turn['user']},
                                 {'role': 'assistant', 'content': '原始回答\n70 * 1 = 70'}])
            messages.append({'role': 'user', 'content': conversation['turns'][turn_index - 1]['user']})
            payload = {'messages': messages, 'model': 'local', 'temperature': 0, 'seed': 42,
                       'stream': True, 'cache_prompt': False, 'id_slot': 0, 'max_tokens': 1024,
                       'chat_template_kwargs': {'enable_thinking': False},
                       'stream_options': {'include_usage': True}, 'verbose': True,
                       'diagnostic_sentinel': {'untouched': ['完整参数', 7]}}
            raw = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode() + b'\n'
            (folder / 'request.json').write_bytes(raw)
            self.originals[identifier] = raw
            base.save(folder / 'quality.json', cases.assess(conversation['turns'][turn_index - 1], '错误答案'))
            base.save(result / 'protocol.json', {'model': model})
            base.save(result / 'summary.json', {'results': [
                {'conversation_id': conversation_id, 'status': 'failed', 'failure': {'turn': turn_index}}]})
            attempts.append({'id': identifier, 'status': 'failed', 'attempt': '/old-board/path/' + identifier})
        base.save(self.source / 'batch/summary.json', {'attempts': attempts})
        self.assertEqual(replay.read_json(self.source / 'cases.json'), cases.read_cases())
        for name in ('multi_turn_cases.py', 'cases.json'):
            self.assertEqual((self.source / name).read_bytes(), (FROZEN / name).read_bytes())
        self.models = self.root / 'models'
        self.models.mkdir()
        manifest = {'models': {}}
        for name, content in (('2B', b'two'), ('4B', b'four')):
            path = self.models / (name + '.gguf')
            path.write_bytes(content)
            manifest['models'][name] = {'filename': path.name, 'sha256': base.sha256(path)}
        self.manifest = self.root / 'manifest.json'
        base.save(self.manifest, manifest)
        self.server = self.root / 'build/bin/llama-server'
        self.server.parent.mkdir(parents=True)
        self.server.write_bytes(b'local-server')
        self.args = argparse.Namespace(output=self.root / 'output', source_batch=self.source,
                                       server=self.server, models=self.models, manifest=self.manifest,
                                       chat=CHAT, timeout=9, port=18260)

    def prepare(self):
        with patch.object(replay, 'runtime_identity', return_value={'runtime': 'local-test'}):
            return replay.prepare(self.args)

    def config(self, identifier='2b-site_totals'):
        return self.args.output / 'configs' / identifier / 'config.json'

    def worker_environment(self, response=None, identifier='2b-site_totals'):
        """构造工作进程所需的外部接口。"""
        config = replay.read_json(self.config(identifier))
        attempt = Path(config['attempt'])
        attempt.mkdir(parents=True)
        process = Mock()
        process.poll.return_value = None
        process.returncode = 0
        chat = Mock()
        chat.count_prompt_tokens.return_value = 91
        chat.complete.return_value = response or {
            'answer': '109', 'finish_reason': 'stop', 'reasoning_text': '', 'server_slot': 0,
            'usage': {'prompt_tokens': 91, 'completion_tokens': 3,
                      'prompt_tokens_details': {'cached_tokens': 0}},
            'timings': {'prompt_n': 91, 'predicted_n': 3, 'prompt_ms': 15.5,
                        'predicted_ms': 23.5, 'draft_n': 0, 'draft_n_accepted': 0},
            'wall_s': 0.039, 'ttft_s': 0.016}
        load_module = base.load_module

        def load(name, path):
            return chat if name == 'local_replay_chat' else load_module(name, path)

        props = Mock()
        props.__enter__ = Mock(return_value=Mock(read=lambda: json.dumps(
            {'total_slots': 1, 'default_generation_settings': {'n_ctx': 12288},
             'chat_template': '模型内置模板'}).encode()))
        props.__exit__ = Mock(return_value=False)
        stack = ExitStack()
        stack.enter_context(patch.object(replay.subprocess, 'Popen', return_value=process))
        stack.enter_context(patch.object(base, 'wait_ready'))
        stack.enter_context(patch.object(base, 'load_module', side_effect=load))
        stack.enter_context(patch.object(replay.urllib.request, 'urlopen', return_value=props))
        stack.enter_context(patch.object(replay.signal, 'signal'))
        self.addCleanup(stack.close)
        return chat, process, attempt / 'result'

    def stream_response(self, chat, failure=None, tail=b''):
        """通过真实客户端先读取文本，再触发流异常或截断。"""
        raw = b': keep-alive\n\n' + b''.join(
            b'data: ' + json.dumps({'choices': [{'delta': {'content': content}}]},
                                  ensure_ascii=False).encode() + b'\n\n'
            for content in ('合计：', '109')) + tail

        def lines():
            yield from raw.splitlines(keepends=True)
            if failure is not None:
                raise failure

        stream = MagicMock()
        stream.__enter__.return_value = stream
        stream.headers = {'Content-Type': 'text/event-stream'}
        stream.__iter__.return_value = lines()
        props = replay.urllib.request.urlopen.return_value
        replay.urllib.request.urlopen.side_effect = [props, stream]
        chat.complete.side_effect = CHAT_MODULE.complete
        return raw

    def assert_partial(self, folder, raw, reason, interruption=None):
        """核对原始字节、回答前缀和非完整标记。"""
        self.assertEqual((folder / 'stream.sse').read_bytes(), raw)
        self.assertEqual((folder / 'answer.partial.txt').read_text(), '合计：109')
        partial = replay.read_json(folder / 'partial-answer.json')
        self.assertIs(partial['complete'], False)
        self.assertEqual(partial['answer'], '合计：109')
        self.assertEqual(partial['answer_chars'], 6)
        self.assertIn(reason, partial['failure_reason'])
        self.assertEqual(partial['recovery_interruption'], interruption)
        self.assertFalse((folder / 'answer.txt').exists())
        self.assertFalse((folder / 'answer.json').exists())

    def test_six_jobs_and_payload_bytes_are_frozen_before_execution(self):
        with patch.object(base, 'sha256', wraps=base.sha256) as digest:
            jobs = self.prepare()
        model_calls = [call.args[0] for call in digest.call_args_list if Path(call.args[0]).suffix == '.gguf']
        self.assertEqual(sorted(model_calls), sorted(self.models.glob('*.gguf')))
        self.assertEqual(len(jobs), 6)
        self.assertEqual(replay.read_json(self.args.output / 'jobs.json'), jobs)
        self.assertEqual(jobs[0]['timeout_s'], 9 + 240 + 120)
        first = replay.read_json(self.config())
        self.assertEqual(first['argv'], [str(self.server), '-m', str(self.models / '2B.gguf'),
                         '--alias', 'local', '--host', '127.0.0.1', '--port', '18260',
                         '--n-gpu-layers', '0', '--threads', '4', '--threads-batch', '4',
                         '--batch-size', '32', '--ubatch-size', '32', '--ctx-size', '12288',
                         '--parallel', '1', '--cache-type-k', 'f16', '--cache-type-v', 'f16',
                         '--flash-attn', 'on', '--spec-type', 'none'])
        for job in jobs:
            config = replay.read_json(Path(job['argv'][-1]))
            self.assertEqual(Path(config['request']).read_bytes(), self.originals[job['id']])
            self.assertEqual(config['original_quality']['passed'], False)
            self.assertEqual(config['rule'], next(item for item in self.cases.read_cases()
                             if item['conversation_id'] == config['conversation_id'])['turns'][config['turn_index'] - 1])
            self.assertIn('--worker', job['argv'])
            self.assertIn('--spec-type', config['argv'])
            self.assertEqual(config['argv'][config['argv'].index('--spec-type') + 1], 'none')
            self.assertNotIn('--chat-template', config['argv'])
            self.assertFalse(Path(config['attempt']).exists())
        frozen = replay.read_json(self.config())
        Path(frozen['source_request']).write_text('{}')
        self.args.timeout = 88
        self.assertEqual(replay.read_json(self.config())['timeout_s'], 9)
        self.assertEqual(Path(frozen['request']).read_bytes(), self.originals['2b-site_totals'])

    def test_changed_model_is_rejected_before_output_creation(self):
        (self.models / '4B.gguf').write_bytes(b'changed')
        with patch.object(replay, 'runtime_identity') as runtime:
            with self.assertRaisesRegex(ValueError, 'model differs from manifest: 4B'):
                replay.prepare(self.args)
        runtime.assert_not_called()
        self.assertFalse(self.args.output.exists())

    def test_runtime_identity_records_linked_and_dynamic_libraries(self):
        linked = self.root / 'libsystem.so'
        linked.write_bytes(b'system')
        dynamic = self.server.parent / 'libggml-cpu.so'
        dynamic.write_bytes(b'backend')
        cache = self.server.parent.parent / 'CMakeCache.txt'
        cache.write_text('GGML_NATIVE:BOOL=OFF\n')
        result = subprocess.CompletedProcess([], 0, f'libsystem.so => {linked} (0x1234)\n', '')
        with patch.object(replay.subprocess, 'run', return_value=result):
            identity = replay.runtime_identity(self.server, {'LD_LIBRARY_PATH': str(self.server.parent)})
        self.assertEqual(identity['dependencies'], {str(linked): base.sha256(linked),
                                                   str(dynamic): base.sha256(dynamic)})
        self.assertEqual(identity['server']['sha256'], base.sha256(self.server))
        self.assertEqual(identity['build']['cmake_cache'], 'GGML_NATIVE:BOOL=OFF\n')
        self.assertEqual(identity['uname'], list(os.uname()))

    def test_worker_sends_unchanged_payload_and_records_numbers(self):
        self.prepare()
        chat, process, folder = self.worker_environment()
        self.assertEqual(replay.worker(self.config()), 0)
        expected = json.loads(self.originals['2b-site_totals'])
        self.assertEqual(chat.count_prompt_tokens.call_args.args[1], expected)
        self.assertEqual(chat.complete.call_args.args[1], expected)
        self.assertEqual(chat.complete.call_args.kwargs['stream_path'], folder / 'stream.sse')
        self.assertEqual((folder / 'request.json').read_bytes(), self.originals['2b-site_totals'])
        self.assertEqual((folder / 'answer.txt').read_text(), '109')
        record = replay.read_json(folder / 'summary.json')
        self.assertEqual(record['metrics'], {'prompt_tokens': 91, 'completion_tokens': 3,
                                             'cached_tokens': 0, 'draft_n': 0, 'draft_n_accepted': 0})
        self.assertEqual(record['wall_s'], 0.039)
        self.assertEqual(record['timings']['predicted_ms'], 23.5)
        self.assertEqual(record['v1_quality']['checks'][0]['matched'], True)
        self.assertEqual(record['v1_quality']['answer_chars'], 3)
        self.assertEqual(replay.read_json(folder / 'quality-v1.json'), record['v1_quality'])
        self.assertFalse((folder / 'quality.json').exists())
        self.assertIsNone(record['quality_gate'])
        self.assertEqual(record['quality_review'], 'pending')
        self.assertEqual(record['reason'], 'complete_for_manual_review')
        self.assertEqual(replay.read_json(folder.parent / 'outcome.json'),
                         {'status': 'passed', 'reason': 'complete_for_manual_review'})
        self.assertEqual(replay.subprocess.Popen.call_args.kwargs['pass_fds'], (9,))
        self.assertEqual(replay.read_json(folder.parent / 'process.json')['pgid'], os.getpgrp())
        process.terminate.assert_called_once()
        process.wait.assert_called_once_with(timeout=30)

    def test_worker_v1_false_keeps_correct_answer_for_manual_review(self):
        self.prepare()
        identifier = '4b-duration_math'
        chat, _, folder = self.worker_environment(identifier=identifier)
        hours, minutes = divmod(150 + 45, 60)
        answer = f'{hours} 个小时 {minutes} 分钟'
        chat.complete.return_value['answer'] = answer
        self.assertEqual(replay.worker(self.config(identifier)), 0)
        self.assertEqual((folder / 'answer.txt').read_text(), '3 个小时 15 分钟')
        record = replay.read_json(folder / 'summary.json')
        self.assertFalse(record['v1_quality']['passed'])
        self.assertEqual(replay.read_json(folder / 'quality-v1.json'), record['v1_quality'])
        self.assertEqual(record['status'], 'passed')
        self.assertEqual(record['reason'], 'complete_for_manual_review')
        self.assertIsNone(record['quality_gate'])
        self.assertEqual(record['quality_review'], 'pending')
        self.assertFalse((folder / 'quality.json').exists())
        self.assertEqual(replay.read_json(folder.parent / 'outcome.json'),
                         {'status': 'passed', 'reason': 'complete_for_manual_review'})

    def test_worker_transport_failure_is_incomplete(self):
        self.prepare()
        chat, process, folder = self.worker_environment()
        failures = [TimeoutError('stream deadline'), urllib.error.URLError('connection reset'),
                    ConnectionResetError('connection lost'), http.client.BadStatusLine('invalid'),
                    http.client.LineTooLong('status line'), http.client.IncompleteRead(b'partial')]
        for failure in failures:
            with self.subTest(failure=type(failure).__name__):
                raw = self.stream_response(chat, failure)
                self.assertEqual(replay.worker(self.config()), 2)
                self.assert_partial(folder, raw, type(failure).__name__)
                record = replay.read_json(folder / 'summary.json')
                self.assertEqual(record['status'], 'incomplete')
                self.assertIsNone(record['quality_gate'])
                self.assertEqual(record['quality_review'], 'pending')
                self.assertEqual(replay.read_json(folder / 'prompt-count.json'), {'prompt_tokens': 91})
                self.assertEqual(replay.read_json(folder.parent / 'outcome.json')['status'], 'incomplete')
                shutil.rmtree(folder)
                (folder.parent / 'outcome.json').unlink()
        self.assertEqual(process.terminate.call_count, len(failures))

    def test_worker_truncation_is_incomplete_and_internal_errors_propagate(self):
        self.prepare()
        chat, process, folder = self.worker_environment()
        raw = self.stream_response(chat)
        self.assertEqual(replay.worker(self.config()), 2)
        self.assertIn('DONE', replay.read_json(folder / 'summary.json')['reason'])
        self.assert_partial(folder, raw, 'DONE')
        shutil.rmtree(folder)
        (folder.parent / 'outcome.json').unlink()
        raw = self.stream_response(chat, RuntimeError('internal defect'))
        with self.assertRaisesRegex(RuntimeError, 'internal defect'):
            replay.worker(self.config())
        self.assert_partial(folder, raw, 'internal defect')
        self.assertFalse((folder.parent / 'outcome.json').exists())
        damaged = [(b'data: {"choices": [\n', json.JSONDecodeError, 'JSONDecodeError')]
        for field in ('usage', 'timings'):
            event = {field: 7, 'choices': [{'delta': {'content': '错误后缀'}}]}
            damaged.append((b'data: ' + json.dumps(event).encode() + b'\n', TypeError, 'TypeError'))
        damaged.append((b'data: {"choices":[{"delta":{"content":"\\ud800"}}]}\n',
                        RuntimeError, 'UnicodeEncodeError'))
        for tail, error_type, recovery_reason in damaged:
            with self.subTest(recovery_reason=recovery_reason, tail=tail):
                shutil.rmtree(folder)
                raw = self.stream_response(chat, RuntimeError('internal defect'), tail=tail)
                with self.assertRaises(error_type):
                    replay.worker(self.config())
                interruption = replay.read_json(folder / 'partial-answer.json')['recovery_interruption']
                self.assertEqual(interruption['line'], 7)
                self.assertIn(recovery_reason, interruption['reason'])
                self.assert_partial(folder, raw, error_type.__name__, interruption)
                self.assertFalse((folder.parent / 'outcome.json').exists())
                self.assertEqual(replay.read_json(folder / 'exit.json'), {'returncode': 0})
        self.assertEqual(process.terminate.call_count, 2 + len(damaged))
        self.assertEqual(process.wait.call_count, 2 + len(damaged))

    def test_response_gate_rejects_bad_stop_cache_and_drafts(self):
        self.prepare()
        chat, _, folder = self.worker_environment()
        original = copy.deepcopy(chat.complete.return_value)
        for field, value in (('finish_reason', 'length'), ('cached_tokens', 1), ('draft_n', 1),
                             ('prompt_tokens', 90), ('completion_tokens', 4)):
            with self.subTest(field=field):
                response = copy.deepcopy(original)
                if field == 'cached_tokens':
                    response['usage']['prompt_tokens_details'][field] = value
                elif field == 'draft_n':
                    response['timings'][field] = value
                elif field in ('prompt_tokens', 'completion_tokens'):
                    response['usage'][field] = value
                else:
                    response[field] = value
                chat.complete.return_value = response
                with self.assertRaises(ValueError):
                    replay.worker(self.config())
                self.assertEqual(replay.read_json(folder / 'answer.json'), response)
                self.assertFalse((folder.parent / 'outcome.json').exists())
                shutil.rmtree(folder)

    def test_one_signal_deadline_covers_tokenize_and_complete(self):
        folder = self.root / 'request'
        folder.mkdir()
        chat = Mock()
        chat.count_prompt_tokens.return_value = 91
        observed = []

        def count(*args):
            observed.append(signal.getitimer(signal.ITIMER_REAL)[0])
            time.sleep(.035)
            return 91

        def complete(*args, **kwargs):
            observed.append(signal.getitimer(signal.ITIMER_REAL)[0])
            time.sleep(.15)
            return {}

        chat.count_prompt_tokens.side_effect = count
        chat.complete.side_effect = complete
        with self.assertRaises(TimeoutError):
            replay.request_once(chat, {'timeout_s': .09, 'url': 'http://unused'}, {'max_tokens': 1024}, folder)
        self.assertGreater(observed[0], observed[1])
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL)[0], 0)
        self.assertEqual(replay.read_json(folder / 'prompt-count.json')['prompt_tokens'], 91)

    def test_timeout_stops_worker_and_server_escalates_to_kill(self):
        self.prepare()
        chat, process, folder = self.worker_environment()
        chat.count_prompt_tokens.side_effect = TimeoutError('request deadline expired')
        process.wait.side_effect = [subprocess.TimeoutExpired('server', 30), 0]
        self.assertEqual(replay.worker(self.config()), 2)
        chat.complete.assert_not_called()
        self.assertEqual(replay.read_json(folder / 'summary.json')['status'], 'incomplete')
        process.kill.assert_called_once()
        self.assertEqual(process.wait.call_count, 2)

    def test_controller_continues_after_truncation_timeout_crash_and_assertion(self):
        jobs = []
        actions = ["raise RuntimeError('truncated stream')", 'import time; time.sleep(5)',
                   'os.kill(os.getpid(), 9)', 'assert False',
                   "(folder / 'outcome.json').write_text('{\"status\":\"failed\"}')",
                   "(folder / 'outcome.json').write_text('{\"status\":\"passed\"}')"]
        output = self.root / 'controller'
        for index, action in enumerate(actions):
            identifier = f'job-{index}'
            prefix = ("import os,json; from pathlib import Path; "
                      f"folder=Path({str(output / 'attempts' / identifier)!r}); "
                      "(folder/'process.json').write_text(json.dumps({'pgid':os.getpgrp()})); ")
            jobs.append({'id': identifier, 'argv': [sys.executable, '-c', prefix + action],
                         'timeout_s': .15 if index == 1 else 5, 'dependency': 'test'})
        before, after = batch.lifecycle_hooks()
        summary = controller.run(jobs, output, before=before, after=after)
        self.assertEqual([item['status'] for item in summary['attempts']],
                         ['failed', 'incomplete', 'failed', 'failed', 'failed', 'passed'])
        self.assertEqual(summary['counts'], {'passed': 1, 'failed': 4, 'incomplete': 1,
                                             'blocked': 0, 'unattempted': 0})
        self.assertEqual(sum(summary['counts'].values()), 6)
        self.assertEqual(controller.exit_code(summary), 2)
        for job in jobs:
            self.assertTrue(replay.read_json(output / 'attempts' / job['id'] / 'cleanup.json')['exited'])

    def test_main_requires_chat_and_freezes_before_controller(self):
        argv = []
        for name in ('output', 'source_batch', 'server', 'models', 'manifest'):
            argv.extend(['--' + name.replace('_', '-'), str(getattr(self.args, name))])
        with self.assertRaises(SystemExit):
            replay.main(argv)
        argv.extend(['--chat', str(CHAT)])

        def run(jobs, output, **kwargs):
            self.assertEqual(len(jobs), 6)
            self.assertEqual(replay.read_json(self.args.output / 'jobs.json'), jobs)
            self.assertEqual(kwargs['pass_fds'], (9,))
            self.assertEqual(replay.read_json(self.config())['timeout_s'], 900)
            self.assertEqual(replay.read_json(self.config())['url'], 'http://127.0.0.1:18260')
            self.assertEqual(replay.read_json(self.args.output / 'protocol.json')['purpose'], 'diagnostic')
            return {'batch_success': False, 'counts': {'failed': 6}}

        with patch.object(replay, 'runtime_identity', return_value={}), \
                patch.object(batch, 'board_lock', return_value=nullcontext()) as lock, \
                patch.object(replay.socket, 'socket') as sock, \
                patch.object(controller, 'run', side_effect=run):
            sock.return_value.__enter__.return_value.connect_ex.return_value = 1
            self.assertEqual(replay.main(argv), 2)
        lock.assert_called_once_with(str(Path(tempfile.gettempdir()) / 'riscv-accl-local-inference.lock'))
        record = replay.read_json(self.args.output / 'batch_status.json')
        self.assertEqual(record['batch_status'], 2)
        self.assertIsNone(record['quality_gate'])

    def test_frozen_v1_records_known_substring_false_positive(self):
        self.prepare()
        assessment = base.load_module('test_frozen_v1', self.args.output / 'assessment_v1.py')
        meeting = next(item for item in assessment.read_cases() if item['conversation_id'] == 'meeting_gap')
        result = assessment.assess(meeting['turns'][1], '不冲突')
        self.assertEqual(result, {'passed': True, 'checks': [
            {'pattern': '冲突|重叠', 'kind': 'require', 'matched': True}], 'failures': [], 'answer_chars': 3})


if __name__ == '__main__':
    unittest.main()
