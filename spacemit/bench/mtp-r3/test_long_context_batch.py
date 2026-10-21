"""用假聊天接口和独立工作进程检查失败隔离，不启动真实模型。"""
import copy
import http.client
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import time
import unittest
from unittest import mock
import urllib.error

import batch_controller as controller
import diagnostic as base
import long_context_batch as batch
import long_context_cases as cases
from test_long_context_cases import character_count

EFFECTIVE_PATH = Path(os.environ.get(
    'LONG_CONTEXT_EFFECTIVE_PATH', Path(__file__).parents[1] / 'final-default' / 'effective.py'))


def response(count=250):
    """固定独立接口记录，供指标检查使用。"""
    return {'answer': '设备数为137台，负责人为顾青禾，巡检周期为19天。',
            'finish_reason': 'stop', 'reasoning_text': '', 'server_slot': 0,
            'usage': {'prompt_tokens': count, 'completion_tokens': 24,
                      'prompt_tokens_details': {'cached_tokens': 0}},
            'timings': {'prompt_n': count, 'predicted_n': 24, 'prompt_ms': 1200,
                        'predicted_ms': 2400, 'draft_n': 0, 'draft_n_accepted': 0},
            'wall_s': 3.8, 'ttft_s': 1.3}


def memory(available=9 * 1024**3, rss=2 * 1024**3):
    return {'MemAvailable': available, 'MemTotal': 16 * 1024**3,
            'SwapTotal': 4 * 1024**3, 'SwapFree': 4 * 1024**3,
            'rss_bytes': rss, 'time_unix_s': 1}


class RequestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.case = cases.generate_cases(character_count)[0]
        self.chat = mock.Mock()
        self.chat.count_prompt_tokens.return_value = 250
        self.chat.complete.return_value = response()

    def test_natural_answer_and_metrics(self):
        result = batch.request_once(self.chat, 'http://假接口', self.case, self.root)
        self.assertEqual(result, {'status': 'passed', 'reason': 'complete_for_manual_review'})
        payload = json.loads((self.root / 'request.json').read_text())
        self.assertEqual(payload['messages'], self.case['messages'])
        self.assertEqual(payload['temperature'], 0)
        self.assertEqual(payload['seed'], 42)
        self.assertEqual(payload['max_tokens'], 256)
        self.assertFalse(payload['cache_prompt'])
        self.assertEqual(payload['chat_template_kwargs'], {'enable_thinking': False})
        metrics = json.loads((self.root / 'metrics.json').read_text())
        self.assertEqual((metrics['prompt_tokens'], metrics['completion_tokens']), (250, 24))
        self.assertEqual((metrics['cached_tokens'], metrics['draft_n'], metrics['draft_n_accepted']), (0, 0, 0))
        self.assertEqual((metrics['wall_s'], metrics['ttft_s']), (3.8, 1.3))
        self.assertEqual((self.root / 'answer.txt').read_text(), response()['answer'])
        self.assertIsNone(json.loads((self.root / 'quality.json').read_text())['passed'])
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL)[0], 0)

    def test_request_saved_before_http(self):
        def count(*args):
            self.assertTrue((self.root / 'request.json').exists())
            raise TimeoutError('计数超时')
        self.chat.count_prompt_tokens.side_effect = count
        with self.assertRaises(TimeoutError):
            batch.request_once(self.chat, 'http://假接口', self.case, self.root)
        self.chat.complete.assert_not_called()

    def test_shared_deadline_for_32k(self):
        case = cases.generate_cases(character_count)[2]
        self.chat.count_prompt_tokens.return_value = 32760
        self.chat.complete.return_value = response(32760)
        with mock.patch.object(batch.signal, 'setitimer') as timer:
            batch.request_once(self.chat, 'http://假接口', case, self.root)
        self.assertEqual(timer.call_args_list, [mock.call(signal.ITIMER_REAL, 21600), mock.call(signal.ITIMER_REAL, 0)])
        self.assertEqual(self.chat.count_prompt_tokens.call_args.args[-1], 21600)
        self.assertEqual(self.chat.complete.call_args.args[-1], 21600)
        count = json.loads((self.root / 'prompt-count.json').read_text())
        self.assertEqual(count['prompt_tokens'], 32760)
        self.assertEqual(count['local_token_count'], case['local_token_count'])

    def test_board_range_failure_prevents_generation(self):
        self.case = cases.generate_cases(character_count)[1]
        self.chat.count_prompt_tokens.return_value = 16200
        with self.assertRaises(batch.ExecutionFailure):
            batch.request_once(self.chat, 'http://假接口', self.case, self.root)
        self.chat.complete.assert_not_called()
        self.assertEqual(json.loads((self.root / 'prompt-count.json').read_text())['prompt_tokens'], 16200)

    def test_invalid_response_metrics_fail_after_answer_saved(self):
        changes = [lambda r: r.update(finish_reason='length'),
                   lambda r: r['usage']['prompt_tokens_details'].update(cached_tokens=1),
                   lambda r: r['timings'].update(draft_n=2),
                   lambda r: r['usage'].update(completion_tokens=256),
                   lambda r: r['usage'].update(prompt_tokens=251),
                   lambda r: r.update(answer=''),
                   lambda r: r.update(reasoning_text='思考')]
        for change in changes:
            with self.subTest(change=changes.index(change)):
                value = response()
                change(value)
                self.chat.complete.return_value = value
                with self.assertRaises(batch.ExecutionFailure):
                    batch.request_once(self.chat, 'http://假接口', self.case, self.root)
                self.assertTrue((self.root / 'answer.json').exists())
                self.assertFalse((self.root / 'quality.json').exists())

    def test_partial_stream_preserved_on_transport_and_internal_errors(self):
        errors = [TimeoutError('超时'), urllib.error.URLError('断开'), ConnectionResetError('断开'),
                  http.client.IncompleteRead('尾部'.encode()), RuntimeError('completion stream ended without a finish reason'),
                  RuntimeError('内部故障'), KeyError('内部字段')]
        raw = 'data: {"choices":[{"delta":{"content":"部分回答"}}]}\n\n'
        for error in errors:
            with self.subTest(error=repr(error)):
                def complete(*args, **kwargs):
                    kwargs['stream_path'].write_text(raw)
                    raise error
                self.chat.complete.side_effect = complete
                expected = batch.ExecutionFailure if str(error) in batch.replay.STREAM_FAILURES else type(error)
                with self.assertRaises(expected):
                    batch.request_once(self.chat, 'http://假接口', self.case, self.root)
                self.assertEqual((self.root / 'stream.sse').read_text(), raw)
                self.assertEqual((self.root / 'answer.partial.txt').read_text(), '部分回答')
                self.assertFalse((self.root / 'quality.json').exists())


