import importlib.util
import json
import os
import signal
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import urllib.error

PATH = Path(__file__).with_name('diagnostic.py')
SPEC = importlib.util.spec_from_file_location('diagnostic_under_test', PATH)
diagnostic = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(diagnostic)


class FakeResponse:
    def __init__(self, data=None, events=None):
        self.data = data
        self.events = events or []
        self.status = 200
        self.headers = {'X-Decode-Route': 'prefix'}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.data).encode()

    def __iter__(self):
        return iter(self.events)


class DiagnosticTests(unittest.TestCase):
    def good_response(self):
        return {
            'answer': 'def encode_runs(text):\n    """Encode Unicode runs."""\n    runs = []\n    for ch in text:\n        if runs and runs[-1][0] == ch:\n            runs[-1] = (ch, runs[-1][1] + 1)\n        else:\n            runs.append((ch, 1))\n    return runs\n\ndef decode_runs(runs):\n    """Decode Unicode runs."""\n    return "".join(ch * count for ch, count in runs)',
            'ttft_s': 1.2, 'wall_s': 5.5, 'finish_reason': 'stop',
            'usage': {'prompt_tokens': 20, 'completion_tokens': 30, 'prompt_tokens_details': {'cached_tokens': 0}},
            'timings': {'prompt_n': 20, 'predicted_n': 30, 'prompt_ms': 40.0,
                        'predicted_ms': 5000.0, 'draft_n': 10, 'draft_n_accepted': 6},
            'server_slot': 0, 'reasoning_text': ''}

    def test_http_sse_record_parses_complete_result(self):
        events = ['data: {"choices":[{"delta":{"content":"你好"}}]}\n'.encode('utf-8'),
                  b'data: {"choices":[{"delta":{},"finish_reason":"stop"}],"usage":{"prompt_tokens":20,"completion_tokens":2,"prompt_tokens_details":{"cached_tokens":0}},"timings":{"prompt_n":20,"predicted_n":2,"prompt_ms":1.0,"predicted_ms":2.0,"draft_n":3,"draft_n_accepted":2},"__verbose":{"id_slot":0}}\n',
                  b'data: [DONE]\n']
        with mock.patch('urllib.request.urlopen', return_value=FakeResponse(events=events)) as open_url, mock.patch('time.monotonic', side_effect=[1.0, 1.1, 2.0]):
            result = type('Chat', (), {})
            path = Path(__file__).parents[2] / 'serve/cached-document-chat.py'
            helper_spec = importlib.util.spec_from_file_location('chat_test_helper', path)
            chat = importlib.util.module_from_spec(helper_spec)
            helper_spec.loader.exec_module(chat)
            actual = chat.complete('http://unit', {}, 1, display=False)
        self.assertEqual(actual['answer'], '你好')
        self.assertEqual(actual['http_headers']['x-decode-route'], 'prefix')
        metrics = diagnostic.validate_response(actual, 20, 'mtp_lowacc')
        self.assertEqual(metrics['draft_n_accepted'], 2)
        self.assertEqual(open_url.call_count, 1)

    def test_response_validation_rejects_invalid_records(self):
        cases = [
            ('finish cap', lambda r: r.update(finish_reason='length')),
            ('token cap', lambda r: (r['usage'].update(completion_tokens=2048),
                                     r['timings'].update(predicted_n=2048))),
            ('cached', lambda r: r['usage']['prompt_tokens_details'].update(cached_tokens=1)),
            ('count', lambda r: r['timings'].update(prompt_n=19)),
            ('nonfinite', lambda r: r['timings'].update(prompt_ms=float('nan'))),
            ('no draft', lambda r: r['timings'].update(draft_n=0, draft_n_accepted=0)),
        ]
        for label, alter in cases:
            with self.subTest(label=label):
                response = self.good_response()
                alter(response)
                with self.assertRaises(ValueError):
                    diagnostic.validate_response(response, 20, 'mtp_lowacc')

    def test_direct_and_loaded_arms_reject_drafts(self):
        response = self.good_response()
        response['timings'].update(draft_n=0, draft_n_accepted=0)
        response['usage']['completion_tokens'] = 30
        response['timings']['predicted_n'] = 30
        self.assertEqual(diagnostic.validate_response(response, 20, 'direct')['draft_n'], 0)
        with self.assertRaises(ValueError):
            diagnostic.validate_response(response, 20, 'mtp')
        response['timings']['draft_n'] = 1
        response['timings']['draft_n_accepted'] = 0
        with self.assertRaises(ValueError):
            diagnostic.validate_response(response, 20, 'loaded_off')

    def test_summary_uses_known_paired_values(self):
        records = []
        walls = {'direct': (10, 10, 10), 'mtp': (9, 9, 9), 'loaded_off': (11, 11, 11), 'mtp_lowacc': (8, 8, 8)}
        for model in diagnostic.MODELS:
            for arm, samples in walls.items():
                for index, wall in enumerate(samples, 1):
                    response = {'wall_s': wall, 'ttft_s': 1.0,
                                'timings': {'prompt_ms': 2.0, 'predicted_ms': 3.0}}
                    records.append({'model': model, 'arm': arm, 'round': index, 'response': response,
                                    'metrics': {'prompt_tokens': 20, 'completion_tokens': 30,
                                                'draft_n': 0 if arm in ('direct', 'loaded_off') else 5,
                                                'draft_n_accepted': 0 if arm in ('direct', 'loaded_off') else 2},
                                    'quality': {'passed': True, 'result': {'pass': True, 'checks': 106}}})
        summary = diagnostic.summarize(records)
        self.assertTrue(summary['quality_gate'])
        self.assertEqual(summary['models']['2B']['direct']['wall_mean_s'], 10)
        self.assertAlmostEqual(summary['models']['2B']['loaded_off']['overhead_vs_direct_pct'], 10)
        self.assertAlmostEqual(summary['models']['2B']['mtp_lowacc']['wall_reduction_vs_direct_pct'], 20)
        self.assertAlmostEqual(summary['models']['2B']['mtp']['wall_reduction_vs_direct_pct'], 10)
        self.assertEqual(summary['models']['4B']['loaded_off']['wall_median_s'], 11)
        for record in records:
            baseline = (10, 20, 40)[record['round'] - 1]
            wall = {'direct': baseline, 'mtp': baseline * .9, 'loaded_off': baseline * 1.1,
                    'mtp_lowacc': (8, 18, 40)[record['round'] - 1]}[record['arm']]
            record['response']['wall_s'] = wall
        summary = diagnostic.summarize(records)
        self.assertAlmostEqual(summary['models']['2B']['mtp_lowacc']['wall_reduction_vs_direct_pct'], 10)
        records[-1]['quality']['passed'] = False
        self.assertFalse(diagnostic.summarize(records)['quality_gate'])
        records[-1]['metrics']['prompt_tokens'] = 21
        with self.assertRaisesRegex(ValueError, 'paired input token counts differ'):
            diagnostic.summarize(records)

    def test_speculation_configuration(self):
        context = 'llama_context: n_rs_seq = 0\nllama_context: n_outputs_max = 1\n'
        marker = 'K1_EFFECTIVE_DEFAULTS threads=4\n'
        direct = context + marker
        cache = 'llama_kv_cache: size = 12.00 MiB (12288 cells, 1 layers, 1/1 seqs)\n'
        mtp = context.replace('n_outputs_max = 1', 'n_outputs_max = 4') + marker + context + cache
        self.assertEqual(diagnostic.verify_speculation(direct, 'direct')['context_records'], 1)
        self.assertEqual(diagnostic.verify_speculation(mtp, 'loaded_off')['output_capacities'], [4, 1])
        self.assertEqual(diagnostic.verify_speculation(mtp, 'mtp')['target_output_capacity'], 4)
        self.assertEqual(diagnostic.verify_speculation(mtp, 'mtp_lowacc')['draft_output_capacities'], [1])
        swapped = context + marker + context.replace('n_outputs_max = 1', 'n_outputs_max = 4') + cache
        for text, arm in [(direct, 'loaded_off'), (direct + context, 'loaded_off'),
                          (direct + context + cache, 'loaded_off'), (swapped, 'mtp'),
                          (direct + context + cache, 'mtp_lowacc'), (direct + cache, 'direct'),
                          (mtp.replace('n_rs_seq = 0', 'n_rs_seq = 3'), 'mtp_lowacc'), ('', 'direct')]:
            with self.subTest(text=text, arm=arm), self.assertRaises(ValueError):
                diagnostic.verify_speculation(text, arm)

    def test_main_uses_all_pairs_and_propagates_failures(self):
        helpers = Path(__file__).parents[2]
        for bad_quality, crash in [(False, False), (True, False), (False, True)]:
            with self.subTest(bad_quality=bad_quality, crash=crash), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                request = root / 'request.json'
                request.write_text(json.dumps({'messages': [{'role': 'user', 'content': 'code task'}]}))
                argv = []
                for flag, value in {'output': root / 'out', 'server': '/server', 'models': '/models',
                                    'spert': '/spert', 'tcm': '/tcm', 'manifest': '/manifest',
                                    'build-receipt': '/receipt', 'request': request, 'tool-receipt': '/tools.json',
                                    'chat': helpers / 'serve/cached-document-chat.py',
                                    'quality': helpers / 'release-candidate/tests/quality.py',
                                    'effective': helpers / 'bench/final-default/effective.py'}.items():
                    argv += ['--' + flag, str(value)]
                seen = []
                def run_one(args, libs, chat, effective, quality, model, arm, round_no, *rest):
                    if crash:
                        raise RuntimeError('HTTP failed')
                    seen.append((model, arm, round_no))
                    response = self.good_response()
                    response['wall_s'] = {'direct': 10, 'mtp': 9, 'loaded_off': 11, 'mtp_lowacc': 8}[arm]
                    if arm in ('direct', 'loaded_off'):
                        response['timings'].update(draft_n=0, draft_n_accepted=0)
                    return {'model': model, 'arm': arm, 'round': round_no, 'response': response,
                            'metrics': diagnostic.validate_response(response, 20, arm),
                            'quality': {'passed': not bad_quality, 'result': {'pass': not bad_quality}}}
                old_term = signal.getsignal(signal.SIGTERM)
                try:
                    with mock.patch.dict(os.environ, {'TMUX': 'test'}), \
                            mock.patch.object(diagnostic, 'verify_inputs', return_value=({'2B': '/2B', '4B': '/4B'}, {})), \
                            mock.patch.object(diagnostic, 'run_one', side_effect=run_one):
                        if crash:
                            with self.assertRaisesRegex(RuntimeError, 'HTTP failed'):
                                diagnostic.main(argv)
                            self.assertFalse((root / 'out/summary.json').exists())
                        else:
                            self.assertEqual(diagnostic.main(argv), 2 if bad_quality else 0)
                            self.assertEqual(len(set(seen)), 24)
                            self.assertEqual(seen[:4], [('2B', 'direct', 1), ('2B', 'mtp', 1), ('2B', 'loaded_off', 1), ('2B', 'mtp_lowacc', 1)])
                            self.assertEqual(seen[12:16], [('4B', 'mtp_lowacc', 1), ('4B', 'loaded_off', 1), ('4B', 'mtp', 1), ('4B', 'direct', 1)])
                            summary = json.loads((root / 'out/summary.json').read_text())
                            self.assertAlmostEqual(summary['models']['2B']['mtp_lowacc']['wall_reduction_vs_direct_pct'], 20)
                            self.assertAlmostEqual(summary['models']['4B']['loaded_off']['overhead_vs_direct_pct'], 10)
                finally:
                    signal.signal(signal.SIGTERM, old_term)

    def test_environment_removes_inherited_controls(self):
        source = {'SPINE_SPEC_RS': '1', 'SPACEMIT_X': '1', 'GGML_X': '1', 'LLAMA_X': '1',
                  'OMP_NUM_THREADS': '8', 'GOMP_X': '1', 'KMP_X': '1', 'LD_PRELOAD': '/bad',
                  'LD_AUDIT': '/bad', 'LD_DEBUG': 'all', 'PATH': '/bin', 'HOME': '/tmp'}
        env = diagnostic.clean_environment(source, Path('/server:/tcm:/spert'), True)
        self.assertEqual(env, {'PATH': '/bin', 'HOME': '/tmp', 'LD_LIBRARY_PATH': '/server:/tcm:/spert',
                               'SPINE_SPEC_RS': '0', 'SPINE_SPEC_LOWACC': '1', 'SPINE_SPEC_MAX_ACTIVE': '1'})
        normal = diagnostic.clean_environment(source, '/lib', False)
        self.assertEqual(normal['SPINE_SPEC_LOWACC'], '0')
        self.assertEqual(normal['SPINE_SPEC_MAX_ACTIVE'], '1')
        disabled = diagnostic.clean_environment(source, '/lib', False, False)
        self.assertEqual(disabled['SPINE_SPEC_MAX_ACTIVE'], '0')
        self.assertEqual(disabled['SPINE_SPEC_LOWACC'], '0')
        traced = diagnostic.clean_environment(source, '/lib', True, trace=True)
        self.assertEqual(traced['LLAMA_TRACE'], '1')
        self.assertNotIn('LLAMA_TRACE', normal)

    def test_health_retries_loading_and_has_a_deadline(self):
        process = mock.Mock()
        process.poll.return_value = None
        loading = urllib.error.HTTPError('http://unit/health', 503, 'loading', {}, None)
        with mock.patch.object(diagnostic.urllib.request, 'urlopen', side_effect=[loading, FakeResponse()]) as fetch, \
                mock.patch.object(diagnostic.time, 'monotonic', side_effect=[0, 0, 1]), \
                mock.patch.object(diagnostic.time, 'sleep'):
            diagnostic.wait_ready(process, 'http://unit')
            self.assertEqual(fetch.call_count, 2)
        with mock.patch.object(diagnostic.time, 'monotonic', side_effect=[0, 241]), \
                mock.patch.object(diagnostic.urllib.request, 'urlopen') as fetch:
            with self.assertRaisesRegex(TimeoutError, 'health deadline expired'):
                diagnostic.wait_ready(process, 'http://unit')
            fetch.assert_not_called()

    def test_assessment_callback_and_abnormal_exit(self):
        for exit_code in (0, -6):
            with self.subTest(exit_code=exit_code), tempfile.TemporaryDirectory() as temp:
                child = mock.Mock(pid=12345, returncode=exit_code)
                child.poll.return_value = None
                args = type('Args', (), {'port': 1, 'server': Path('/server')})
                chat = mock.Mock()
                chat.request_body.return_value = {'messages': []}
                chat.count_prompt_tokens.return_value = 20
                chat.complete.return_value = self.good_response()
                effective = mock.Mock()
                effective.verify.return_value = {}
                assessment = mock.Mock(return_value={'passed': None, 'result': {'required_facts': ['source']}})
                original_read = Path.read_text
                def read(path, *values, **kwargs):
                    if str(path) == '/proc/12345/environ':
                        return '\0'.join(k + '=' + v for k, v in spawn.call_args.kwargs['env'].items())
                    return original_read(path, *values, **kwargs)
                props = {'total_slots': 1, 'default_generation_settings': {'n_ctx': 12288}}
                with mock.patch.object(diagnostic.subprocess, 'Popen', return_value=child) as spawn, \
                     mock.patch.object(diagnostic, 'wait_ready'), \
                     mock.patch.object(diagnostic, 'verify_speculation', return_value={}), \
                     mock.patch.object(diagnostic, 'resource_snapshot', return_value={}), \
                     mock.patch.object(Path, 'read_text', read), \
                     mock.patch('urllib.request.urlopen', return_value=FakeResponse(props)):
                    call = lambda: diagnostic.run_one(args, '/lib', chat, effective, object(),
                        '2B', 'mtp', 1, {'messages': []}, Path('/model'), Path(temp), assess=assessment, trace=True)
                    if exit_code:
                        with self.assertRaisesRegex(RuntimeError, 'server exited with code -6'):
                            call()
                    else:
                        record = call()
                        self.assertIsNone(record['quality']['passed'])
                        saved = json.loads((Path(temp) / '2B/mtp/round-1/quality.json').read_text())
                        self.assertIsNone(saved['passed'])
                    assessment.assert_called_once_with(self.good_response()['answer'])
                    self.assertEqual(spawn.call_args.kwargs['env']['LLAMA_TRACE'], '1')
                    self.assertEqual((Path(temp) / '2B/mtp/round-1/result.json').exists(), exit_code == 0)

    def test_server_error_terminates_child(self):
        class Child:
            pid = 12345
            returncode = None
            terminated = False
            def poll(self):
                return None
            def terminate(self):
                self.terminated = True
                self.returncode = -15
            def wait(self, timeout=None):
                return self.returncode
            def kill(self):
                self.returncode = -9
        child = Child()
        args = type('Args', (), {'port': 1, 'server': Path('/server')})
        request_data = {'messages': []}
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            with mock.patch.object(diagnostic.subprocess, 'Popen', return_value=child) as spawn, \
                    mock.patch('urllib.request.urlopen', side_effect=ValueError('internal failure')):
                with self.assertRaises(ValueError):
                    diagnostic.run_one(args, '/lib', object(), object(), object(), '2B', 'direct', 1,
                                       request_data, Path('/model'), output)
            self.assertTrue(child.terminated)
            argv = spawn.call_args.args[0]
            self.assertEqual(argv[argv.index('--log-verbosity') + 1], '4')
            exit_record = json.loads((output / '2B/direct/round-1/server-exit.json').read_text())
            self.assertEqual(exit_record['returncode'], -15)

    def test_tool_receipt_mismatch_names_the_differing_keys(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            helpers = {}
            for name in ('chat', 'quality', 'effective'):
                path = root / (name + '.py')
                path.write_text('# 固定辅助模块。\n')
                helpers[name] = path
            receipt = root / 'tools.json'
            receipt.write_text(json.dumps({'diagnostic': 'a', 'chat': 'b', 'quality': 'c',
                                           'effective': 'd', 'extra': 'e'}))
            args = type('Args', (), {'server': Path('/server'), 'models': root, 'port': 1,
                                     'tool_receipt': receipt, **helpers})
            with mock.patch.dict(os.environ, {'K1_PACKAGE_LOCK_FD': '9'}), \
                    mock.patch.object(diagnostic.os, 'fstat'), \
                    mock.patch.object(diagnostic.subprocess, 'run',
                                      return_value=type('Done', (), {'returncode': 1})), \
                    mock.patch.object(diagnostic.socket, 'socket') as socket:
                socket.return_value.__enter__.return_value.connect_ex.return_value = 1
                with self.assertRaises(ValueError) as failed:
                    diagnostic.verify_inputs(args, model_names=())
        message = str(failed.exception)
        self.assertIn("missing=['extra']", message)
        self.assertIn('extra=[]', message)
        self.assertIn("'chat'", message)
        self.assertIn('changed=', message)


if __name__ == '__main__':
    unittest.main()
