"""检查已有服务的附加采集入口和 PID 生命周期。"""
import copy
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import attach_trace
import diagnostic as base
import discovery_cases

POLICY = base.load_module('attach_test_policy', Path(__file__).parents[2] / 'serve/decode-router/policy.py')


class AttachTraceTests(unittest.TestCase):
    def test_live_process_tracks_start_identity(self):
        process = attach_trace.LiveProcess(os.getpid())
        self.assertIsNone(process.poll())
        status = process._stat()
        with mock.patch.object(process, '_stat', return_value=[*status[:19], 'different', *status[20:]]):
            self.assertEqual(process.poll(), 1)
        status[0] = 'Z'
        with mock.patch.object(process, '_stat', return_value=status):
            self.assertEqual(process.poll(), 1)
        with mock.patch.object(process, '_stat', side_effect=FileNotFoundError):
            self.assertEqual(process.poll(), 1)
        with self.assertRaisesRegex(ValueError, 'PID'):
            attach_trace.LiveProcess(True)

    def test_generic_dataset_keeps_unequal_counts_and_rejects_bad_references(self):
        cases = discovery_cases.build_cases()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'cases.json'
            path.write_text(json.dumps(cases))
            rows = attach_trace.read_cases(path, POLICY, discovery_cases)
            self.assertEqual(len(rows), 48)
            self.assertEqual(sum(r['category'] == 'code' for r in rows), 24)
            for field, value in [('case_id', cases[1]['case_id']), ('code_task', 'unknown'), ('required_facts', [3])]:
                bad = copy.deepcopy(cases)
                bad[0][field] = value
                path.write_text(json.dumps(bad))
                with self.subTest(field=field), self.assertRaises(ValueError):
                    attach_trace.read_cases(path, POLICY, discovery_cases)
            bad = copy.deepcopy(cases)
            bad[0]['messages'] = bad[1]['messages']
            path.write_text(json.dumps(bad))
            with self.assertRaisesRegex(ValueError, 'text is repeated'):
                attach_trace.read_cases(path, POLICY, discovery_cases)

    def test_input_registry_uses_the_existing_service_lease(self):
        args = SimpleNamespace(service=Path('/service'), cases=Path('/cases'), diagnostic_plan=Path('/plan'),
            legacy_request=Path('/legacy'), cases_module=Path('/assessment'), chat=Path('/chat'), quality=Path('/quality'))
        paths = attach_trace.input_paths(args)
        self.assertEqual(paths['request_lease'], Path('/service/router/request_lease.py'))
        self.assertEqual(paths['policy'], Path('/service/router/policy.py'))

    def test_completion_matches_the_recorded_protocol_not_zero_counts(self):
        self.assertEqual(attach_trace.verify_completion({'completed': 81, 'planned': 81}, {'planned': 81}), 81)
        with self.assertRaisesRegex(RuntimeError, 'counts differ'):
            attach_trace.verify_completion({'completed': 0, 'planned': 0}, {'planned': 81})
        with self.assertRaisesRegex(ValueError, 'invalid'):
            attach_trace.verify_completion({'completed': 0, 'planned': 0}, {'planned': 0})
        with self.assertRaisesRegex(RuntimeError, 'incomplete'):
            attach_trace.verify_completion({'completed': 80, 'planned': 81}, {'planned': 81})

    def test_stale_receipt_fails_before_attachment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / 'artifact'
            artifact.write_bytes(b'abc')
            receipt = root / 'receipt.json'
            receipt.write_text('{"fixture":"wrong"}')
            argv = []
            for key in ('service', 'cases', 'cases-module', 'chat', 'quality', 'diagnostic-plan', 'legacy-request'):
                argv.extend(['--' + key, str(root / 'unused')])
            argv.extend(['--output', str(root / 'output'), '--tool-receipt', str(receipt)])
            with mock.patch.dict(os.environ, {'TMUX': 'test'}), \
                 mock.patch.object(attach_trace, 'input_paths', return_value={'fixture': artifact}):
                with self.assertRaisesRegex(ValueError, 'hashes differ'):
                    attach_trace.main(argv)


if __name__ == '__main__':
    unittest.main()
