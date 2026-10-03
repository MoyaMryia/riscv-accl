#!/usr/bin/env python3
"""Check cold-prefill, completeness, metadata and resume gates without inference."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

HERE = Path(__file__).resolve().parent

def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

fast, lifecycle = load('k1-fast-test'), load('bench-lifecycle')


def records():
    rows = []
    for label in ('control', 'candidate'):
        rows.append({'kind': 'config', 'label': label, 'n_predict': 1,
                     'cache_prompt': False, 'verify_cold': True})
        ids = [42]
        rows.append({'kind': 'measurement', 'label': label, 'context_tokens': 512,
                     'prompt_token_sha256': ['a' * 64], 'results': [{
                         'error': None, 'stop_type': 'limit', 'tokens_predicted': 1,
                         'streamed_tokens': 1, 'token_ids': ids,
                         'tokens_sha256': hashlib.sha256(json.dumps(ids, separators=(',', ':')).encode()).hexdigest(),
                         'sha256': 'b' * 64, 'ttft_ms': 101,
                         'timings': {'cache_n': 0, 'prompt_n': 512, 'prompt_ms': 100}}]})
    return rows


class Gates(unittest.TestCase):
    def test_cold_requires_actual_counts(self):
        lifecycle.verify_cold({'timings': {'cache_n': 0, 'prompt_n': 512}}, 512)
        for telemetry in ({}, {'cache_n': 1, 'prompt_n': 512}, {'cache_n': 0, 'prompt_n': 511}):
            with self.assertRaises(RuntimeError):
                lifecycle.verify_cold({'timings': telemetry}, 512)

    def test_complete_inputs_and_outputs(self):
        self.assertEqual(len(fast.check_model_records(records(), ['control', 'candidate'], 512)), 2)
        bad = records()[:-1]
        with self.assertRaises(ValueError): fast.check_model_records(bad, ['control', 'candidate'], 512)
        mutations = (
            lambda r: r[-1].update(label='control'),
            lambda r: r[-1]['results'][0]['timings'].update(cache_n=8),
            lambda r: r[-1]['results'][0].update(tokens_predicted=0),
            lambda r: r[-1]['results'][0].update(tokens_sha256='x'),
            lambda r: r[-1]['results'][0].update(token_ids=[43]),
            lambda r: r[-1].update(prompt_token_sha256=['c' * 64]),
            lambda r: r[-1]['results'][0].update(stop_type='eos'),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                data = records(); mutate(data)
                with self.assertRaises(ValueError): fast.check_model_records(data, ['control', 'candidate'], 512)

    def test_gain_must_exceed_noise_and_threshold(self):
        self.assertTrue(fast.gate([100, 100], [90, 91])['advance'])
        self.assertFalse(fast.gate([100, 100], [99, 99])['advance'])
        self.assertFalse(fast.gate([90, 110], [94, 95])['advance'])
        self.assertTrue(fast.gate([100, 100], [105, 105])['clear_regression'])
        with self.assertRaises(ValueError): fast.gate([100], [90])
        with self.assertRaises(ValueError): fast.gate([100, 100], [0, 0])

    def test_decode_requires_every_requested_token_and_equal_outputs(self):
        data = records()
        ids = list(range(64))
        digest = hashlib.sha256(json.dumps(ids, separators=(',', ':')).encode()).hexdigest()
        for row in data:
            if row['kind'] == 'config': row['n_predict'] = 64
            else:
                row['results'][0].update(tokens_predicted=64, streamed_tokens=64,
                                         token_ids=ids[:], tokens_sha256=digest)
        self.assertEqual(len(fast.check_model_records(data, ['control', 'candidate'], 512, 64)), 2)
        for field in ('tokens_predicted', 'streamed_tokens'):
            bad = copy.deepcopy(data)
            bad[-1]['results'][0][field] = 63
            with self.assertRaises(ValueError): fast.check_model_records(bad, ['control', 'candidate'], 512, 64)
        bad = copy.deepcopy(data)
        bad[-1]['results'][0]['token_ids'][-1] = 99
        bad[-1]['results'][0]['tokens_sha256'] = hashlib.sha256(
            json.dumps(bad[-1]['results'][0]['token_ids'], separators=(',', ':')).encode()).hexdigest()
        with self.assertRaises(ValueError): fast.check_model_records(bad, ['control', 'candidate'], 512, 64)

    def test_resume_rejects_corrupt_artifacts_and_changed_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = fast.Runner(root, root, 'screen'); runner.fingerprint = 'original'
            artifact = root / 'native.log'; artifact.write_text('PASS')
            called = []
            def stage():
                called.append(1)
                return {'cases_per_layout': 241}, [artifact]
            runner.stage('numeric', stage); runner.stage('numeric', stage)
            self.assertEqual(len(called), 1)
            runner.fingerprint = 'changed'
            with self.assertRaises(ValueError): runner.stage('numeric', stage)
            runner.fingerprint = 'original'; artifact.write_text('changed')
            with self.assertRaises(ValueError): runner.stage('numeric', stage)

    def test_real_model_metadata_and_skipped_vocabulary(self):
        def string(s):
            b = s.encode(); return struct.pack('<Q', len(b)) + b
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'test.gguf'
            entries = [('general.architecture', 8, string('qwen35')),
                       ('tokenizer.ggml.tokens', 9, struct.pack('<IQ', 8, 2) + string('a') + string('b'))]
            entries += [('qwen35.attention.' + key, 4, struct.pack('<I', val)) for key, val in
                        (('head_count', 16), ('head_count_kv', 4), ('key_length', 256), ('value_length', 256))]
            p.write_bytes(b'GGUF' + struct.pack('<IQQ', 3, 0, len(entries)) +
                          b''.join(string(k) + struct.pack('<I', t) + v for k, t, v in entries))
            self.assertEqual(fast.model_shape(p), {'heads': 16, 'kv_heads': 4, 'dk': 256, 'dv': 256})
            p.write_bytes(p.read_bytes()[:20])
            with self.assertRaises(ValueError): fast.model_shape(p)


if __name__ == '__main__':
    unittest.main()
