#!/usr/bin/env python3
"""核验结构比较工具拒绝差异，并接受完全相同的记录。"""

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path


SPEC = importlib.util.spec_from_file_location('verify_artifact', Path(__file__).with_name('verify-artifact.py'))
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


def structure(**overrides):
    base = {
        'path': 'candidate.gguf',
        'sha256': 'a' * 64,
        'gguf_version': 3,
        'tensor_count': 2,
        'tensors': [
            {'name': 'blk.0.attn_q.weight', 'shape': [64, 64], 'dtype': 'Q4_0'},
            {'name': 'token_embd.weight', 'shape': [128, 64], 'dtype': 'Q4_0'},
        ],
        'tokenizer_model': 'gpt2',
        'tokenizer': {'count': 151936, 'tokens_sha256': 'b' * 64},
        'chat_template_sha256': 'c' * 64,
    }
    base.update(overrides)
    return base


class CompareTest(unittest.TestCase):
    def test_identical_records_pass(self):
        result = VERIFY.compare_structures(structure(), structure())
        self.assertTrue(result['passed'])
        self.assertEqual(result['failures'], [])

    def test_different_file_digest_fails(self):
        result = VERIFY.compare_structures(structure(), structure(sha256='d' * 64))
        self.assertIn('file_sha256', result['failures'])

    def test_missing_tensor_fails_with_names(self):
        candidate = structure(tensor_count=1, tensors=[
            {'name': 'token_embd.weight', 'shape': [128, 64], 'dtype': 'Q4_0'}])
        result = VERIFY.compare_structures(structure(), candidate)
        names = [c for c in result['checks'] if c['check'] == 'tensor_names'][0]
        self.assertFalse(names['passed'])
        self.assertEqual(names['detail']['missing'], ['blk.0.attn_q.weight'])

    def test_shape_difference_fails(self):
        candidate = structure(tensors=[
            {'name': 'blk.0.attn_q.weight', 'shape': [64, 32], 'dtype': 'Q4_0'},
            {'name': 'token_embd.weight', 'shape': [128, 64], 'dtype': 'Q4_0'},
        ])
        result = VERIFY.compare_structures(structure(), candidate)
        self.assertIn('shape:blk.0.attn_q.weight', result['failures'])

    def test_dtype_difference_fails(self):
        candidate = structure(tensors=[
            {'name': 'blk.0.attn_q.weight', 'shape': [64, 64], 'dtype': 'Q8_0'},
            {'name': 'token_embd.weight', 'shape': [128, 64], 'dtype': 'Q4_0'},
        ])
        result = VERIFY.compare_structures(structure(), candidate)
        self.assertIn('dtype:blk.0.attn_q.weight', result['failures'])

    def test_tokenizer_and_template_differences_fail(self):
        result = VERIFY.compare_structures(
            structure(), structure(tokenizer_model='llama',
                                   chat_template_sha256='e' * 64,
                                   tokenizer={'count': 151936, 'tokens_sha256': 'f' * 64}))
        self.assertIn('tokenizer_model', result['failures'])
        self.assertIn('tokenizer_tokens', result['failures'])
        self.assertIn('chat_template', result['failures'])

    def test_ignored_tensor_is_not_compared(self):
        candidate = structure(tensor_count=2, tensors=[
            {'name': 'token_embd.weight', 'shape': [128, 64], 'dtype': 'Q4_0'}])
        result = VERIFY.compare_structures(structure(), candidate,
                                           ignore=['blk.0.attn_q.weight'])
        self.assertTrue(result['passed'])


class FakeField:
    def __init__(self, value=None, data=None):
        self.value = value
        self.data = data or []

    def contents(self):
        return self.value


class FakeTensor:
    def __init__(self, name, shape, tensor_type):
        self.name, self.shape, self.tensor_type = name, shape, tensor_type


class FakeReader:
    gguf_version = 3

    def __init__(self):
        self.fields = {
            'tokenizer.ggml.model': FakeField('gpt2'),
            'tokenizer.ggml.tokens': FakeField(data=[b'a', b'b']),
            'tokenizer.chat_template': FakeField('template'),
        }
        self.tensors = [FakeTensor('w', [2, 2], 'Q4_0')]


class FakeModule:
    GGUFReader = staticmethod(lambda path: FakeReader())


class ReadStructureTest(unittest.TestCase):
    def test_reads_string_fields_through_contents(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'fake.gguf'
            path.write_bytes(b'GGUF')
            result = VERIFY.read_structure(path, FakeModule)
        self.assertEqual(result['tokenizer_model'], 'gpt2')
        self.assertEqual(result['tokenizer'], {
            'count': 2,
            'tokens_sha256': hashlib.sha256(b'a\0b\0').hexdigest()})
        self.assertEqual(result['chat_template_sha256'],
                         hashlib.sha256(b'template').hexdigest())
        self.assertEqual(result['tensor_count'], 1)
        self.assertEqual(result['gguf_version'], 3)


if __name__ == '__main__':
    unittest.main()
