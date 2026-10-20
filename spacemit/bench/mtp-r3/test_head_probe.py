import json
import os
from pathlib import Path
import signal
import tempfile
import unittest
from unittest import mock

import head_probe


class HeadProbeTests(unittest.TestCase):
    def test_prefix_coverage_counts_boundary_and_high_ids(self):
        result = head_probe.prefix_coverage([65, 320, 65535, 65536, 115412], 65536)
        self.assertEqual(result['retokenized_tokens'], 5)
        self.assertEqual(result['prefix_tokens'], 3)
        self.assertAlmostEqual(result['prefix_fraction'], .6)
        for invalid in ([], [True], [-1], ['65'], {'tokens': [65]}):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                head_probe.prefix_coverage(invalid, 65536)

    def test_main_includes_all_historical_sources_and_not_probe_answer(self):
        here = Path(__file__).parent
        records = [{'model': '2B', 'arm': 'direct', 'case_id': f'case_{i}', 'category': 'qa',
                    'response': {'answer': f'source {i}'}, 'metrics': {'completion_tokens': 4}}
                   for i in range(12)]
        records.append({'model': '2B', 'arm': 'direct', 'case_id': 'prior_code_unicode_runs',
                        'category': 'prior_code', 'response': {'answer': 'prior code'},
                        'metrics': {'completion_tokens': 508}})
        excluded = dict(records[0], arm='mtp')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'records.json'
            source.write_text(json.dumps({'records': records + [excluded]}))
            request = root / 'cases.json'
            request.write_text(json.dumps([{'case_id': 'probe_case', 'messages': []}]))
            argv = ['--prefix-rows', '65536', '--case-id', 'probe_case']
            for flag, value in {'output': root / 'out', 'server': '/server', 'models': '/models',
                'spert': '/spert', 'tcm': '/tcm', 'manifest': '/manifest', 'request': request,
                'build-receipt': '/receipt', 'tool-receipt': '/tools.json', 'records': source,
                'chat': here.parents[1] / 'serve/cached-document-chat.py',
                'quality': '/quality', 'effective': here.parent / 'final-default/effective.py'}.items():
                argv += ['--' + flag, str(value)]
            class Response:
                def __enter__(self): return self
                def __exit__(self, *args): return False
                def read(self): return b'{"tokens":[65,65535,65536]}'
            def run_one(*args, assess, trace):
                self.assertTrue(trace)
                assess('current probe answer')
                folder = root / 'out/2B/mtp_lowacc/round-1'
                folder.mkdir(parents=True)
                (folder / 'server.log').write_text('accepted 0/3 draft tokens (restore checkpoint)\naccepted 1/1 draft tokens\n')
                return {'metrics': {'draft_n': 3, 'draft_n_accepted': 1}, 'fallback_events': []}
            old_term = signal.getsignal(signal.SIGTERM)
            try:
                with mock.patch.dict(os.environ, {'TMUX': 'test'}), \
                     mock.patch.object(head_probe.base, 'verify_inputs', return_value=({'2B': Path('/model')}, {})), \
                     mock.patch.object(head_probe.base, 'run_one', side_effect=run_one), \
                     mock.patch('urllib.request.urlopen', return_value=Response()) as http:
                    self.assertEqual(head_probe.main(argv), 0)
                coverage = json.loads((root / 'out/coverage.json').read_text())['records']
                self.assertEqual(len(coverage), 13)
                self.assertEqual(coverage[-1]['case_id'], 'prior_code_unicode_runs')
                self.assertEqual(coverage[-1]['generated_tokens'], 508)
                self.assertTrue(all(r['prefix_tokens'] == 2 for r in coverage))
                self.assertTrue(all(abs(r['prefix_fraction'] - 2 / 3) < 1e-12 for r in coverage))
                self.assertEqual(http.call_count, 13)
                sent = [json.loads(c.args[0].data)['content'] for c in http.call_args_list]
                self.assertEqual(sent, [r['response']['answer'] for r in records])
                self.assertNotIn('current probe answer', sent)
            finally:
                signal.signal(signal.SIGTERM, old_term)

    def test_trace_keeps_original_rejection_and_replay_events(self):
        events = head_probe.trace_events('''startup
slot: accepted  0/ 3 draft tokens (restore checkpoint)
slot: accepted  1/ 1 draft tokens
slot: accepted  2/ 3 draft tokens (restore checkpoint)
slot: accepted  3/ 3 draft tokens
slot: accepted  3/ 3 draft tokens
''')
        self.assertEqual([(e['accepted'], e['drafted'], e['restore_checkpoint']) for e in events],
                         [(0, 3, True), (1, 1, False), (2, 3, True), (3, 3, False), (3, 3, False)])
        self.assertEqual(head_probe.trace_events('startup without verification'), [])


if __name__ == '__main__':
    unittest.main()
