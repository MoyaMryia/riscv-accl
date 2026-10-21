import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

PATH = Path(__file__).with_name('batch_controller.py')
SPEC = importlib.util.spec_from_file_location('batch_controller_under_test', PATH)
controller = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(controller)


class BatchControllerTests(unittest.TestCase):
    def worker(self, directory, code):
        return [sys.executable, '-c', code, str(directory)]

    def test_frozen_batch_runs_all_jobs_and_keeps_each_result(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'out'
            jobs = []
            jobs.append({'id': 'passed1', 'argv': self.worker('PATH', ""), 'timeout_s': 3, 'dependency': 'a'})
            scripts = [
                "import json,pathlib,sys; p=pathlib.Path(sys.argv[1]); print('truncated'); (p/'outcome.json').write_text(json.dumps({'status':'incomplete','reason':'truncated'})); sys.exit(3)",
                "import time; time.sleep(20)",
                "import os,signal; os.kill(os.getpid(), signal.SIGKILL)",
                "raise AssertionError('worker assertion')",
                "import json,pathlib,sys; p=pathlib.Path(sys.argv[1]); (p/'outcome.json').write_text(json.dumps({'status':'failed','reason':'functional'})); sys.exit(2)",
                "import json,pathlib,sys; p=pathlib.Path(sys.argv[1]); print('done'); (p/'outcome.json').write_text(json.dumps({'status':'passed'}))",
            ]
            ids = ['truncated', 'timedout', 'workercrash', 'assertion', 'functional', 'passed2']
            for name, script in zip(ids, scripts):
                jobs.append({'id': name, 'argv': self.worker('{attempt}', script),
                             'timeout_s': 0.15 if name == 'timedout' else 3, 'dependency': 'shared'})
            # 将路径写入 worker 参数，模拟调用方准备 argv。
            for job in jobs:
                if job['id'] == 'passed1':
                    script = "import json,pathlib,sys; p=pathlib.Path(sys.argv[1]); (p/'outcome.json').write_text(json.dumps({'status':'passed'}))"
                else:
                    script = job['argv'][2]
                job['argv'] = self.worker(root / 'attempts' / job['id'], script)
            summary = controller.run(jobs, root)
            self.assertEqual([row['status'] for row in summary['attempts']],
                             ['passed', 'incomplete', 'incomplete', 'failed', 'failed', 'failed', 'passed'])
            self.assertEqual(summary['counts'], {'passed': 2, 'failed': 3, 'incomplete': 2,
                                                 'blocked': 0, 'unattempted': 0})
            self.assertEqual(summary['planned'], sum(summary['counts'].values()))
            self.assertFalse(summary['batch_success'])
            self.assertTrue((root / 'attempts/passed2/stdout.log').read_text())
            self.assertEqual(json.loads((root / 'attempts/functional/exit-status.json').read_text())['returncode'], 2)
            self.assertEqual(json.loads((root / 'progress.json').read_text())['settled'], 7)
            self.assertEqual(controller.exit_code(summary), 2)

    def test_each_failure_keeps_final_gate_false(self):
        cases = [
            ("import json,pathlib,sys; (pathlib.Path(sys.argv[1])/'outcome.json').write_text(json.dumps({'status':'incomplete'})); sys.exit(3)", 'incomplete'),
            ("import time; time.sleep(10)", 'timeout'),
            ("import os,signal; os.kill(os.getpid(),signal.SIGKILL)", 'crash'),
            ("raise AssertionError()", 'assertion'),
            ("import json,pathlib,sys; (pathlib.Path(sys.argv[1])/'outcome.json').write_text(json.dumps({'status':'failed'})); sys.exit(2)", 'functional'),
        ]
        for script, label in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp:
                root = Path(temp) / 'out'
                job = {'id': 'one', 'argv': self.worker(root / 'attempts/one', script),
                       'timeout_s': 0.1 if label == 'timeout' else 2, 'dependency': 'x'}
                summary = controller.run([job], root)
                self.assertFalse(summary['batch_success'])
                self.assertEqual(controller.exit_code(summary), 2)
                self.assertEqual(sum(summary['counts'].values()), 1)

    def test_protocol_failures_and_nonzero_pass_report_fail(self):
        scripts = [
            "import json,pathlib,sys; (pathlib.Path(sys.argv[1])/'outcome.json').write_text('{')",
            "pass",
            "import json,pathlib,sys; (pathlib.Path(sys.argv[1])/'outcome.json').write_text(json.dumps({'status':'passed'})); sys.exit(2)",
        ]
        for index, script in enumerate(scripts):
            with self.subTest(index=index), tempfile.TemporaryDirectory() as temp:
                root = Path(temp) / 'out'
                job = {'id': 'one', 'argv': self.worker(root / 'attempts/one', script),
                       'timeout_s': 2, 'dependency': 'x'}
                result = controller.run([job], root)
                self.assertEqual(result['attempts'][0]['status'], 'failed')
                self.assertEqual(result['attempts'][0]['reason'], 'worker_protocol' if index < 2 else 'worker_exit')
                self.assertFalse(result['batch_success'])

    def test_hooks_and_dependency_block_are_isolated(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'out'
            events = []
            def guard(job):
                events.append(('guard-enter', job['id']))
                class Scope:
                    def __enter__(self):
                        return None
                    def __exit__(self, *args):
                        events.append(('guard-exit', job['id']))
                return Scope()
            def before(job):
                return {'status': 'blocked', 'reason': 'backend_unavailable', 'evidence': 'lock'} if job['id'] == 'blocked' else None
            def after(job, folder, status):
                self.assertEqual(events[-1][0], 'guard-enter')
                events.append(('after', job['id'], status))
            jobs = []
            for name in ('blocked', 'next'):
                script = "import json,pathlib,sys; (pathlib.Path(sys.argv[1])/'outcome.json').write_text(json.dumps({'status':'passed'}))"
                jobs.append({'id': name, 'argv': self.worker(root / 'attempts' / name, script),
                             'timeout_s': 2, 'dependency': name})
            result = controller.run(jobs, root, guard=guard, before=before, after=after)
            self.assertEqual([item['status'] for item in result['attempts']], ['blocked', 'passed'])
            self.assertEqual([event[1] for event in events if event[0] == 'after'], ['next'])
            self.assertFalse(result['batch_success'])
            self.assertEqual(json.loads((root / 'attempts/blocked/status.json').read_text())['evidence'], 'lock')

    def test_backend_cleanup_failure_is_reported_after_worker_completion(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'out'
            script = "import json,pathlib,sys; (pathlib.Path(sys.argv[1])/'outcome.json').write_text(json.dumps({'status':'passed'}))"
            job = {'id': 'one', 'argv': [sys.executable, '-c', script, str(root / 'attempts/one')],
                   'timeout_s': 2, 'dependency': 'x'}
            def after(job, folder, status):
                self.assertEqual(status, 'passed')
                return {'status': 'failed', 'reason': 'backend_busy'}
            result = controller.run([job], root, after=after)
            row = result['attempts'][0]
            self.assertEqual(row['status'], 'failed')
            self.assertEqual(row['reason'], 'backend_busy')
            self.assertEqual(row['worker_status'], {'status': 'passed', 'reason': 'passed'})
            self.assertFalse(result['batch_success'])

    def test_output_must_be_new_and_job_input_is_checked(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'out'
            root.mkdir()
            valid = {'id': 'one', 'argv': [sys.executable, '-c', 'pass'],
                     'timeout_s': 1, 'dependency': 'x'}
            with self.assertRaises(FileExistsError):
                controller.run([valid], root)
            with self.assertRaises(ValueError):
                controller.run([], Path(temp) / 'empty')


if __name__ == '__main__':
    unittest.main()
