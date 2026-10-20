"""检查原始接受统计、累计计时差和完整诊断矩阵。"""
import copy
from contextlib import nullcontext
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import router_cases
import trace_cases as probe


class TraceCasesTests(unittest.TestCase):
    def plan(self):
        return {'prefix_rows': 10, 'stages': [
            {'category': 'code', 'repeats': 3}, {'category': 'chinese', 'repeats': 2},
            {'category': 'qa', 'repeats': 2}, {'category': 'long_document', 'repeats': 1}]}

    def fragment(self, task=7):
        lines = [('0.01.000.000', '1/ 3', True), ('0.01.100.000', '2/ 2', False),
                 ('0.02.000.000', '0/ 3', True), ('0.02.200.000', '1/ 1', False),
                 ('0.03.000.000', '3/ 3', False)]
        return '\n'.join(f'{stamp} I slot operator(): id 0 | task {task} | accepted {counts} draft tokens' +
                         (' (restore checkpoint)' if restore else '') for stamp, counts, restore in lines) + '\n'

    def test_original_acceptance_replay_and_real_timestamp_format(self):
        counts = probe.analyze_trace(self.fragment(), {'draft_n': 9, 'draft_n_accepted': 6}, 'prefix')
        self.assertEqual(counts['original_proposed'], 9)
        self.assertEqual(counts['original_first_accepted'], 4)
        self.assertEqual(counts['original_first_acceptance'], 4 / 9)
        self.assertEqual(counts['original_restore_fraction'], 2 / 3)
        self.assertEqual(counts['accept_histogram'], {'1': 1, '0': 1, '3': 1})
        self.assertEqual(counts['replay_accepted'], 3)
        self.assertEqual(counts['replay_gap_ms'], [100.0, 200.0])
        with self.assertRaisesRegex(ValueError, 'proposal total'):
            probe.analyze_trace(self.fragment(), {'draft_n': 12, 'draft_n_accepted': 6}, 'prefix')
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            probe.analyze_trace(self.fragment() + self.fragment(task=8), {'draft_n': 18, 'draft_n_accepted': 12}, 'prefix')
        with self.assertRaisesRegex(ValueError, 'direct backend'):
            probe.analyze_trace(self.fragment(), {}, 'direct')
        with self.assertRaisesRegex(ValueError, 'timestamp'):
            probe.analyze_trace(self.fragment().replace('0.01.000.000', 'no-time'),
                                {'draft_n': 9, 'draft_n_accepted': 6}, 'prefix')
        with self.assertRaisesRegex(ValueError, 'restored queue'):
            probe.analyze_trace(self.fragment().replace('2/ 2', '3/ 3'),
                                {'draft_n': 9, 'draft_n_accepted': 7}, 'prefix')

    def test_prefix_rows_use_actual_gguf_head(self):
        from test_model_head_check import _fixture
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'model.gguf'
            _fixture(path, True)
            probe.verify_prefix_rows(path, 2)
            with self.assertRaisesRegex(ValueError, 'actual model'):
                probe.verify_prefix_rows(path, 3)

    def test_plan_and_native_cumulative_statistics(self):
        self.assertEqual(probe.validate_plan(self.plan())['prefix_rows'], 10)
        for mutation in [dict(self.plan(), prefix_rows=True),
                         dict(self.plan(), stages=self.plan()['stages'][:3])]:
            with self.assertRaises(ValueError): probe.validate_plan(mutation)
        invalid = self.plan()
        invalid['stages'][0]['repeats'] = True
        with self.assertRaises(ValueError): probe.validate_plan(invalid)
        self.assertEqual(probe.cumulative_stats('startup'), (0, 0, 0))
        with self.assertRaisesRegex(ValueError, 'timing is absent'):
            probe.cumulative_stats('startup', required=True)
        rows = ('I spec common_specu: statistics draft-mtp: dur(b,g,a) = 1.0, 10.0, 2.0 ms\n'
                'I spec common_specu: statistics draft-mtp: dur(b,g,a) = 2.0, 25.0, 4.0 ms\n')
        self.assertEqual(probe.cumulative_stats(rows), (2, 25, 4))

    def test_discovery_queue_has_294_requests_and_reverses_second_round(self):
        import discovery_cases
        plan = self.plan()
        plan['case_order'] = 'reverse_alternate'
        for stage in plan['stages']:
            stage['repeats'] = 2
        legacy = {'case_id': 'legacy_unicode_runs', 'category': 'code'}
        queue = probe.schedule(probe.validate_plan(plan), discovery_cases.build_cases(), legacy)
        self.assertEqual(len(queue), 294)
        self.assertEqual(sum(stage == 'code' for stage, repeat, case, arm in queue), 150)
        self.assertEqual([case['case_id'] for stage, repeat, case, arm in queue[:3]], ['legacy_unicode_runs'] * 3)
        second = [case['case_id'] for stage, repeat, case, arm in queue if stage == 'code' and repeat == 2]
        self.assertEqual(second[-3:], ['legacy_unicode_runs'] * 3)
        self.assertEqual(second[:3], ['code_interval_union_en_zh'] * 3)

    def test_full_81_requests_continue_after_quality_failures(self):
        cases = router_cases.build_cases()
        calls = dict.fromkeys(probe.ARMS, 0)
        seen = []
        class Reply:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return b'{"tokens":[1,2,12,13]}'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for arm in probe.ARMS:
                (root / 'backends' / arm).mkdir(parents=True)
                (root / 'backends' / arm / 'server.log').write_text('startup\n')
            def complete(url, payload, timeout, display):
                arm = url.rsplit('/', 1)[1]
                calls[arm] += 1
                seen.append((arm, copy.deepcopy(payload)))
                log = '0.03.100.000 I slot print_timing: id 0 | task 7 | prompt eval time = 100 ms\n'
                if arm != 'direct':
                    log += self.fragment()
                    log += f'I spec statistics draft-mtp: dur(b,g,a) = 0.0, {calls[arm] * 10}.0, 0.0 ms\n'
                with (root / 'backends' / arm / 'server.log').open('a') as stream:
                    stream.write(log)
                return {'answer': 'hello', 'wall_s': {'direct': 10, 'prefix': 14, 'lowacc': 15}[arm] + calls[arm] % 3,
                    'ttft_s': 1.0, 'finish_reason': 'stop', 'reasoning_text': '', 'server_slot': 0,
                    'usage': {'prompt_tokens': 20, 'completion_tokens': 10, 'prompt_tokens_details': {'cached_tokens': 0}},
                    'timings': {'prompt_n': 20, 'predicted_n': 10, 'prompt_ms': 100.0, 'predicted_ms': 1000.0,
                        'draft_n': 0 if arm == 'direct' else 9, 'draft_n_accepted': 0 if arm == 'direct' else 6}}
            chat = SimpleNamespace(complete=complete, count_prompt_tokens=lambda *args: 20,
                request_body=lambda messages, *args: {'messages': messages, 'seed': 42, 'temperature': 0})
            def assess(case, answer, sandbox):
                self.assertEqual(sandbox, Path('checker.py'))
                return {'passed': False if case['category'] == 'code' else None}
            assessor = SimpleNamespace(assess=assess)
            quality = SimpleNamespace(check_code=lambda *args: {'pass': True, 'checks': 106})
            args = SimpleNamespace(output=root, quality=Path('checker.py'), max_tokens=4096,
                trace_plan=probe.validate_plan(self.plan()), legacy_data={'messages': [{'role': 'user', 'content': 'legacy'}]},
                lease=SimpleNamespace(acquire=lambda path: nullcontext()), request_lock=root / 'request.lock')
            procs = {arm: SimpleNamespace(pid=99, poll=lambda: None) for arm in probe.ARMS}
            with mock.patch.object(probe.base, 'resource_snapshot', return_value={}), \
                 mock.patch.object(probe.urllib.request, 'urlopen', return_value=Reply()):
                records = probe.run(args, cases, chat, assessor, quality, procs,
                                    {arm: 'http://local/' + arm for arm in probe.ARMS})
            progress = json.loads((root / 'diagnostics/progress.json').read_text())
            self.assertEqual(progress['completed'], 81)
            self.assertEqual(progress['planned'], 81)
        self.assertEqual(len(records), 81)
        self.assertEqual([r['case_id'] for r in records[:3]], ['legacy_unicode_runs'] * 3)
        self.assertEqual([r['arm'] for r in records[:3]], list(probe.ARMS))
        self.assertTrue(all(not payload['cache_prompt'] for arm, payload in seen))
        summary = probe.summarize(records)
        self.assertEqual(summary['quality_failures'], 27)
        legacy = summary['cases']['legacy_unicode_runs']['prefix']
        self.assertEqual(legacy['samples'], 3)
        self.assertEqual(legacy['wall_mean_s'], 15.0)
        self.assertAlmostEqual(legacy['original_acceptance'], 4 / 9)
        self.assertAlmostEqual(legacy['restore_fraction'], 2 / 3)
        self.assertEqual(legacy['draft_mean_ms'], 10.0)
        self.assertEqual(legacy['coverage_mean'], .5)


if __name__ == '__main__':
    unittest.main()
