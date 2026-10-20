"""检查真实路由批次的数值、配对和传输边界。"""
import copy
import http.client
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import diagnostic as base
import router_cases
import router_e2e as bench


class RouterE2ETests(unittest.TestCase):
    def response(self, route, wall):
        return {'answer': '完整答案', 'ttft_s': 1.0, 'wall_s': wall, 'finish_reason': 'stop',
            'usage': {'prompt_tokens': 20, 'completion_tokens': 10, 'prompt_tokens_details': {'cached_tokens': 0}},
            'timings': {'prompt_n': 20, 'predicted_n': 10, 'prompt_ms': 1.0, 'predicted_ms': 1000.0,
                        'draft_n': 6 if route == 'prefix' else 0, 'draft_n_accepted': 2 if route == 'prefix' else 0},
            'server_slot': 0, 'reasoning_text': '',
            'http_headers': {'x-decode-route': route, 'x-route-reason': 'class_map', 'x-classify-ms': '3.0',
                             'x-classifier': 'ngram'}}

    def matrix(self, output, classifier_name='ngram'):
        cases = router_cases.build_cases()
        seen = []
        def complete(url, payload, timeout, display):
            case_index = len(seen) // 2
            routed = url == 'http://gateway'
            route = 'prefix' if routed and case_index < 3 else 'direct'
            wall = 8.0 if routed and route == 'prefix' else 10.0
            seen.append((url, copy.deepcopy(payload)))
            response = self.response(route, wall + (0.08 if routed and classifier_name == 'bert' else 0))
            response['http_headers']['x-classifier'] = classifier_name
            if classifier_name == 'bert':
                response['http_headers']['x-classify-ms'] = '80'
            return response
        chat = SimpleNamespace(request_body=lambda messages, *args: {'messages': messages},
            count_prompt_tokens=lambda *args: 20, complete=complete)
        assessor = SimpleNamespace(assess=lambda case, *args: {'passed': False if case['category'] == 'code' else None})
        args = SimpleNamespace(output=output, quality=Path('quality.py'), max_tokens=base.MAX_TOKENS,
                               classifier_name=classifier_name)
        with mock.patch.object(bench, 'resources', return_value={'observed': 1}):
            rows = bench.run_matrix(args, cases, chat, assessor, 'http://direct', 'http://gateway', {})
        return cases, rows, seen

    def test_discovery_case_counts_and_families_are_accepted_only_in_trace_mode(self):
        import discovery_cases
        cases = discovery_cases.build_cases()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'cases.json'
            path.write_text(json.dumps(cases, ensure_ascii=False))
            policy = SimpleNamespace(request_text=lambda case: case['messages'][-1]['content'])
            self.assertEqual(len(bench.read_cases(path, policy, None, discovery_cases.FAMILIES)), len(cases))
            with self.assertRaisesRegex(ValueError, 'categories or counts'):
                bench.read_cases(path, policy)
            with self.assertRaisesRegex(ValueError, 'code task'):
                bench.read_cases(path, policy, None, ('other_family',))

    def test_tool_receipt_names_separate_the_assessor_from_router_cases(self):
        root = Path('/input')
        args = SimpleNamespace(router=root / 'router', cases_module=root / 'tools/discovery_cases.py',
                               cases=root / 'cases.json', diagnostic_plan=root / 'diagnostic-plan.json',
                               legacy_request=root / 'legacy-request.json', bert_model=root / 'encoder.gguf',
                               bert_head=root / 'bert-head.json')
        extras = bench.tool_extras(args, True)
        self.assertNotIn('router_cases', extras)
        self.assertEqual(extras['cases_module'], args.cases_module)
        self.assertEqual(extras['cases_module'].name, extras['discovery_cases'].name)
        self.assertEqual(extras['bert_model'], args.bert_model)
        self.assertIn('router_request_lease.py', extras)
        self.assertEqual(len(set(extras)), len(extras))

    def test_live_mode_rejects_incomplete_or_mixed_controls(self):
        import contextlib
        import io
        argv = []
        for name in ('output', 'server', 'models', 'spert', 'tcm', 'manifest', 'build-receipt',
                     'chat', 'quality', 'effective', 'tool-receipt', 'cases', 'cases-module', 'router'):
            argv.extend(['--' + name, 'unused'])
        for options in [('--diagnostic-plan', 'plan.json'), ('--serve', '--code-controls')]:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as failed:
                bench.main(argv + list(options))
            self.assertEqual(failed.exception.code, 2)

    def test_backend_trace_and_fallback_are_explicit_and_recorded(self):
        from contextlib import ExitStack
        import json
        original_read = Path.read_text
        for enabled in (False, True):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                args = SimpleNamespace(output=root, server=Path('/server'),
                    effective_module=SimpleNamespace(verify=lambda *args: {}))
                process = SimpleNamespace(pid=123, poll=lambda: 0, returncode=0)
                observed = {}
                def launch(command, **kwargs):
                    observed.update(kwargs['env'])
                    return process
                def read(path, *args, **kwargs):
                    if str(path) == '/proc/123/environ':
                        return '\0'.join(key + '=' + value for key, value in observed.items())
                    return original_read(path, *args, **kwargs)
                class Reply:
                    def __enter__(self): return self
                    def __exit__(self, *args): pass
                    def read(self):
                        return json.dumps({'total_slots': 1, 'default_generation_settings': {'n_ctx': base.CONTEXT}}).encode()
                with ExitStack() as stack, mock.patch.object(bench.subprocess, 'Popen', side_effect=launch), \
                     mock.patch.object(base, 'wait_ready'), mock.patch.object(base, 'verify_speculation', return_value={}), \
                     mock.patch.object(Path, 'read_text', read), \
                     mock.patch.object(bench.urllib.request, 'urlopen', return_value=Reply()):
                    bench.start_backend(stack, args, 'libs', 'prefix', Path('/model'), 18111,
                                        trace=enabled, lowacc=enabled)
                record = json.loads((root / 'backends/prefix/launch.json').read_text())
                self.assertEqual(record['environment']['SPINE_SPEC_LOWACC'], '1' if enabled else '0')
                self.assertEqual(record['environment']['SPINE_SPEC_RS'], '0')
                self.assertEqual(record['environment'].get('LLAMA_TRACE'), '1' if enabled else None)

    def test_complete_numeric_matrix_keeps_failed_quality_and_pairs(self):
        with tempfile.TemporaryDirectory() as temporary:
            cases, rows, seen = self.matrix(Path(temporary))
        self.assertEqual(len(rows), 24)
        for index in range(12):
            self.assertEqual(seen[2 * index][1], seen[2 * index + 1][1])
            self.assertFalse(seen[2 * index][1]['cache_prompt'])
            self.assertEqual(seen[2 * index][0], 'http://direct' if index % 2 == 0 else 'http://gateway')
        result = bench.summarize(cases, rows)
        self.assertEqual(result['baseline_total_s'], 120.0)
        self.assertEqual(result['routed_total_s'], 114.0)
        self.assertAlmostEqual(result['wall_reduction_pct'], 5.0)
        self.assertAlmostEqual(result['categories']['code']['paired_slowdown_mean_pct'], -20.0)
        self.assertEqual(result['routes'], {'prefix': 3, 'direct': 9})
        self.assertTrue(result['category_speed_gate'])
        self.assertIsNone(result['noncode_review'])
        self.assertIsNone(result['quality_gate'])
        self.assertIsNone(result['adoption_gate'])
        self.assertEqual(len(result['code_checks']['routed']), 3)
        self.assertTrue(all(r['passed'] is False for r in result['code_checks']['routed']))

    def test_bert_numeric_matrix_includes_classification_cost_and_requires_live_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            cases, rows, seen = self.matrix(Path(temporary), classifier_name='bert')
        result = bench.summarize(cases, rows)
        self.assertEqual(len(rows), 24)
        self.assertAlmostEqual(result['routed_total_s'], 114.96)
        self.assertAlmostEqual(result['wall_reduction_pct'], 4.2)
        self.assertEqual([r['classify_ms'] for r in rows if r['arm'] == 'routed'], [80.0] * 12)
        response = self.response('prefix', 8.0)
        with self.assertRaisesRegex(ValueError, 'classifier'):
            bench.response_route(response, 'routed', classifier_name='bert')
        response['http_headers']['x-classifier'] = 'bert'
        self.assertEqual(bench.response_route(response, 'routed', classifier_name='bert'), ('prefix', 3.0))

    def test_manual_prefix_matrix_uses_fixed_code_cases_and_header_override(self):
        cases = [case for case in router_cases.build_cases() if case['category'] == 'code']
        seen = []
        def complete(url, payload, timeout, display, headers=None):
            manual = headers == {'X-Decode-Mode': 'prefix'}
            seen.append((url, copy.deepcopy(payload), headers))
            response = self.response('prefix' if manual else 'direct', 8.0 if manual else 10.0)
            if manual:
                response['http_headers'].update({'x-route-reason': 'manual', 'x-classify-ms': '0'})
            return response
        chat = SimpleNamespace(request_body=lambda messages, *args: {'messages': messages},
            count_prompt_tokens=lambda *args: 20, complete=complete)
        assessor = SimpleNamespace(assess=lambda *args: {'passed': True})
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(bench, 'resources', return_value={}):
            rows = bench.run_matrix(SimpleNamespace(output=Path(temporary), quality=Path('quality.py'), max_tokens=base.MAX_TOKENS,
                                               classifier_name='ngram'),
                cases, chat, assessor, 'http://direct', 'http://gateway', {}, bench.CONTROL_CANDIDATE)
        self.assertEqual(len(rows), 6)
        for index in range(3):
            self.assertEqual(seen[2 * index][1], seen[2 * index + 1][1])
        result = bench.summarize(cases, rows, bench.CONTROL_CANDIDATE)
        self.assertEqual(result['routes'], {'prefix': 3})
        self.assertEqual(result['baseline_total_s'], 30.0)
        self.assertEqual(result['routed_total_s'], 24.0)
        self.assertAlmostEqual(result['wall_reduction_pct'], 20.0)
        self.assertEqual(set(result['categories']), {'code'})

    def test_category_gate_fails_despite_overall_gain_and_missing_pair_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            cases, rows, _ = self.matrix(Path(temporary))
        for row in rows:
            if row['arm'] == 'routed' and row['category'] == 'qa':
                row['response']['wall_s'] = 10.4
        result = bench.summarize(cases, rows)
        self.assertGreater(result['wall_reduction_pct'], 0)
        self.assertFalse(result['categories']['qa']['speed_gate'])
        self.assertFalse(result['category_speed_gate'])
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            bench.summarize(cases, rows[:-1])
        with self.assertRaisesRegex(ValueError, 'repeated'):
            bench.summarize(cases, rows + [rows[0]])

    def test_exact_speed_boundary_and_new_code_error_gate(self):
        with tempfile.TemporaryDirectory() as temporary:
            cases, rows, _ = self.matrix(Path(temporary))
        for row in rows:
            if row['category'] == 'qa' and row['arm'] == 'routed':
                row['response']['wall_s'] = 10.3
        result = bench.summarize(cases, rows)
        self.assertEqual(result['categories']['qa']['paired_slowdown_mean_pct'], 3.0)
        self.assertTrue(result['categories']['qa']['speed_gate'])
        for row in rows:
            if row['category'] == 'qa' and row['arm'] == 'routed':
                row['response']['wall_s'] = 10.3001
        self.assertFalse(bench.summarize(cases, rows)['categories']['qa']['speed_gate'])
        for row in rows:
            if row['case_id'] == 'clamp_values' and row['arm'] == 'baseline':
                row['quality']['passed'] = True
        result = bench.summarize(cases, rows)
        self.assertEqual(result['new_code_failures'], ['clamp_values'])
        self.assertFalse(result['quality_gate'])
        self.assertFalse(result['adoption_gate'])

    def test_live_route_must_match_draft_activity_and_classification_headers(self):
        response = self.response('prefix', 8.0)
        route, cost = bench.response_route(response, 'routed')
        self.assertEqual((route, cost), ('prefix', 3.0))
        response['timings'].update(draft_n=0, draft_n_accepted=0)
        with self.assertRaisesRegex(ValueError, 'no drafts'):
            base.validate_response(response, 20, 'mtp' if route == 'prefix' else 'direct')
        for key, value in [('x-decode-route', 'full'), ('x-route-reason', 'manual'), ('x-classify-ms', 'nan')]:
            damaged = self.response('prefix', 8.0)
            damaged['http_headers'][key] = value
            with self.assertRaises(ValueError):
                bench.response_route(damaged, 'routed')

    def test_explicit_output_budget_keeps_natural_stop_and_cap_gates(self):
        response = self.response('direct', 1000.0)
        response['usage']['completion_tokens'] = 3000
        response['timings']['predicted_n'] = 3000
        with self.assertRaisesRegex(ValueError, 'cap'):
            base.validate_response(response, 20, 'direct')
        metrics = base.validate_response(response, 20, 'direct', max_tokens=4096)
        self.assertEqual(metrics['completion_tokens'], 3000)
        response['finish_reason'] = 'length'
        with self.assertRaisesRegex(ValueError, 'naturally'):
            base.validate_response(response, 20, 'direct', max_tokens=4096)
        response['finish_reason'] = 'stop'
        response['usage']['completion_tokens'] = 4096
        response['timings']['predicted_n'] = 4096
        with self.assertRaisesRegex(ValueError, 'cap'):
            base.validate_response(response, 20, 'direct', max_tokens=4096)

    def test_sse_drains_after_done_and_rejects_missing_or_extra_done(self):
        path = Path(__file__).parents[2] / 'serve/cached-document-chat.py'
        chat = base.load_module('router_e2e_chat_test', path)
        events = [b'data: {"choices":[{"delta":{"content":"answer"}}]}\n',
            b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n', b'data: [DONE]\n']
        class Response:
            headers = {'X-Decode-Route': 'prefix'}
            def __init__(self, records): self.records = records
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def __iter__(self): return iter(self.records)
        clock = [1.0]
        def delayed_eof():
            clock[0] = 1.2
            yield from events
            clock[0] = 1.7
        with mock.patch.object(chat.urllib.request, 'urlopen', return_value=Response(delayed_eof())), \
                mock.patch.object(chat.time, 'monotonic', side_effect=lambda: clock[0]):
            result = chat.complete('http://unit', {}, 1, display=False)
        self.assertEqual(result['wall_s'], 0.7)
        self.assertEqual(result['ttft_s'], 0.2)
        self.assertEqual(result['answer'], 'answer')
        self.assertEqual(result['http_headers']['x-decode-route'], 'prefix')
        with mock.patch.object(chat.urllib.request, 'urlopen', return_value=Response(events)) as fetch:
            chat.complete('http://unit', {'messages': []}, 1, display=False,
                          headers={'X-Decode-Mode': 'prefix'})
            self.assertEqual(fetch.call_args.args[0].get_header('X-decode-mode'), 'prefix')
        for damaged in (events[:-1], events + [events[-1]]):
            with mock.patch.object(chat.urllib.request, 'urlopen', return_value=Response(damaged)):
                with self.assertRaisesRegex(RuntimeError, 'DONE'):
                    chat.complete('http://unit', {}, 1, display=False)
        def truncated():
            yield from events
            raise http.client.IncompleteRead(b'', 1)
        with mock.patch.object(chat.urllib.request, 'urlopen', return_value=Response(truncated())):
            with self.assertRaises(http.client.IncompleteRead):
                chat.complete('http://unit', {}, 1, display=False)


if __name__ == '__main__':
    unittest.main()
