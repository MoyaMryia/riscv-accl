"""核对 BERT 输入身份、固定窗口和分类投影。"""
import hashlib
import json
import math
from pathlib import Path
import tempfile
import unittest

import bert_common
import bert_train
import bert_export
import bert_runtime
from unittest import mock


class BertTests(unittest.TestCase):
    def test_window_has_independent_expected_positions(self):
        self.assertEqual(bert_common.select_content([8, 2, 7], 8), [8, 2, 7])
        self.assertEqual(bert_common.select_content(list(range(20)), 8), [0, 1, 2, 3, 10, 11, 18, 19])
        self.assertEqual(bert_common.select_content(list(range(9)), 8), [0, 1, 2, 3, 4, 5, 7, 8])
        self.assertEqual(bert_common.add_special(list(range(20)),
            {'max_tokens': 10, 'cls_token_id': 101, 'sep_token_id': 102}),
            [101, 0, 1, 2, 3, 10, 11, 18, 19, 102])

    def test_projection_uses_independent_linear_and_softmax_reference(self):
        result = bert_common.classify_embedding([[1, 0], [0, 2], [-1, 0], [0, -1]],
                                               [0.5, 0, 0, -0.5], [2, 1])
        self.assertEqual(result['logits'], [2.5, 2, -2, -1.5])
        expected = [math.exp(v) / sum(math.exp(x) for x in [2.5, 2, -2, -1.5])
                    for v in [2.5, 2, -2, -1.5]]
        for actual, reference in zip(result['scores'].values(), expected):
            self.assertAlmostEqual(actual, reference, places=14)
        self.assertEqual(result['category'], 'code')

    def test_exporter_rejects_other_tokenizers(self):
        valid = {'normalizer': {'type': 'BertNormalizer', 'clean_text': True,
            'handle_chinese_chars': True, 'strip_accents': None, 'lowercase': False},
            'pre_tokenizer': {'type': 'BertPreTokenizer'},
            'model': {'type': 'WordPiece', 'unk_token': '[UNK]',
                'continuing_subword_prefix': '##', 'max_input_chars_per_word': 100}}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'tokenizer.json'
            path.write_text(json.dumps(valid))
            self.assertEqual(bert_export.check_tokenizer(Path(directory)), valid)
            valid['normalizer']['lowercase'] = True
            path.write_text(json.dumps(valid))
            with self.assertRaisesRegex(ValueError, 'normalizer'):
                bert_export.check_tokenizer(Path(directory))
            valid['normalizer']['lowercase'] = False
            valid['model']['type'] = 'BPE'
            path.write_text(json.dumps(valid))
            with self.assertRaisesRegex(ValueError, 'WordPiece'):
                bert_export.check_tokenizer(Path(directory))

    def test_native_client_returns_independent_projection_and_checks_responses(self):
        head = {'format': 1, 'labels': list(bert_common.LABELS),
            'max_tokens': bert_common.DEFAULTS['max_tokens'], 'hidden_size': 2, 'vocab_size': 256,
            'cls_token_id': 101, 'sep_token_id': 102, 'pad_token_id': 0,
            'weights': [[1, 0], [0, 2], [-1, 0], [0, -1]], 'bias': [0.5, 0, 0, -0.5],
            'min_score': bert_common.DEFAULT_MIN_SCORE}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'head.json'
            path.write_text(json.dumps(head))
            client = bert_runtime.Client(path, 'http://127.0.0.1:18120', 2)
            with mock.patch.object(client, 'post', side_effect=[{'tokens': [3, 4, 5]},
                    {'data': [{'embedding': [2, 1]}]}]) as fetch:
                result = client.predict('只返回实现')
                self.assertEqual(result['logits'], [2.5, 2, -2, -1.5])
                self.assertEqual(result['category'], 'code')
                self.assertEqual(fetch.call_args.args[1], {'input': [101, 3, 4, 5, 102], 'embd_normalize': -1})
            for response in ({'data': []}, {'data': [{'embedding': [2]}]},
                             {'data': [{'embedding': [float('nan'), 1]}]}):
                with mock.patch.object(client, 'post', side_effect=[{'tokens': [3]}, response]):
                    with self.assertRaises(ValueError):
                        client.predict('只返回实现')
            with mock.patch.object(client, 'post', return_value={'tokens': [True]}):
                with self.assertRaisesRegex(ValueError, 'token response'):
                    client.predict('只返回实现')
            head['format'] = True
            path.write_text(json.dumps(head))
            with self.assertRaisesRegex(ValueError, 'format'):
                bert_runtime.load_head(path)
        with self.assertRaisesRegex(ValueError, 'overflow'):
            bert_common.classify_embedding([[1e308, 0], [0, 0], [0, 0], [0, 0]], [0, 0, 0, 0], [2, 1])

    def inputs(self, root):
        base = root / 'base'
        base.mkdir()
        (base / 'weights').write_bytes(b'recorded source')
        rows = [{'id': 'a', 'text': 'source request', 'label': 'code', 'split': 'train', 'group': 'source'},
                {'id': 'b', 'text': 'new validation', 'label': 'qa', 'split': 'dev', 'group': 'validation'},
                {'id': 'c', 'text': 'new evaluation', 'label': 'text', 'split': 'test', 'group': 'evaluation'}]
        tasks = root / 'tasks.jsonl'
        tasks.write_text(''.join(json.dumps(row) + '\n' for row in rows))
        regression = root / 'regression.json'
        regression.write_text(json.dumps([{'id': 'r', 'label': 'code', 'text': 'historical request'}]))
        receipt = root / 'receipt.json'
        receipt.write_text(json.dumps({'repository': bert_train.REPOSITORY, 'revision': bert_train.REVISION,
            'base': {'weights': hashlib.sha256(b'recorded source').hexdigest()},
            'dataset_sha256': hashlib.sha256(tasks.read_bytes()).hexdigest()}))
        return base, tasks, receipt, regression, rows

    def test_entry_reads_valid_data_and_rejects_source_or_dataset_corruption(self):
        with tempfile.TemporaryDirectory() as folder:
            args = self.inputs(Path(folder))
            rows, regression = bert_train.read_inputs(*args[:4])
            self.assertEqual(rows, args[4])
            self.assertEqual(regression[0]['text'], 'historical request')
            (args[0] / 'weights').write_bytes(b'changed source')
            with self.assertRaisesRegex(ValueError, 'base 文件哈希'):
                bert_train.read_inputs(*args[:4])
            (args[0] / 'weights').write_bytes(b'recorded source')
            with args[1].open('a') as target:
                target.write('\n')
            with self.assertRaisesRegex(ValueError, 'tasks 文件哈希'):
                bert_train.read_inputs(*args[:4])

    def test_regression_is_separate_and_cannot_be_empty_or_enter_training(self):
        with tempfile.TemporaryDirectory() as folder:
            args = self.inputs(Path(folder))
            args[3].write_text('[]')
            with self.assertRaisesRegex(ValueError, '非空数组'):
                bert_train.read_inputs(*args[:4])
            args[3].write_text(json.dumps([{'id': 'r', 'label': 'code', 'text': ' SOURCE   REQUEST '}]))
            with self.assertRaisesRegex(ValueError, '进入训练集'):
                bert_train.read_inputs(*args[:4])


if __name__ == '__main__':
    unittest.main()
