"""检查部署入口的路径隔离、参数边界与重复会话拒绝行为。"""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('committee_deploy', Path(__file__).with_name('deploy.py'))
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


class DeployTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / "release with spaces"
        self.package = self.root / 'runtime/package'
        self.package.mkdir(parents=True)
        self.binary = self.root / 'runtime/build/bin/llama-server'
        self.binary.parent.mkdir(parents=True)
        self.binary.write_text('fixture')
        (self.binary.parent.parent / 'build-receipt.json').write_text('{}')
        (self.package / 'with-lock.sh').write_text('#!/bin/bash\nexec "$@"\n')
        self.model = self.base / 'model $(touch INJECTED).gguf'
        self.model.write_text('fixture')
        self.runs = self.base / 'runs with spaces'
        (self.package / 'start.py').write_text(
            'import json,sys\nfrom pathlib import Path\n'
            'a=sys.argv[1:]\nPath(a[a.index("--receipt")+1]).write_text(json.dumps(a))\n'
            'print("fixture-server")\nsys.exit(17)\n')

    def tearDown(self):
        self.temp.cleanup()

    def command(self, *extra):
        return ['deploy.py', str(self.model), '--bundle-root', str(self.root),
                '--runs', str(self.runs), '--session', 'test_session', *extra]

    def test_shell_keeps_literal_paths_and_exit_status(self):
        record = deploy.plan(self.root, self.model, 'test_session', self.runs)
        run = Path(record['run'])
        run.mkdir(parents=True)
        result = subprocess.run(['bash', '-c', record['shell']], cwd=self.root)
        self.assertEqual(result.returncode, 17)
        self.assertEqual((run / 'exit-status').read_text(), '17\n')
        args = json.loads((run / 'launch.json').read_text())
        self.assertEqual(args[args.index('--model') + 1], str(self.model))
        self.assertEqual((run / 'server.log').read_text(), 'fixture-server\n')
        self.assertFalse((self.root / 'INJECTED').exists())
        self.assertEqual(set(args[::2]), {'--model', '--port', '--receipt'})

    def test_rejects_invalid_port_or_session(self):
        for port in (0, 65536):
            with self.assertRaises(ValueError):
                deploy.plan(self.root, self.model, 'test_session', self.runs, port=port)
        for name in ('bad;command', 'name:window', '../escape'):
            with self.assertRaises(ValueError):
                deploy.plan(self.root, self.model, name, self.runs)

    def test_preview_has_no_side_effects(self):
        with patch.object(sys, 'argv', self.command('--describe')):
            deploy.main()
        self.assertFalse(self.runs.exists())

    def test_rejects_other_architecture_before_spawn(self):
        with patch.object(sys, 'argv', self.command()), patch.object(deploy.platform, 'machine', return_value='x86_64'):
            with self.assertRaises(SystemExit) as error:
                deploy.main()
        self.assertEqual(error.exception.code, 1)
        self.assertFalse(self.runs.exists())

    def test_rejects_existing_session_without_new_run(self):
        with patch.object(sys, 'argv', self.command()), \
             patch.object(deploy.platform, 'system', return_value='Linux'), \
             patch.object(deploy.platform, 'machine', return_value='riscv64'), \
             patch.object(deploy.shutil, 'which', return_value='/fixture/tool'), \
             patch.object(deploy.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)) as call:
            with self.assertRaises(SystemExit):
                deploy.main()
        self.assertEqual(call.call_count, 1)
        self.assertFalse(self.runs.exists())

    def test_rejects_missing_bundle_file(self):
        self.binary.unlink()
        with self.assertRaises(ValueError):
            deploy.plan(self.root, self.model, 'test_session', self.runs)

    def test_creates_one_session_and_retains_command_record(self):
        with patch.object(sys, 'argv', self.command()), \
             patch.object(deploy.platform, 'system', return_value='Linux'), \
             patch.object(deploy.platform, 'machine', return_value='riscv64'), \
             patch.object(deploy.shutil, 'which', return_value='/fixture/tool'), \
             patch.object(deploy.Path, 'home', return_value=self.base), \
             patch.object(deploy.subprocess, 'run', side_effect=[subprocess.CompletedProcess([], 1), subprocess.CompletedProcess([], 0)]) as call:
            deploy.main()
        self.assertEqual(call.call_count, 2)
        record = json.loads((self.runs / 'test_session/deployment.json').read_text())
        self.assertEqual(record['performance_flags'], [])
        self.assertEqual(record['context'], 12288)
        self.assertEqual(call.call_args.args[0][:4], ['tmux', 'new-session', '-d', '-s'])


if __name__ == '__main__':
    unittest.main()