class MemoryTests(unittest.TestCase):
    def test_system_snapshot_numbers(self):
        row = batch.memory_sample()
        self.assertGreater(row['MemTotal'], 0)
        self.assertGreaterEqual(row['MemAvailable'], 0)
        self.assertEqual(row['rss_bytes'], 0)
        self.assertIn('SwapFree', row)

    def test_memory_limits_terminate_and_raise(self):
        for row in (memory(available=1024**3 - 1), memory(rss=12 * 1024**3 + 1)):
            with self.subTest(row=row), tempfile.TemporaryDirectory() as folder:
                process = mock.Mock(pid=123)
                process.poll.return_value = None
                sampler = batch.MemorySampler(process, Path(folder), notify=mock.Mock(), sample=lambda pid: row)
                sampler.start()
                with self.assertRaises(batch.MemoryViolation):
                    sampler.future.result(timeout=2)
                with self.assertRaises(batch.MemoryViolation):
                    sampler.close()
                process.terminate.assert_called_once()
                record = json.loads((Path(folder) / 'memory.jsonl').read_text())
                self.assertTrue(record['violation'])
                self.assertTrue((Path(folder) / 'memory-violation.json').exists())

    def test_sampler_error_propagates(self):
        with tempfile.TemporaryDirectory() as folder:
            process = mock.Mock(pid=123)
            process.poll.return_value = None
            sampler = batch.MemorySampler(process, Path(folder), notify=mock.Mock(), sample=mock.Mock(side_effect=OSError('采样失败')))
            sampler.start()
            with self.assertRaises(OSError):
                sampler.future.result(timeout=2)
            with self.assertRaises(OSError):
                sampler.close()
            process.terminate.assert_called_once()
            self.assertEqual(json.loads((Path(folder) / 'memory-error.json').read_text())['type'], 'OSError')

    def test_sample_is_on_disk_before_close(self):
        with tempfile.TemporaryDirectory() as folder:
            process = mock.Mock(pid=123)
            process.poll.return_value = None
            sampler = batch.MemorySampler(process, Path(folder), notify=mock.Mock(), sample=lambda pid: memory(available=1024**3, rss=12 * 1024**3))
            sampler.start()
            path = Path(folder) / 'memory.jsonl'
            end = time.monotonic() + 2
            while (not path.exists() or path.stat().st_size == 0) and time.monotonic() < end:
                time.sleep(.01)
            self.assertFalse(json.loads(path.read_text())['violation'])
            sampler.close()
            process.terminate.assert_not_called()

    def test_startup_memory_is_checked_for_each_unblocked_job(self):
        with tempfile.TemporaryDirectory() as folder:
            sample = mock.Mock(side_effect=[memory(available=9 * 1024**3), memory(available=0)])
            before, _ = batch.resource_hooks(Path(folder), sample)
            self.assertIsNone(before({'id': 'first'}))
            second = before({'id': 'second'})
            self.assertEqual(second['status'], 'blocked')
            self.assertEqual(before({'id': 'third'}), second)
            self.assertEqual(sample.call_count, 2)
            self.assertEqual(json.loads(Path(second['evidence'][0]).read_text())['MemAvailable'], 0)

    def test_startup_shared_failure_blocks_without_recheck(self):
        with tempfile.TemporaryDirectory() as folder:
            sample = mock.Mock(return_value=memory(available=8 * 1024**3 - 1))
            before, after = batch.resource_hooks(Path(folder), sample)
            first = before({'id': 'first'})
            second = before({'id': 'second'})
            self.assertEqual(first['status'], 'blocked')
            self.assertEqual(first, second)
            sample.assert_called_once_with()
            self.assertTrue(Path(first['evidence'][0]).exists())
            jobs = [{'id': name, 'argv': [sys.executable, '-c', 'raise AssertionError("必须阻止启动")'],
                     'timeout_s': 1, 'dependency': '2B'} for name in ('first', 'second')]
            summary = controller.run(jobs, Path(folder) / 'blocked-batch', before=before, after=after)
            self.assertFalse(summary['batch_success'])
            self.assertEqual(summary['counts']['blocked'], 2)
            sample.assert_called_once_with()


