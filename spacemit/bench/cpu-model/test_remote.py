"""检查远端超时与错误响应不会伪装为成功。"""
from importlib.util import module_from_spec,spec_from_file_location
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

spec=spec_from_file_location('remote_status',Path(__file__).with_name('remote-status.py'))
remote=module_from_spec(spec);spec.loader.exec_module(remote)


class RemoteStatusTests(unittest.TestCase):
    def test_timeout_is_failure(self):
        with patch.object(remote.subprocess,'run',side_effect=subprocess.TimeoutExpired('ssh',30)):
            self.assertEqual(remote.inspect('musepipro-wg','/project','session')['connection'],'failed')

    def test_nonzero_exit_is_failure(self):
        with patch.object(remote.subprocess,'run',return_value=subprocess.CompletedProcess('ssh',255,'','unreachable')):
            value=remote.inspect('musepipro-wg','/project','session')
            self.assertEqual(value['connection'],'failed')
            self.assertEqual(value['returncode'],255)

    def test_bad_json_is_failure(self):
        with patch.object(remote.subprocess,'run',return_value=subprocess.CompletedProcess('ssh',0,'truncated','')):
            self.assertEqual(remote.inspect('musepipro-wg','/project','session')['connection'],'failed')

    def test_native_failure_has_nonzero_status(self):
        value=dict(connection='available',remote=dict(stages=[dict(state='failed')],tmux_session_present=False))
        self.assertEqual(remote.exit_code(value),3)

    def test_missing_active_session_needs_inspection(self):
        value=dict(connection='available',remote=dict(stages=[dict(state='active-or-interrupted')],tmux_session_present=False))
        self.assertEqual(remote.exit_code(value),4)

    def test_remote_status_is_retained(self):
        with patch.object(remote.subprocess,'run',return_value=subprocess.CompletedProcess('ssh',0,'{"stages":[],"tmux_session_present":true}','')):
            self.assertTrue(remote.inspect('musepipro-wg','/project','session')['remote']['tmux_session_present'])


if __name__=='__main__':
    unittest.main()
