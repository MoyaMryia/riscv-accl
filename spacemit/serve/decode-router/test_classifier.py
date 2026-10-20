"""分类器接口与数值测试。"""
import gzip
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest

MODULE_PATH = Path(__file__).with_name('classifier.py')
spec = importlib.util.spec_from_file_location('decode_classifier', MODULE_PATH)
classifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(classifier)


class ClassifierTests(unittest.TestCase):
    def test_hand_calculated_softmax(self):
        model = {
            'format': 1, 'labels': list(classifier.LABELS), 'dimensions': 8,
            'window': 256, 'min_score': 0.0, 'weights': [{}, {}, {}, {}],
            'bias': [0.0, math.log(2.0), 0.0, 0.0],
        }
        result = classifier.predict(model, '?')
        expected = [1 / 5, 2 / 5, 1 / 5, 1 / 5]
        self.assertEqual(result['category'], 'qa')
        self.assertAlmostEqual(result['score'], 0.4)
        for label, probability in zip(classifier.LABELS, expected):
            self.assertAlmostEqual(result['scores'][label], probability)

    def test_single_feature_dot_product_and_low_score_keeps_label(self):
        model = {'dimensions': 8, 'weights': [{}, {'5': math.log(2)}, {}, {}],
                 'bias': [0.0] * 4, 'min_score': classifier.DEFAULT_MIN_SCORE}
        for text in ('ab', 'AB'):
            result = classifier.predict(model, text)
            self.assertEqual(result['category'], 'qa')
            self.assertAlmostEqual(result['score'], .4)
            self.assertAlmostEqual(result['scores']['code'], .2)

    def test_training_reduces_loss_and_hits_classes(self):
        rows = [
            {'text': 'def add(a, b): return a + b', 'label': 'code'},
            {'text': 'class Router: return route(text)', 'label': 'code'},
            {'text': 'What is a router? Why does it work?', 'label': 'qa'},
            {'text': 'How can I train this model?', 'label': 'qa'},
            {'text': 'A short plain sentence about the sky.', 'label': 'text'},
            {'text': 'This is a simple note for today.', 'label': 'text'},
            {'text': '# Manual\n1. Set the value. 2. Run the command.', 'label': 'document'},
            {'text': 'Chapter 1: System guide and reference.', 'label': 'document'},
        ]
        model = classifier.train(rows, epochs=80, dimensions=128, seed=13)
        self.assertLess(model['loss_history'][-1], model['loss_history'][0])
        for row in rows:
            result = classifier.predict(model, row['text'])
            self.assertEqual(result['category'], row['label'])

    def test_deterministic_training_and_gzip_bytes(self):
        rows = [{'text': 'alpha beta', 'label': 'text'},
                {'text': 'def alpha(): pass', 'label': 'code'}]
        first = classifier.train(rows, epochs=3, dimensions=64)
        second = classifier.train(rows, epochs=3, dimensions=64)
        self.assertEqual(first, second)
        with tempfile.TemporaryDirectory() as directory:
            one, two = Path(directory) / 'one.gz', Path(directory) / 'two.gz'
            classifier.save_model(first, one)
            classifier.save_model(second, two)
            self.assertEqual(one.read_bytes(), two.read_bytes())
            loaded = classifier.load_model(one)
            for text in ('alpha beta', 'def alpha(): pass'):
                self.assertEqual(classifier.predict(first, text), classifier.predict(loaded, text))

    def test_load_rejects_nan_and_bad_shape(self):
        base = {
            'format': 1, 'labels': list(classifier.LABELS), 'dimensions': 8,
            'window': 256, 'min_score': 0.65, 'weights': [{}, {}, {}, {}],
            'bias': [0.0, 0.0, 0.0, 0.0],
        }
        for change in (
                lambda value: value.update(bias=[float('nan'), 0.0, 0.0, 0.0]),
                lambda value: value.update(weights=[{}, {}, {}]),
                lambda value: value.update(min_score=True),
                lambda value: value.update(weights=[{'00': 1.0}, {}, {}, {}]),
                lambda value: value.update(weights=[{'0': 1e308, '1': 1e308}, {}, {}, {}]),
        ):
            model = dict(base)
            change(model)
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'bad.gz'
                with gzip.open(path, 'wt', encoding='utf-8') as stream:
                    json.dump(model, stream, allow_nan=True)
                with self.assertRaises(ValueError):
                    classifier.load_model(path)


if __name__ == '__main__':
    unittest.main()
