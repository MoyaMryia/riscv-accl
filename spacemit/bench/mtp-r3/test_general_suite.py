from copy import deepcopy
import json
import os
from pathlib import Path
import signal
import tempfile
import unittest
from unittest import mock

import general_suite as suite

HERE = Path(__file__).parent
QUALITY = suite.base.load_module('suite_quality_test', HERE.parents[1] / 'release-candidate/tests/quality.py')
CASES = suite.base.load_module('suite_cases_test', HERE / 'general_cases.py')


class GeneralSuiteTests(unittest.TestCase):
    def test_input_schema_rejects_real_errors(self):
        cases = CASES.build_cases(QUALITY)
        changes = [lambda c: c.pop(),
                   lambda c: c[1].update(case_id=c[0]['case_id']),
                   lambda c: c[0].update(case_id='../escape'),
                   lambda c: c[0].update(category='other'),
                   lambda c: c[0].update(messages=[{'role': 'user', 'content': ''}]),
                   lambda c: c[0]['messages'][0].update(content=''),
                   lambda c: c[0].update(required_facts=[]),
                   lambda c: c[0].update(code_task='unknown'),
                   lambda c: c[0]['metadata'].update(evidence='')]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'cases.json'
            path.write_text(json.dumps(cases))
            self.assertEqual(len(suite.read_cases(path, QUALITY)), 12)
            for change in changes:
                altered = deepcopy(cases)
                change(altered)
                path.write_text(json.dumps(altered))
                with self.assertRaises(ValueError):
                    suite.read_cases(path, QUALITY)

    def test_main_all_36_requests_numeric_results_and_pending_reviews(self):
        for failure, crash in [(False, False), (True, False), (False, True)]:
            with self.subTest(failure=failure, crash=crash), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                cases = CASES.build_cases(QUALITY)
                path = root / 'cases.json'
                path.write_text(json.dumps(cases))
                argv = []
                for flag, value in {'output': root / 'out', 'server': '/server', 'models': '/models',
                    'spert': '/spert', 'tcm': '/tcm', 'manifest': '/manifest', 'request': path,
                    'build-receipt': '/receipt', 'tool-receipt': '/tools.json',
                    'chat': HERE.parents[1] / 'serve/cached-document-chat.py',
                    'quality': HERE.parents[1] / 'release-candidate/tests/quality.py',
                    'effective': HERE.parent / 'final-default/effective.py'}.items():
                    argv += ['--' + flag, str(value)]
                seen = []
                def run_one(args, libs, chat, effective, quality, model, arm, round_no, case, *rest, assess):
                    if crash:
                        raise RuntimeError('transport failure')
                    self.assertEqual(model, '2B')
                    seen.append((case['case_id'], arm))
                    index = cases.index(case)
                    baseline = (10, 20, 40)[index % 3]
                    wall = {'direct': baseline, 'mtp': baseline * .8, 'mtp_lowacc': baseline * 1.05}[arm]
                    pending = case['category'] != 'code'
                    passed = None if pending else not (failure and index == 0 and arm == 'mtp')
                    return {'model': model, 'arm': arm, 'round': round_no,
                        'response': {'wall_s': wall, 'ttft_s': 1,
                                     'timings': {'prompt_ms': 2, 'predicted_ms': wall * 1000}},
                        'metrics': {'prompt_tokens': 100 + index, 'completion_tokens': 50 + index,
                                    'draft_n': 0 if arm == 'direct' else 10,
                                    'draft_n_accepted': 0 if arm == 'direct' else 3},
                        'quality': {'passed': passed, 'result': {}}, 'fallback_events': []}
                old_term = signal.getsignal(signal.SIGTERM)
                try:
                    with mock.patch.dict(os.environ, {'TMUX': 'test'}), \
                         mock.patch.object(suite.base, 'verify_inputs', return_value=({'2B': Path('/2B')}, {})) as verify, \
                         mock.patch.object(suite.base, 'run_one', side_effect=run_one):
                        if crash:
                            with self.assertRaisesRegex(RuntimeError, 'transport failure'):
                                suite.main(argv)
                            self.assertFalse((root / 'out/summary.json').exists())
                        else:
                            self.assertEqual(suite.main(argv), 2 if failure else 0)
                            self.assertEqual(len(set(seen)), 36)
                            self.assertEqual(seen[:3], [(cases[0]['case_id'], a) for a in ('direct', 'mtp', 'mtp_lowacc')])
                            self.assertEqual(seen[3:6], [(cases[1]['case_id'], a) for a in ('mtp', 'mtp_lowacc', 'direct')])
                            actual = json.loads((root / 'out/summary.json').read_text())
                            self.assertEqual(actual['automatic_failures'], int(failure))
                            self.assertEqual(actual['manual_reviews_pending'], 27)
                            self.assertNotIn('quality_gate', actual)
                            for category in ('code', 'chinese', 'qa', 'long_document'):
                                values = actual['categories'][category]
                                self.assertAlmostEqual(values['direct']['wall_mean_s'], 70 / 3)
                                self.assertAlmostEqual(values['mtp']['wall_mean_s'], 56 / 3)
                                self.assertAlmostEqual(values['mtp']['wall_change_vs_direct_pct'], -20)
                                self.assertAlmostEqual(values['mtp_lowacc']['wall_change_vs_direct_pct'], 5)
                                self.assertAlmostEqual(values['mtp']['draft_acceptance'], .3)
                            actual['records'][-1]['metrics']['prompt_tokens'] += 1
                            with self.assertRaisesRegex(ValueError, 'paired input token counts differ'):
                                suite.summarize(actual['records'])
                        self.assertEqual(verify.call_args.kwargs['model_names'], ('2B',))
                finally:
                    signal.signal(signal.SIGTERM, old_term)


if __name__ == '__main__':
    unittest.main()
