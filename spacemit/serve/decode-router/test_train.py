"""测试任务检查和拆分评估。"""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

MODULE_PATH = Path(__file__).with_name('train.py')
spec = importlib.util.spec_from_file_location('decode_train', MODULE_PATH)
train_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(train_module)


class TrainTests(unittest.TestCase):
    def write_tasks(self, directory, rows):
        path = Path(directory) / 'tasks.jsonl'
        path.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')
        return path

    @staticmethod
    def valid_rows():
        return [
            {'id': 'a', 'text': 'alpha', 'label': 'code', 'split': 'train'},
            {'id': 'b', 'text': 'beta', 'label': 'qa', 'split': 'train'},
            {'id': 'c', 'text': 'gamma', 'label': 'text', 'split': 'dev'},
            {'id': 'd', 'text': 'delta', 'label': 'document', 'split': 'test'},
        ]

    def test_evaluate_uses_predictions_and_reports_counts(self):
        rows = [
            {'text': 'one', 'label': 'code'},
            {'text': 'two', 'label': 'qa'},
            {'text': 'three', 'label': 'text'},
            {'text': 'four', 'label': 'document'},
        ]
        predictions = {
            'one': ('code', 0.9),
            'two': ('qa', 0.8),
            'three': ('document', 0.7),
            'four': ('document', 0.4),
        }

        def predict(_model, text):
            category, score = predictions[text]
            return {'category': category, 'score': score}

        with patch.object(train_module.classifier, 'predict', side_effect=predict):
            result = train_module.evaluate({'min_score': 0.65}, rows)
        self.assertEqual(result['accuracy'], 0.75)
        self.assertEqual(result['per_label']['code']['precision'], 1.0)
        self.assertEqual(result['per_label']['text']['recall'], 0.0)
        self.assertEqual(result['per_label']['document']['precision'], 0.5)
        self.assertEqual(result['per_label']['document']['recall'], 1.0)
        self.assertAlmostEqual(result['per_label']['document']['f1'], 2 / 3)
        self.assertEqual(result['confusion']['text']['document'], 1)
        self.assertEqual(result['confusion']['document']['document'], 1)
        self.assertEqual(result['confusion']['document']['code'], 0)
        self.assertEqual(result['high_score_coverage_count'], 3)
        self.assertEqual(result['high_score_coverage'], 0.75)
        self.assertAlmostEqual(result['high_score_accuracy'], 2 / 3)

    def test_group_schema_accepts_within_split_and_rejects_leakage(self):
        with tempfile.TemporaryDirectory() as directory:
            rows = self.valid_rows()
            for row in rows:
                row['group'] = 'g-' + row['split']
            self.assertEqual(train_module.read_tasks(self.write_tasks(directory, rows)), rows)
            rows[-1]['group'] = ' G-TRAIN '
            with self.assertRaisesRegex(ValueError, '跨拆分'):
                train_module.read_tasks(self.write_tasks(directory, rows))
            rows[-1]['group'] = 'g-test'
            rows[0]['group'] = ' '
            with self.assertRaisesRegex(ValueError, 'group 无效'):
                train_module.read_tasks(self.write_tasks(directory, rows))
            rows[0].pop('group')
            with self.assertRaisesRegex(ValueError, '字段格式'):
                train_module.read_tasks(self.write_tasks(directory, rows))

    def test_main_computes_training_and_held_out_results(self):
        rows = [
            {'id': 'a', 'text': 'x', 'label': 'code', 'split': 'train', 'group': 'first'},
            {'id': 'b', 'text': 'y', 'label': 'code', 'split': 'dev', 'group': 'second'},
            {'id': 'c', 'text': 'z', 'label': 'qa', 'split': 'test', 'group': 'third'},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_tasks(directory, rows)
            output = Path(directory) / 'trained'
            result = train_module.main(['--tasks', str(path), '--output', str(output)])
            self.assertEqual(result['metrics']['dev']['accuracy'], 1.0)
            self.assertEqual(result['metrics']['test']['accuracy'], 0.0)
            self.assertEqual(result['metrics']['test']['per_label']['code']['predicted'], 1)
            self.assertEqual(result['metrics']['test']['per_label']['code']['precision'], 0.0)
            self.assertEqual(result['metrics']['test']['per_label']['qa']['recall'], 0.0)
            self.assertTrue((output / 'model.json.gz').is_file())

    def test_read_tasks_accepts_nonempty_splits(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_tasks(directory, self.valid_rows())
            self.assertEqual(train_module.read_tasks(path), self.valid_rows())

    def test_read_tasks_rejects_duplicate_text_and_id(self):
        for field, value in (('text', ' ALPHA  '), ('id', 'a')):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                rows = self.valid_rows()
                rows[1][field] = value
                with self.assertRaisesRegex(ValueError, '重复'):
                    train_module.read_tasks(self.write_tasks(directory, rows))

    def test_read_tasks_rejects_unknown_label_and_empty_split(self):
        with tempfile.TemporaryDirectory() as directory:
            rows = self.valid_rows()
            rows[0]['label'] = 'unknown'
            with self.assertRaisesRegex(ValueError, 'label'):
                train_module.read_tasks(self.write_tasks(directory, rows))
        with tempfile.TemporaryDirectory() as directory:
            rows = self.valid_rows()[:-1]
            with self.assertRaisesRegex(ValueError, '不能为空'):
                train_module.read_tasks(self.write_tasks(directory, rows))


if __name__ == '__main__':
    unittest.main()
