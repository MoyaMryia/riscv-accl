"""核对原生编码器参考门禁和延时统计。"""
import copy
import unittest

import bert_bench


class BertBenchTests(unittest.TestCase):
    def test_reference_numbers_and_each_mismatch_fail(self):
        reference = {'selected_token_ids': [101, 8, 102], 'logits': [1.0, 2.0, 3.0, 4.0],
                     'category': 'document'}
        actual = copy.deepcopy(reference)
        actual['logits'][0] = 1.01
        self.assertAlmostEqual(bert_bench.verify_prediction(actual, reference), 0.01)
        for damage in ('tokens', 'logits', 'category'):
            actual = copy.deepcopy(reference)
            if damage == 'tokens':
                actual['selected_token_ids'][1] = 9
            elif damage == 'logits':
                actual['logits'][0] = 1.03
            else:
                actual['category'] = 'code'
            with self.subTest(damage=damage), self.assertRaises(ValueError):
                bert_bench.verify_prediction(actual, reference)

    def test_nearest_rank_p95_and_median(self):
        result = bert_bench.summary_times([1, 4, 9, 2])
        self.assertEqual(result, {'count': 4, 'median_ms': 3, 'p95_ms': 9, 'min_ms': 1, 'max_ms': 9})


if __name__ == '__main__':
    unittest.main()
