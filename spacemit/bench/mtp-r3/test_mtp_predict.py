"""检查收益数据集、分组切分与预测器评估。"""
import unittest

import mtp_predict


def row(family, saving_pct, direct_ms=1000.0, code_words=0):
    return {'family': family, 'case_id': family, 'round': 1, 'prompt_tokens': 100,
            'chars': 100, 'cjk_ratio': 0.0, 'lines': 3, 'code_fence': 0.0,
            'code_words': code_words, 'question_marks': 0, 'digits': 0, 'ascii_words': 10,
            'direct_ms': direct_ms, 'mtp_ms': direct_ms * (1 - saving_pct / 100),
            'saving_ms': direct_ms * saving_pct / 100, 'saving_pct': saving_pct}


class PredictTests(unittest.TestCase):
    def test_features_count_language_and_code(self):
        case = {'messages': [{'role': 'user', 'content': '实现 stable_unique，返回列表。\n```python\nreturn items\n```'}]}
        values = mtp_predict.features(case, 42)
        self.assertEqual(values['prompt_tokens'], 42)
        self.assertGreater(values['cjk_ratio'], 0)
        self.assertEqual(values['code_fence'], 1.0)
        self.assertGreater(values['lines'], 1)
        self.assertEqual(set(values), set(mtp_predict.FEATURES))

    def test_grouped_split_keeps_families_disjoint(self):
        rows = [row(name, 1.0) for name in ('a', 'b', 'c', 'd') for _ in range(2)]
        folds = mtp_predict.split_by_family(rows, 2)
        seen = [frozenset(item['family'] for item in fold) for fold in folds]
        self.assertFalse(set.intersection(*map(set, seen)))
        self.assertEqual(set().union(*map(set, seen)), {'a', 'b', 'c', 'd'})
        again = mtp_predict.split_by_family(rows, 2)
        self.assertEqual([[item['family'] for item in fold] for fold in again],
                         [[item['family'] for item in fold] for fold in folds])

    def test_logistic_separates_code_feature(self):
        train = [row('f1', 10.0, code_words=12), row('f2', 10.0, code_words=9),
                 row('f3', -5.0, code_words=0), row('f4', -3.0, code_words=1)]
        stats, weights = mtp_predict.fit(train, lambda item: 1.0 if item['saving_pct'] >= 5 else 0.0)
        self.assertGreater(mtp_predict.score(stats, weights, train[0]), 0.5)
        self.assertLess(mtp_predict.score(stats, weights, train[2]), 0.5)
        threshold = mtp_predict.best_threshold(train, stats, weights, 3.0)
        self.assertTrue(0.0 <= threshold <= 1.0)

    def test_evaluate_counts_gain_precision_and_loss(self):
        rows = [row('a', 10.0), row('b', -10.0)]
        result = mtp_predict.evaluate(rows, lambda item: True, 3.0)
        self.assertAlmostEqual(result['net_gain_pct'], 100 * (1 - (903.0 + 1103.0) / 2000.0))
        self.assertEqual(result['precision'], 0.5)
        self.assertEqual(result['recall'], 1.0)
        self.assertAlmostEqual(result['false_positive_mean_loss_ms'], 100.0)
        self.assertEqual(mtp_predict.evaluate(rows, lambda item: False, 3.0)['net_gain_pct'], 0.0)


if __name__ == '__main__':
    unittest.main()