class BatchTests(unittest.TestCase):
    def test_freeze_matrix_deadlines(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            generated = cases.generate_cases(character_count)
            jobs = batch.prepare_jobs(root, {}, ['2B', '4B'], generated)
            self.assertEqual(len(jobs), 12)
            self.assertEqual(sum(job['id'].endswith('short') for job in jobs), 4)
            self.assertEqual([job['timeout_s'] for job in jobs[:3]], [1260, 11160, 21960])
            self.assertEqual(len(list((root / 'configs').glob('*.json'))), 12)
            self.assertEqual(json.loads((root / 'protocol.json').read_text())['retries'], 0)
            for job in jobs:
                self.assertTrue(Path(job['argv'][-1]).exists())
            with self.assertRaises(FileExistsError):
                batch.prepare_jobs(root, {}, ['2B'], generated)

    def test_effective_defaults_only_context_changes(self):
        effective = base.load_module('test_long_effective', EFFECTIVE_PATH)
        text = 'K1_EFFECTIVE_DEFAULTS threads=4 batch_threads=4 batch=32 ubatch=32 context=36864 slots=1 flash=1 gpu=0 key=f16 value=f16 mask=3'
        self.assertEqual(batch.verify_effective(effective, text, 36864)['context'], '36864')
        for changed in (text.replace('threads=4', 'threads=5'), text.replace('flash=1', 'flash=0'),
                        text.replace('context=36864', 'context=12288'), text + '\n' + text):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                batch.verify_effective(effective, changed, 36864)

    def test_execute_launch_stop_and_sampler_failure(self):
        from contextlib import ExitStack
        import io
        for mode in ('success', 'sample_error', 'server_crash', 'primary_cleanup_failure'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as folder, ExitStack() as stack:
                root = Path(folder)
                result = root / 'result'
                result.mkdir()
                process = mock.Mock(pid=12345, returncode=None)
                process.poll.side_effect = lambda: process.returncode
                process.terminate.side_effect = lambda: (
                    setattr(process, 'returncode', -15) if process.returncode is None else None)
                process.wait.side_effect = lambda **kwargs: process.returncode
                text = 'K1_EFFECTIVE_DEFAULTS threads=4 batch_threads=4 batch=32 ubatch=32 context=12288 slots=1 flash=1 gpu=0 key=f16 value=f16 mask=3\n'

                def launch(*args, **kwargs):
                    kwargs['stdout'].write(text)
                    kwargs['stdout'].flush()
                    return process

                case = cases.generate_cases(character_count)[0]
                runtime = {key: '/固定/' + key for key in batch.batch.RUNTIME_KEYS}
                config = {'root': str(root), 'runtime': runtime, 'model': '2B', 'case': case, 'port': 18088}
                chat = mock.Mock()
                chat.count_prompt_tokens.return_value = 250
                chat.complete.return_value = response()
                if mode == 'server_crash':
                    def crash_after_answer(*args, **kwargs):
                        process.returncode = -11
                        return response()
                    chat.complete.side_effect = crash_after_answer
                if mode == 'primary_cleanup_failure':
                    def primary_failure(*args, **kwargs):
                        process.returncode = -11
                        raise KeyError('原始内部错误')
                    chat.complete.side_effect = primary_failure
                    original_close = batch.MemorySampler.close

                    def close_failure(sampler):
                        original_close(sampler)
                        raise OSError('附加采样错误')
                    stack.enter_context(mock.patch.object(batch.MemorySampler, 'close', close_failure))
                effective = base.load_module('test_execute_effective', EFFECTIVE_PATH)
                stack.enter_context(mock.patch.object(base, 'verify_inputs', return_value=({'2B': '/固定/model.gguf'}, {'checked': True})))
                stack.enter_context(mock.patch.object(base, 'load_module', side_effect=[chat, effective]))
                popen = stack.enter_context(mock.patch.object(batch.subprocess, 'Popen', side_effect=launch))
                stack.enter_context(mock.patch.object(base, 'verify_speculation', return_value={'draft': 0}))
                props = io.StringIO(json.dumps({'total_slots': 1, 'default_generation_settings': {'n_ctx': 12288}}))
                stack.enter_context(mock.patch.object(batch.urllib.request, 'urlopen', return_value=props))
                original_sampler = batch.MemorySampler
                notification = stack.enter_context(mock.patch.object(batch.os, 'kill', wraps=batch.os.kill))

                def sample(pid):
                    if mode == 'sample_error':
                        raise OSError('内存文件读取失败')
                    return memory()

                stack.enter_context(mock.patch.object(batch, 'MemorySampler', side_effect=lambda process, folder, notify: original_sampler(process, folder, notify, sample=sample)))

                def ready(*args):
                    end = time.monotonic() + 2
                    while time.monotonic() < end:
                        if mode == 'sample_error':
                            time.sleep(.01)
                        else:
                            path = result / 'memory.jsonl'
                            if path.exists() and path.stat().st_size:
                                return
                            time.sleep(.01)
                    raise AssertionError('采样线程未通知主线程')

                stack.enter_context(mock.patch.object(base, 'wait_ready', side_effect=ready))
                old_handler = signal.getsignal(signal.SIGUSR1)
                if mode == 'sample_error':
                    with self.assertRaisesRegex(OSError, '内存文件读取失败'):
                        batch.execute(config, result)
                    self.assertFalse((result / 'quality.json').exists())
                    self.assertTrue((result / 'memory-error.json').exists())
                    notification.assert_called_once_with(os.getpid(), signal.SIGUSR1)
                elif mode == 'primary_cleanup_failure':
                    with self.assertRaisesRegex(KeyError, '原始内部错误'):
                        batch.execute(config, result)
                    self.assertEqual(json.loads((result / 'server-cleanup-error.json').read_text())['type'], 'ExecutionFailure')
                    self.assertEqual(json.loads((result / 'sampler-cleanup-error.json').read_text())['type'], 'OSError')
                elif mode == 'server_crash':
                    with self.assertRaisesRegex(batch.ExecutionFailure, '服务器退出状态异常：-11'):
                        batch.execute(config, result)
                    self.assertTrue((result / 'answer.json').exists())
                    self.assertEqual(json.loads((result / 'exit.json').read_text())['returncode'], -11)
                else:
                    self.assertEqual(batch.execute(config, result)['status'], 'passed')
                    self.assertTrue((result / 'identity.json').exists())
                    self.assertTrue((result / 'effective.json').exists())
                    self.assertTrue((result / 'props.json').exists())
                self.assertEqual(signal.getsignal(signal.SIGUSR1), old_handler)
                self.assertIsNotNone(process.returncode)
                if mode == 'success':
                    process.wait.assert_called()
                launch_record = json.loads((result / 'launch.json').read_text())
                self.assertEqual(launch_record['argv'], ['/固定/server', '-m', '/固定/model.gguf', '--alias', 'local',
                                                       '--host', '127.0.0.1', '--port', '18088', '-c', '12288', '--log-verbosity', '4'])
                self.assertEqual(launch_record['environment']['SPINE_SPEC_MAX_ACTIVE'], '0')
                self.assertEqual(popen.call_args.kwargs['pass_fds'], (9,))

    def test_worker_internal_error_propagates(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            config = root / 'config.json'
            config.write_text(json.dumps({'attempt': str(root)}))
            old = signal.getsignal(signal.SIGTERM)
            try:
                with mock.patch.object(batch, 'execute', side_effect=KeyError('内部错误')):
                    with self.assertRaises(KeyError):
                        batch.worker(config)
            finally:
                signal.signal(signal.SIGTERM, old)
            self.assertFalse((root / 'outcome.json').exists())

    def test_controller_continues_all_failure_types(self):
        worker_source = '''
import json, os, sys, time
from pathlib import Path
from unittest import mock
import long_context_batch as b
import long_context_cases as c
from test_long_context_batch import response, memory
root, mode = Path(sys.argv[1]), sys.argv[2]
config = root / 'config.json'
config.write_text(json.dumps({'attempt': str(root)}))
def execute(config, folder):
    if mode == 'crash':
        os.kill(os.getpid(), 9)
    if mode == 'timeout':
        time.sleep(10)
    if mode in ('memory', 'sample_error'):
        process = mock.Mock(pid=123)
        process.poll.return_value = None
        def sample(pid):
            if mode == 'sample_error':
                raise OSError('采样内部错误')
            return memory(available=0)
        sampler = b.MemorySampler(process, folder, notify=mock.Mock(), sample=sample)
        sampler.start()
        try:
            sampler.future.result(timeout=2)
        finally:
            sampler.close()
    case = {'level': 'short', 'messages': [], 'payload_settings': c.payload_settings(),
            'local_token_count': 250, 'reference': {}}
    chat = mock.Mock()
    chat.count_prompt_tokens.return_value = 250
    def complete(*args, **kwargs):
        kwargs['stream_path'].write_text('data: {"choices":[{"delta":{"content":"部分回答"}}]}\\n\\n')
        if mode == 'network':
            raise ConnectionResetError('连接断开')
        if mode == 'assertion':
            raise AssertionError('内部断言')
        answer = response()
        if mode == 'truncate':
            answer['finish_reason'] = 'length'
        return answer
    chat.complete.side_effect = complete
    return b.request_once(chat, 'http://假接口', case, folder)
with mock.patch.object(b, 'execute', side_effect=execute):
    sys.exit(b.worker(config))
'''
        modes = ('truncate', 'timeout', 'network', 'crash', 'assertion', 'memory', 'sample_error', 'success')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            jobs = []
            for mode in modes:
                jobs.append({'id': mode, 'argv': [sys.executable, '-c', 'import sys; sys.path.insert(0, ' + repr(str(Path(__file__).parent.resolve())) + ')\n' + worker_source,
                                                 str(root / 'batch' / 'attempts' / mode), mode],
                             'timeout_s': .3 if mode == 'timeout' else 5, 'dependency': '2B'})
            summary = controller.run(jobs, root / 'batch')
            self.assertFalse(summary['batch_success'])
            self.assertEqual(summary['settled'], 8)
            self.assertEqual(summary['counts'], {'passed': 1, 'failed': 3, 'incomplete': 4, 'blocked': 0, 'unattempted': 0})
            self.assertEqual(summary['attempts'][-1]['status'], 'passed')
            for attempt in summary['attempts'][:-1]:
                self.assertNotEqual(attempt['status'], 'passed')
            for mode in ('truncate', 'network', 'assertion'):
                path = root / 'batch' / 'attempts' / mode / 'result'
                self.assertEqual((path / 'answer.partial.txt').read_text(), '部分回答')
                self.assertTrue((path / 'stream.sse').exists())
            self.assertEqual(controller.exit_code(summary), 2)

    def test_root_gate_scope_and_fd_inheritance(self):
        from contextlib import nullcontext
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            generated = cases.generate_cases(character_count)
            (root / 'cases.json').write_text(json.dumps(generated, ensure_ascii=False))
            summary = {'counts': {'passed': 12}, 'batch_success': True}
            with mock.patch.object(batch.batch, 'board_lock', return_value=nullcontext()) as lock, \
                    mock.patch.object(batch.controller, 'run', return_value=summary) as run:
                self.assertEqual(batch.run_batch(root, {'lock': '/锁'}, ['2B', '4B']), 0)
            lock.assert_called_once_with('/锁')
            self.assertEqual(run.call_args.kwargs['pass_fds'], (9,))
            status = json.loads((root / 'batch-status.json').read_text())
            self.assertIsNone(status['quality_acceptance'])
            self.assertEqual(status['quality_review'], 'pending')
            self.assertEqual(status['gate_scope'], 'execution_only')


if __name__ == '__main__':
    unittest.main()
