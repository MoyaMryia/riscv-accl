#!/usr/bin/env python3
"""Exercise bounded judge recovery without credentials or network requests."""
import http.client
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('judge', Path(__file__).with_name('judge-shared-document-cache.py'))
judge = importlib.util.module_from_spec(spec); spec.loader.exec_module(judge)


def response(finish='stop', valid=True):
    answer = {'score': 4, 'reason': 'supported', 'factual_errors': [], 'missing_points': []}
    content = json.dumps({'answer_a': answer, 'answer_b': answer}) if valid else '{unfinished'
    return io.BytesIO(json.dumps({'choices': [{'finish_reason': finish, 'message': {'content': content}}],
                                 'usage': {'completion_tokens': 30}}).encode())


class TransportTests(unittest.TestCase):
    def call(self, retries=2):
        return judge.chat_completion('https://example.invalid/v1/chat/completions', 'test-model',
                                     'dummy-test-key', [], 1, retries, 256)

    def test_disconnect_and_partial_read_recover(self):
        failures = [http.client.RemoteDisconnected('disconnected'), http.client.IncompleteRead(b'partial')]
        with patch.object(judge.urllib.request, 'urlopen', side_effect=failures + [response()]) as request, \
             patch.object(judge.time, 'sleep') as sleep:
            result, usage = self.call()
            self.assertEqual(result['answer_a']['score'], 4)
            self.assertEqual(usage['completion_tokens'], 30)
            self.assertEqual(request.call_count, 3)
            self.assertEqual(sleep.call_count, 2)

    def test_invalid_and_truncated_judgments_recover_without_changing_budget(self):
        with patch.object(judge.urllib.request, 'urlopen', side_effect=[response(valid=False), response('length'), response()]) as request, \
             patch.object(judge.time, 'sleep'):
            self.call()
            for call in request.call_args_list:
                payload = json.loads(call.args[0].data)
                self.assertEqual(payload['max_completion_tokens'], 256)
                self.assertEqual(payload['messages'], [])

    def test_invalid_judgments_exhaust_bounded_retries(self):
        with patch.object(judge.urllib.request, 'urlopen', side_effect=[response(valid=False) for _ in range(3)]) as request, \
             patch.object(judge.time, 'sleep'):
            with self.assertRaisesRegex(ValueError, 'bounded retries') as error:
                self.call()
            self.assertEqual(request.call_count, 3)
            self.assertNotIn('dummy-test-key', str(error.exception))

    def test_connection_failure_exhausts_bounded_retries(self):
        with patch.object(judge.urllib.request, 'urlopen', side_effect=TimeoutError('internal detail')) as request, \
             patch.object(judge.time, 'sleep'):
            with self.assertRaisesRegex(RuntimeError, 'connection failed'):
                self.call(retries=1)
            self.assertEqual(request.call_count, 2)


if __name__ == '__main__':
    unittest.main()
