#!/usr/bin/env python3
"""检查会话计划、失败隔离与子进程清理。"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import batch_controller as controller
import multi_turn_batch as batch


class BatchTest(unittest.TestCase):
    def test_plan_contains_both_models_and_all_conversations(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = {key: '/runtime/' + key for key in batch.RUNTIME_KEYS}
            runtime['turn_timeout_s'] = 900
            jobs = batch.prepare_jobs(root, runtime, ['2B', '4B'])
            self.assertEqual(len(jobs), 12)
            self.assertEqual(len({job['id'] for job in jobs}), 12)
            self.assertEqual(sum(job['dependency'] == '2B' for job in jobs), 6)
            for job in jobs:
                config = json.loads(Path(job['argv'][-1]).read_text())
                arguments = config['arguments']
                self.assertEqual(arguments[arguments.index('--model') + 1], job['dependency'])
                self.assertEqual(arguments[arguments.index('--conversation') + 1],
                                 job['id'].split('-', 1)[1])
                self.assertEqual(job['timeout_s'], 3960)
                self.assertEqual(Path(config['attempt']).name, job['id'])
                self.assertEqual(arguments[arguments.index('--timeout') + 1], '900')

    def test_quality_totals_keep_review_and_unattempted_turns(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = {key: '/runtime/' + key for key in batch.RUNTIME_KEYS}
            runtime['turn_timeout_s'] = 900
            jobs = batch.prepare_jobs(root, runtime, ['2B', '4B'])
            folder = root / 'batch/attempts/2b-site_totals/result/conversations/site_totals'
            for index, passed in enumerate((True, False, True, None), 1):
                turn = folder / f'turn-{index}'
                turn.mkdir(parents=True)
                (turn / 'quality.json').write_text(json.dumps({
                    'passed': passed, 'format_warnings': ['额外说明'] if index == 1 else []}))
            result = batch.summarize_quality(root, jobs)
            self.assertEqual(result['models']['2B'], {
                'correct': 2, 'incorrect': 1, 'review_required': 1, 'unattempted': 20,
                'planned': 24, 'accuracy': None, 'turns_with_format_warnings': 1})
            self.assertEqual(result['models']['4B'], {
                'correct': 0, 'incorrect': 0, 'review_required': 0, 'unattempted': 24,
                'planned': 24, 'accuracy': None, 'turns_with_format_warnings': 0})
            self.assertIsNone(result['quality_acceptance'])
            self.assertEqual(result['assessment_version'], 'v2')

    def exercise_worker(self, status=None, error=None):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = root / 'result'
            result.mkdir()
            config = root / 'config.json'
            config.write_text(json.dumps({'attempt': str(root), 'lock': '/lock', 'arguments': []}))
            if status is not None:
                (result / 'summary.json').write_text(json.dumps({'results': [{'status': status}]}))
            code = 0 if status == 'passed' else 2
            with patch.object(batch.suite, 'main', return_value=code, side_effect=error):
                if error is None:
                    self.assertEqual(batch.worker(config), code)
                    self.assertEqual(json.loads((root / 'outcome.json').read_text())['status'], status)
                else:
                    with self.assertRaises(type(error)):
                        batch.worker(config)
                    self.assertFalse((root / 'outcome.json').exists())

    def test_worker_records_passed_failed_and_incomplete(self):
        for status in ('passed', 'failed', 'incomplete'):
            with self.subTest(status=status):
                self.exercise_worker(status=status)

    def test_internal_error_stops_worker(self):
        self.exercise_worker(error=KeyError('internal fault'))

    def test_cleanup_timeout_blocks_remaining_shared_resource_jobs(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / 'process.json').write_text(json.dumps({'pgid': os.getpgrp() + 100000}))
            before, after = batch.lifecycle_hooks()
            self.assertIsNone(before({}))
            with patch.object(batch.os, 'killpg'), \
                    patch.object(batch, 'group_active', return_value=True), \
                    patch.object(batch.time, 'monotonic', side_effect=[0, 100]):
                failure = after({}, folder, 'failed')
            self.assertEqual(failure, {'status': 'incomplete', 'reason': 'worker_cleanup_timeout'})
            self.assertFalse(json.loads((folder / 'cleanup.json').read_text())['exited'])
            blocked = before({})
            self.assertEqual(blocked['status'], 'blocked')
            self.assertEqual(blocked['evidence'], [str(folder / 'cleanup.json')])

    def test_cleanup_waits_until_group_exits(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / 'process.json').write_text(json.dumps({'pgid': os.getpgrp() + 100000}))
            with patch.object(batch.os, 'killpg'), \
                    patch.object(batch, 'group_active', side_effect=[True, False]), \
                    patch.object(batch.time, 'sleep') as sleep:
                self.assertIsNone(batch.cleanup({}, folder, 'failed'))
            sleep.assert_called_once_with(.05)
            self.assertTrue(json.loads((folder / 'cleanup.json').read_text())['exited'])

    def test_crashed_worker_child_is_stopped_and_next_job_runs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / 'batch'
            first = output / 'attempts' / 'crash'
            second = output / 'attempts' / 'next'
            broken = (
                'import json,os,subprocess,sys\n'
                'from pathlib import Path\n'
                f'p=Path({str(first)!r})\n'
                "(p/'process.json').write_text(json.dumps({'pgid':os.getpgrp()}))\n"
                "child=subprocess.Popen([sys.executable,'-c','import os,time; os.fstat(9); time.sleep(60)'], pass_fds=(9,))\n"
                "(p/'child.json').write_text(json.dumps({'pid':child.pid}))\n"
                'sys.exit(7)\n')
            next_job = (
                'import json,time\nfrom pathlib import Path\n'
                f'first=Path({str(first)!r}); second=Path({str(second)!r})\n'
                "pid=json.loads((first/'child.json').read_text())['pid']\n"
                "for attempt in range(100):\n"
                "    stat=Path(f'/proc/{pid}/stat')\n"
                "    if not stat.exists() or stat.read_text().split()[2]=='Z': break\n"
                "    time.sleep(.01)\n"
                "else: raise AssertionError('orphan child remains active')\n"
                "(second/'outcome.json').write_text(json.dumps({'status':'passed'}))\n")
            jobs = [
                {'id': 'crash', 'argv': [sys.executable, '-c', broken], 'timeout_s': 5, 'dependency': ''},
                {'id': 'next', 'argv': [sys.executable, '-c', next_job], 'timeout_s': 5, 'dependency': ''},
            ]
            lock = root / 'board.lock'
            with batch.board_lock(str(lock)):
                summary = controller.run(jobs, output, after=batch.cleanup, pass_fds=(9,))
                with lock.open('w') as competitor:
                    with self.assertRaises(BlockingIOError):
                        batch.fcntl.flock(competitor, batch.fcntl.LOCK_EX | batch.fcntl.LOCK_NB)
            with lock.open('w') as competitor:
                batch.fcntl.flock(competitor, batch.fcntl.LOCK_EX | batch.fcntl.LOCK_NB)
            self.assertEqual([row['status'] for row in summary['attempts']], ['failed', 'passed'])
            self.assertFalse(summary['batch_success'])
            self.assertEqual(summary['settled'], 2)
            self.assertEqual(summary['counts']['failed'], 1)
            self.assertEqual(summary['counts']['passed'], 1)
            self.assertNotEqual(controller.exit_code(summary), 0)
            self.assertEqual(json.loads((first / 'exit-status.json').read_text())['returncode'], 7)


if __name__ == '__main__':
    unittest.main()
