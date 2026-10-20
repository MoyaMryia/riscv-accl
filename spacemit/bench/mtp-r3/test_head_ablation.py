import json
import os
from pathlib import Path
import signal
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import head_ablation as ablation

HERE = Path(__file__).parent
QUALITY = ablation.base.load_module('ablation_test_quality', HERE.parents[1] / 'release-candidate/tests/quality.py')
CASES = ablation.base.load_module('ablation_test_cases', HERE / 'general_cases.py')


class HeadAblationTests(unittest.TestCase):
    def test_replay_is_separate_from_original_proposals(self):
        events = [{'accepted': 0, 'drafted': 3, 'restore_checkpoint': True},
                  {'accepted': 1, 'drafted': 1, 'restore_checkpoint': False},
                  {'accepted': 3, 'drafted': 3, 'restore_checkpoint': False}]
        result = ablation.verification_counts(events)
        self.assertEqual(result['original_proposed'], 6)
        self.assertEqual(result['original_first_accepted'], 3)
        self.assertEqual(result['original_first_acceptance'], .5)
        self.assertEqual(result['replay_steps'], 1)
        self.assertEqual(result['replay_accepted'], 1)
        self.assertEqual(result['replay_restores'], 0)
        events.insert(1, {'accepted': 0, 'drafted': 1, 'restore_checkpoint': True})
        result = ablation.verification_counts(events)
        self.assertEqual(result['original_proposed'], 6)
        self.assertEqual(result['replay_steps'], 2)
        self.assertEqual(result['replay_restores'], 1)
        self.assertIsNone(ablation.verification_counts([])['original_first_acceptance'])

    def test_trace_checks_drop_and_corrupt_real_events(self):
        events = [{'accepted': 0, 'drafted': 3, 'restore_checkpoint': True},
                  {'accepted': 1, 'drafted': 1, 'restore_checkpoint': False},
                  {'accepted': 3, 'drafted': 3, 'restore_checkpoint': False}]
        metrics = {'draft_n': 6, 'draft_n_accepted': 4}
        result = ablation.verify_trace(events, metrics)
        self.assertEqual(result['original_first_accepted'], 3)
        self.assertEqual(result['original_first_acceptance'], .5)
        for bad in (events[1:], events[:-1], [events[0], events[2]],
                    [dict(events[0], accepted=1), *events[1:]],
                    [events[0], dict(events[1], accepted=0), events[2]],
                    [dict(events[0], accepted=3), *events[1:]]):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                ablation.verify_trace(bad, metrics)
        with self.assertRaisesRegex(ValueError, 'ends before'):
            ablation.verify_trace(events[:1], {'draft_n': 3, 'draft_n_accepted': 0})
        with self.assertRaisesRegex(ValueError, 'completion total'):
            ablation.verify_trace(events, {'draft_n': 6, 'draft_n_accepted': 5})
        self.assertEqual(ablation.verify_trace([], {'draft_n': 0, 'draft_n_accepted': 0})['original_steps'], 0)

    def test_main_twelve_requests_models_times_and_failure_behavior(self):
        cases = []
        for category in ('code', 'chinese', 'qa', 'long_document'):
            cases.append(next(c for c in CASES.build_cases(QUALITY) if c['category'] == category))
        for failure, crash in [(False, False), (True, False), (False, True)]:
            with self.subTest(failure=failure, crash=crash), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                source = root / 'cases.json'
                source.write_text(json.dumps(cases))
                argv = []
                for flag, value in {'output': root / 'out', 'server': '/server', 'models': '/models',
                    'spert': '/spert', 'tcm': '/tcm', 'manifest': '/manifest', 'request': source,
                    'build-receipt': '/receipt', 'tool-receipt': '/tools.json', 'full-model': '/full',
                    'chat': HERE.parents[1] / 'serve/cached-document-chat.py',
                    'quality': HERE.parents[1] / 'release-candidate/tests/quality.py',
                    'effective': HERE.parent / 'final-default/effective.py'}.items():
                    argv += ['--' + flag, str(value)]
                comparison = {'prefix_head': {'shape': [2048, 65536]}, 'vocabulary_rows': 248320}
                model_check = SimpleNamespace(compare_models=mock.Mock(return_value=comparison))
                loader = ablation.base.load_module
                def load(name, path):
                    if path.name == 'model_head_check.py':
                        return model_check
                    return loader(name, path)
                seen = []
                def run_one(args, libs, chat, effective, quality, model, arm, round_no,
                            case, model_path, output, *, assess, trace):
                    if crash:
                        raise RuntimeError('transport failure')
                    self.assertEqual(model, '2B')
                    self.assertTrue(trace)
                    variant = output.name
                    self.assertEqual(model_path, Path('/full') if variant == 'full' else Path('/prefix'))
                    self.assertEqual(arm, 'direct' if variant == 'direct' else 'mtp')
                    seen.append((case['case_id'], variant))
                    folder = output / '2B' / arm / 'round-1'
                    folder.mkdir(parents=True)
                    text = '' if variant == 'direct' else ('accepted 0/3 draft tokens (restore checkpoint)\n'
                                                          'accepted 1/1 draft tokens\naccepted 3/3 draft tokens\n')
                    (folder / 'server.log').write_text(text)
                    passed = None if case['category'] != 'code' else not (failure and variant == 'prefix')
                    wall = {'direct': 10, 'prefix': 12, 'full': 8}[variant]
                    return {'model': model, 'arm': arm,
                        'response': {'wall_s': wall, 'ttft_s': 1,
                            'timings': {'prompt_ms': 2, 'predicted_ms': wall * 1000}},
                        'metrics': {'prompt_tokens': 100, 'completion_tokens': 50,
                                    'draft_n': 0 if variant == 'direct' else 6,
                                    'draft_n_accepted': 0 if variant == 'direct' else 4},
                        'quality': {'passed': passed, 'result': {}}}
                old_term = signal.getsignal(signal.SIGTERM)
                try:
                    with mock.patch.dict(os.environ, {'TMUX': 'test'}), \
                         mock.patch.object(ablation.base, 'verify_inputs', return_value=({'2B': Path('/prefix')}, {})) as verify, \
                         mock.patch.object(ablation.base, 'load_module', side_effect=load), \
                         mock.patch.object(ablation.base, 'run_one', side_effect=run_one):
                        if crash:
                            with self.assertRaisesRegex(RuntimeError, 'transport failure'):
                                ablation.main(argv)
                            self.assertFalse((root / 'out/summary.json').exists())
                        else:
                            self.assertEqual(ablation.main(argv), 2 if failure else 0)
                            self.assertEqual(len(set(seen)), 12)
                            self.assertEqual(seen[:3], [(cases[0]['case_id'], v) for v in ('direct', 'prefix', 'full')])
                            self.assertEqual(seen[3:6], [(cases[1]['case_id'], v) for v in ('prefix', 'full', 'direct')])
                            result = json.loads((root / 'out/summary.json').read_text())
                            self.assertEqual(result['automatic_failures'], int(failure))
                            self.assertEqual(result['manual_reviews_pending'], 9)
                            for case in result['cases'].values():
                                values = case['variants']
                                self.assertEqual(values['direct']['wall_s'], 10)
                                self.assertEqual(values['full']['wall_s'], 8)
                                self.assertAlmostEqual(values['prefix']['wall_change_vs_direct_pct'], 20)
                                self.assertAlmostEqual(values['full']['wall_change_vs_direct_pct'], -20)
                                self.assertEqual(values['full']['verification']['original_first_accepted'], 3)
                            result['records'][-1]['metrics']['prompt_tokens'] = 101
                            with self.assertRaisesRegex(ValueError, 'paired input token counts differ'):
                                ablation.summarize(result['records'])
                        self.assertEqual(verify.call_args.kwargs['model_names'], ('2B',))
                        model_check.compare_models.assert_called_once_with(Path('/full'), Path('/prefix'))
                finally:
                    signal.signal(signal.SIGTERM, old_term)


if __name__ == '__main__':
    unittest.main()
