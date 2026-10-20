"""核对回放数值和分类计时统计。"""
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import evaluate_routing as evaluation


class EvaluationTests(unittest.TestCase):
    def test_classification_is_not_fastest_path_oracle(self):
        labels = ('code', 'qa', 'text', 'document')
        rows = [{'case_id': label, 'text': label, 'times': {'direct': 10, 'prefix': 12, 'full': 8}}
                for label in labels]
        with mock.patch.object(evaluation.classifier, 'predict', side_effect=lambda model, text: {
                'category': text, 'score': .9}), \
             mock.patch.object(evaluation.time, 'perf_counter_ns', side_effect=iter(range(0, 1_000_000_000, 10_000_000))):
            result = evaluation.replay({'min_score': .65}, rows)
        self.assertEqual(result['direct_sum_s'], 40)
        two, three = result['policies']['two'], result['policies']['three']
        self.assertEqual(two['oracle_sum_s'], 40)
        self.assertEqual(three['oracle_sum_s'], 32)
        self.assertEqual(two['selected_sum_s'], 42)
        self.assertEqual(three['selected_sum_s'], 40)
        self.assertAlmostEqual(two['estimated_sum_s'], 42.08)
        self.assertAlmostEqual(three['estimated_sum_s'], 40.08)
        self.assertLess(two['estimated_reduction_pct'], 0)

    def test_benchmark_counts_and_quantile(self):
        with mock.patch.object(evaluation.classifier, 'predict', return_value={'category': 'code', 'score': .9}), \
             mock.patch.object(evaluation.time, 'perf_counter_ns', side_effect=iter(range(0, 100_000_000, 1_000_000))):
            result = evaluation.benchmark({'min_score': .65}, [{'id': 'one', 'text': '?'}, {'id': 'two', 'text': '!'}], 2)
        self.assertEqual(result['calls'], 4)
        self.assertEqual(result['unique_requests'], 2)
        self.assertEqual(result['decision_ms'], {'min': 2, 'median': 2, 'p95': 2, 'max': 2})
        self.assertEqual([sample['route'] for sample in result['samples']], ['prefix'] * 4)

    def test_replay_input_rejects_missing_and_invalid_times(self):
        cases = [{'case_id': 'one', 'messages': [{'role': 'user', 'content': '问题'}]}]
        base = {'cases': {'one': {'variants': {name: {'wall_s': 10} for name in ('direct', 'prefix', 'full')}}}}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            req, times = root / 'cases.json', root / 'times.json'
            req.write_text(json.dumps(cases))
            times.write_text(json.dumps(base))
            self.assertEqual(evaluation.read_replay(times, req)[0]['times']['full'], 10)
            for value in (0, -1, True, float('nan')):
                changed = json.loads(json.dumps(base))
                changed['cases']['one']['variants']['full']['wall_s'] = value
                times.write_text(json.dumps(changed))
                with self.assertRaises(ValueError):
                    evaluation.read_replay(times, req)
            changed = json.loads(json.dumps(base))
            del changed['cases']['one']['variants']['full']
            times.write_text(json.dumps(changed))
            with self.assertRaises(ValueError):
                evaluation.read_replay(times, req)


if __name__ == '__main__':
    unittest.main()
