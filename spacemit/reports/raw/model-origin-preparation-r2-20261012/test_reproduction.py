"""核验来源记录拒绝受损输入和错误模型。"""

import importlib.util
import json
import struct
import tempfile
import unittest
from pathlib import Path


SPEC = importlib.util.spec_from_file_location('recorder', Path(__file__).with_name('record-reproduction.py'))
RECORDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RECORDER)


class InputIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        tensors = {f'mtp.fake.{i}': {'dtype': 'BF16', 'shape': [1],
                                    'data_offsets': [i * 2, i * 2 + 2]} for i in range(15)}
        shard = 'model.safetensors'
        header = json.dumps(tensors).encode()
        (self.root / shard).write_bytes(struct.pack('<Q', len(header)) + header + b'\0' * 30)
        config = {'architectures': ['Qwen3_5ForConditionalGeneration'],
                  'text_config': {'num_hidden_layers': 24, 'mtp_num_hidden_layers': 1}}
        (self.root / 'config.json').write_text(json.dumps(config))
        (self.root / 'model.safetensors.index.json').write_text(json.dumps(
            {'weight_map': {key: shard for key in tensors}}))
        siblings = []
        for path in sorted(self.root.iterdir()):
            value = RECORDER.hashes(path)
            item = {'rfilename': path.name, 'blobId': value['git_blob_sha1']}
            if path.suffix == '.safetensors':
                item['lfs'] = {'sha256': value['sha256'], 'size': value['bytes']}
            siblings.append(item)
        self.metadata = {'id': 'Qwen/Qwen3.5-2B', 'sha': 'a' * 40, 'siblings': siblings}

    def test_complete_input_records_identity_only(self):
        result = RECORDER.snapshot(self.root, self.metadata, '2B')
        self.assertEqual(result['status'], 'input-identity-verified')
        self.assertEqual(result['tensor_count'], 15)
        self.assertTrue(result['limits'])

    def test_changed_weight_is_rejected(self):
        path = self.root / 'model.safetensors'
        path.write_bytes(path.read_bytes()[:-2] + b'xx')
        with self.assertRaisesRegex(ValueError, '大文件身份不匹配'):
            RECORDER.snapshot(self.root, self.metadata, '2B')

    def test_changed_tokenizer_configuration_is_rejected(self):
        (self.root / 'config.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, '配置文件身份不匹配'):
            RECORDER.snapshot(self.root, self.metadata, '2B')

    def test_wrong_model_is_rejected(self):
        with self.assertRaisesRegex(ValueError, '仓库标识不匹配'):
            RECORDER.snapshot(self.root, self.metadata, '4B')

    def test_missing_shard_is_rejected(self):
        (self.root / 'model.safetensors').unlink()
        with self.assertRaisesRegex(ValueError, '文件缺失'):
            RECORDER.snapshot(self.root, self.metadata, '2B')

    def test_extra_conversion_configuration_is_rejected(self):
        (self.root / 'hf_quant_config.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, '未记录文件'):
            RECORDER.snapshot(self.root, self.metadata, '2B')

    def test_changed_converter_is_rejected(self):
        path = self.root / 'convert.py'
        path.write_text('before')
        receipt = {'commit': 'a990751d55a4c54acf2bb77d44282c2093652359',
                   'files_sha256': {'convert.py': RECORDER.hashes(path)['sha256']}}
        path.write_text('after')
        with self.assertRaisesRegex(ValueError, '源码身份不匹配'):
            RECORDER.source(self.root, receipt)


if __name__ == '__main__':
    unittest.main()
