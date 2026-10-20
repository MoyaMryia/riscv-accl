"""检查独立请求工作进程和完成配对汇总。"""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import urllib.error

import attempt_worker
import isolated_trace
import repetition_guard

HERE = Path(__file__).resolve().parent




class IsolatedTraceTests(unittest.TestCase):
    def test_timing_summary_excludes_failed_and_incomplete_attempts(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            queue = []
            arms = ('direct', 'prefix', 'lowacc')
            for index, arm in enumerate(arms):
                queue.append(('code', 1, {'case_id': 'x', 'category': 'code'}, arm))
            attempts = []
            for index, (stage, repeat, case, arm) in enumerate(queue):
                folder = root / 'attempts' / str(index)
                folder.mkdir(parents=True)
                reason = 'complete' if arm == 'direct' else 'quality' if arm == 'prefix' else 'output_limit'
                if reason != 'output_limit':
                    passed = reason in ('complete', 'quality')
                    (folder / 'outcome.json').write_text(json.dumps(
                        {'status': 'passed' if passed else 'failed', 'reason': reason}))
                    (folder / 'result.json').write_text(json.dumps({
                        'case_id': 'x', 'arm': arm,
                        'response': {'wall_s': 2.0, 'ttft_s': 1.0,
                                     'timings': {'prompt_ms': 10.0, 'predicted_ms': 20.0}},
                        'quality': {'passed': reason in ('complete', 'quality')},
                        'verification': None, 'draft_duration_delta_ms': None,
                        'coverage': {'prefix_fraction': 0.5}, 'fallback_events': []}))
                attempts.append({'attempt': str(folder), 'reason': reason})
            result = isolated_trace.timing_summary(queue, {'attempts': attempts, 'batch_success': False})
            self.assertEqual(result['complete_triplets'], 0)
            self.assertEqual(result['excluded_triplets'], 1)
            self.assertEqual(result['quality_review_pending'], 0)
            self.assertEqual(result['observations']['cases'], {})
            self.assertFalse(result['adoption_gate'])

            (Path(attempts[2]['attempt']) / 'outcome.json').write_text(json.dumps(
                {'status': 'incomplete', 'reason': 'quality_review_pending'}))
            (Path(attempts[2]['attempt']) / 'result.json').write_text(json.dumps({
                'case_id': 'x', 'arm': 'lowacc',
                'response': {'wall_s': 3.0, 'ttft_s': 1.0,
                             'timings': {'prompt_ms': 10.0, 'predicted_ms': 30.0}},
                'quality': {'passed': None}, 'verification': None,
                'draft_duration_delta_ms': None, 'coverage': {'prefix_fraction': 0.5},
                'fallback_events': []}))
            attempts[2]['reason'] = 'quality_review_pending'
            result = isolated_trace.timing_summary(queue, {'attempts': attempts, 'batch_success': False})
            self.assertEqual(result['complete_triplets'], 1)
            self.assertEqual(result['quality_review_pending'], 1)

    def test_worker_preserves_output_limit_and_transport_failures(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = {'case': {}, 'category': 'code', 'round': 1, 'arm': 'prefix',
                'legacy': False, 'pid': 1, 'url': 'http://unused', 'log_path': str(root / 'server.log'),
                'folder': str(root / 'attempt'), 'max_tokens': 4096, 'prefix_rows': 65536,
                'chat': str(HERE.parents[1] / 'serve/cached-document-chat.py'),
                'assessment': str(HERE / 'discovery_cases.py'),
                'quality': str(HERE.parents[1] / 'release-candidate/tests/quality.py')}
            path = root / 'job.json'
            path.write_text(json.dumps(config))
            (root / 'attempt').mkdir()
            with mock.patch('trace_cases.sample', side_effect=isolated_trace.trace_cases.OutputTruncated('limit')):
                status = attempt_worker.main(['--config', str(path)])
            self.assertEqual(status, 3)
            outcome = json.loads((root / 'attempt/outcome.json').read_text())
            self.assertEqual(outcome, {'status': 'incomplete', 'reason': 'output_limit'})

            config['folder'] = str(root / 'transport')
            path.write_text(json.dumps(config))
            (root / 'transport').mkdir()
            with mock.patch('trace_cases.sample', side_effect=urllib.error.URLError('server unavailable')):
                status = attempt_worker.main(['--config', str(path)])
            self.assertEqual(status, 3)
            outcome = json.loads((root / 'transport/outcome.json').read_text())
            self.assertEqual(outcome['status'], 'incomplete')
            self.assertEqual(outcome['reason'], 'request_transport')

            config['folder'] = str(root / 'degenerate')
            path.write_text(json.dumps(config))
            (root / 'degenerate').mkdir()
            with mock.patch('trace_cases.sample', side_effect=repetition_guard.DegenerateOutput('loop')):
                status = attempt_worker.main(['--config', str(path)])
            self.assertEqual(status, 3)
            outcome = json.loads((root / 'degenerate/outcome.json').read_text())
            self.assertEqual(outcome, {'status': 'incomplete', 'reason': 'degenerate_repetition'})

    def test_batch_status_keeps_failed_controller_nonzero(self):
        controller = {'batch_success': False, 'planned': 4,
                      'counts': {'passed': 3, 'failed': 1, 'incomplete': 0, 'blocked': 0, 'unattempted': 0}}
        status = isolated_trace.batch_status(controller)
        self.assertEqual(status['exit_code'], 2)
        self.assertFalse(status['batch_success'])
        self.assertEqual(status['counts']['failed'], 1)
        passed = {'batch_success': True, 'planned': 1,
                  'counts': {'passed': 1, 'failed': 0, 'incomplete': 0, 'blocked': 0, 'unattempted': 0}}
        self.assertEqual(isolated_trace.batch_status(passed)['exit_code'], 0)

    def test_backend_busy_blocks_only_the_affected_arm(self):
        class Lease:
            def acquire(self, path):
                import contextlib
                return contextlib.nullcontext()

        class Process:
            pid = 4321
            def poll(self):
                return None

        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / 'attempt'
            folder.mkdir()
            args = mock.Mock(lease=Lease(), request_lock=Path(temp) / 'request.lock')
            processes = {'direct': Process(), 'prefix': Process(), 'lowacc': Process()}
            urls = {arm: 'http://' + arm for arm in processes}
            guard, before, after = isolated_trace.backend_hooks(args, processes, urls)
            with mock.patch.object(isolated_trace, 'wait_idle', side_effect=isolated_trace.BackendBusy('busy')):
                self.assertEqual(after({'dependency': 'prefix'}, folder, 'passed'),
                                 {'status': 'failed', 'reason': 'backend_busy'})
            self.assertEqual(before({'dependency': 'prefix'})['status'], 'blocked')
            self.assertEqual(before({'dependency': 'prefix'})['reason'], 'backend_busy')
            self.assertIsNone(before({'dependency': 'direct'}))
            with mock.patch.object(isolated_trace, 'wait_idle', return_value=[{'is_processing': False}]), \
                    mock.patch.object(isolated_trace.base, 'save'):
                self.assertIsNone(after({'dependency': 'direct'}, folder, 'passed'))
            self.assertIsNone(before({'dependency': 'direct'}))

    def test_backend_wait_rejects_invalid_slot_state(self):
        with mock.patch.object(isolated_trace, 'slots', side_effect=isolated_trace.BackendStateError('bad state')):
            with self.assertRaises(isolated_trace.BackendStateError):
                isolated_trace.wait_idle('http://unused', deadline_s=0)


if __name__ == '__main__':
    unittest.main()
