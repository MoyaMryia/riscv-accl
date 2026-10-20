"""用固定字节向量核对复现门禁和输出保护。"""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import bert_reproduce

SHA256_ABC = 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'


class ReproduceTests(unittest.TestCase):
    def prepare(self, root):
        result = root / 'result'
        (result / 'encoder').mkdir(parents=True)
        paths = {'encoder_safetensors': result / 'encoder/model.safetensors',
                 'head': result / 'head.json', 'gguf': result / 'encoder-f32.gguf'}
        for path in paths.values():
            path.write_bytes(b'abc')
        artifacts = root / 'artifacts.json'
        artifacts.write_text(json.dumps({name: {'bytes': 3, 'sha256': SHA256_ABC}
                                        for name in [*paths, 'converter_snapshot']}))
        training = {'configuration': {'seed': 42}, 'versions': {'python': '3.13.14'},
            'parameters': {'total': 1028}, 'split_counts': {'train': 2, 'dev': 2, 'test': 2},
            'best_epoch': 2, 'metrics': {}}
        for split, correct in [('best_dev', 2), ('test', 1), ('regression', 2)]:
            training['metrics'][split] = {'confusion': {'code': {'code': correct, 'qa': 2 - correct}},
                                          'accuracy': correct / 2}
        original = root / 'original-training.json'
        original.write_text(json.dumps(training))
        (result / 'training.json').write_text(json.dumps(training))
        return result, artifacts, original

    def test_verified_result_has_expected_numbers_and_each_artifact_corruption_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            args = self.prepare(Path(directory))
            report = bert_reproduce.verify_result(*args)
            self.assertEqual(report['best_epoch'], 2)
            self.assertEqual(report['test_accuracy'], 0.5)
            self.assertEqual(report['regression_accuracy'], 1.0)
            for relative in ['encoder/model.safetensors', 'head.json', 'encoder-f32.gguf']:
                path = args[0] / relative
                path.write_bytes(b'abd')
                with self.subTest(relative=relative), self.assertRaisesRegex(ValueError, 'artifact differs'):
                    bert_reproduce.verify_result(*args)
                path.write_bytes(b'abc')

    def test_metadata_and_confusion_corruption_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            args = self.prepare(Path(directory))
            original = json.loads(args[2].read_text())
            mutations = [('configuration', {'seed': 43}), ('versions', {'python': '3.13.13'}),
                         ('parameters', {'total': 1029}), ('split_counts', {'train': 3}), ('best_epoch', 3)]
            for key, value in mutations:
                damaged = copy.deepcopy(original)
                damaged[key] = value
                (args[0] / 'training.json').write_text(json.dumps(damaged))
                with self.subTest(key=key), self.assertRaisesRegex(ValueError, key):
                    bert_reproduce.verify_result(*args)
            damaged = copy.deepcopy(original)
            del damaged['parameters']
            (args[0] / 'training.json').write_text(json.dumps(damaged))
            with self.assertRaises(KeyError):
                bert_reproduce.verify_result(*args)
            damaged = copy.deepcopy(original)
            damaged['metrics']['test']['confusion']['code']['code'] = 2
            (args[0] / 'training.json').write_text(json.dumps(damaged))
            with self.assertRaisesRegex(ValueError, 'results differ'):
                bert_reproduce.verify_result(*args)

    def test_converter_checksum_and_existing_destination_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.prepare(root)
            archive = root / 'converter.tgz'
            archive.write_bytes(b'abc')
            bert_reproduce.verify_converter(archive, args[1])
            archive.write_bytes(b'abd')
            with self.assertRaisesRegex(ValueError, 'snapshot hash'):
                bert_reproduce.verify_converter(archive, args[1])
            output = root / 'existing'
            output.mkdir()
            sentinel = output / 'run.log'
            sentinel.write_text('preserve the record')
            script = Path(__file__).with_name('reproduce-bert.sh')
            run = subprocess.run(['bash', str(script), str(output)], capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertEqual(sentinel.read_text(), 'preserve the record')


if __name__ == '__main__':
    unittest.main()
