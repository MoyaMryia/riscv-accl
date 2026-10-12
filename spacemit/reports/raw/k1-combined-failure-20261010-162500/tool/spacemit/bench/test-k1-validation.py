#!/usr/bin/env python3
"""Acceptance gates: reject cached, incomplete, unequal or regressing results."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('validation', HERE / 'k1-validation.py')
validation = importlib.util.module_from_spec(spec); spec.loader.exec_module(validation)


def fixture():
    rows = []; labels = []
    ids = list(range(64))
    digest = hashlib.sha256(json.dumps(ids, separators=(',', ':')).encode()).hexdigest()
    for i, mode in enumerate((0, 3, 3, 0)):
        label = f'2B-8192-q{mode}-pass{i+1}'; labels.append(label)
        rows.append({'kind': 'config', 'label': label, 'n_predict': 64,
                     'cache_prompt': False, 'verify_cold': True})
        rows.append({'kind': 'measurement', 'label': label, 'context_tokens': 8192,
            'prompt_token_sha256': ['a' * 64], 'results': [{
                'stop_type': 'limit', 'tokens_predicted': 64, 'streamed_tokens': 64,
                'token_ids': ids, 'tokens_sha256': digest, 'sha256': 'b' * 64, 'ttft_ms': 100,
                'timings': {'cache_n': 0, 'prompt_n': 8192, 'prompt_ms': 100 if mode == 0 else 90,
                            'predicted_n': 64, 'predicted_ms': 100 if mode == 0 else 80}}]})
    return rows, labels


class Gates(unittest.TestCase):
    def test_long_routing_acceptance(self):
        rows, labels = fixture()
        self.assertTrue(validation.routing_gate(rows, labels)['eligible'])
        for field, bad in (('streamed_tokens', 63), ('tokens_predicted', 63), ('stop_type', 'eos'), ('tokens_sha256', 'f' * 64)):
            altered = copy.deepcopy(rows); altered[3]['results'][0][field] = bad
            with self.assertRaises(ValueError): validation.routing_gate(altered, labels)
        altered = copy.deepcopy(rows); altered[3]['results'][0]['timings']['cache_n'] = 1
        with self.assertRaises(ValueError): validation.routing_gate(altered, labels)
        altered = copy.deepcopy(rows); altered[3]['prompt_token_sha256'] = ['f' * 64]
        with self.assertRaises(ValueError): validation.routing_gate(altered, labels)

    def test_regression_and_noise_do_not_advance(self):
        rows, labels = fixture()
        for row in rows:
            if row['kind'] == 'measurement' and '-q3-' in row['label']:
                row['results'][0]['timings']['predicted_ms'] = 105
        self.assertFalse(validation.routing_gate(rows, labels)['eligible'])
        rows, labels = fixture(); rows[-1]['results'][0]['timings']['prompt_ms'] = 150
        self.assertFalse(validation.routing_gate(rows, labels)['eligible'])

    def test_natural_completion_cold_and_usage_required(self):
        result = {'finish_reason': 'stop', 'answer': '78 [S1] [S3] [S5]', 'server_slot': 0,
                  'usage': {'prompt_tokens': 4200, 'completion_tokens': 12,
                            'prompt_tokens_details': {'cached_tokens': 0}}}
        self.assertTrue(validation.complete_answer(result, 4200))
        for field, bad in (('finish_reason', 'length'), ('answer', ''), ('reasoning_text', 'thinking'), ('server_slot', 1)):
            modified = copy.deepcopy(result); modified[field] = bad
            self.assertFalse(validation.complete_answer(modified, 4200))
        modified = copy.deepcopy(result); modified['usage']['prompt_tokens_details']['cached_tokens'] = 4000
        self.assertFalse(validation.complete_answer(modified, 4200))
        self.assertFalse(validation.complete_answer(result, 4199))

    def test_mtp_failure_keeps_independent_stage_runnable(self):
        with tempfile.TemporaryDirectory() as directory:
            run = object.__new__(validation.Run)
            run.root = Path(directory); run.started = 0; run.interrupted = False
            run.summary = {'status': 'running', 'stages': {}, 'limitations': ''}
            def fail(): raise ValueError('state mismatch')
            self.assertEqual(run.stage('state', fail)['status'], 'failed')
            self.assertEqual(run.stage('direct', lambda: {'status': 'pass'})['status'], 'pass')

    def test_first_difference_includes_length(self):
        self.assertEqual(validation.first_difference([1, 2], [1, 3]), 1)
        self.assertEqual(validation.first_difference([1], [1, 2]), 1)
        self.assertIsNone(validation.first_difference([1], [1]))


if __name__ == '__main__': unittest.main()
