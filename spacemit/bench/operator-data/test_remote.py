"""用本机假客户端检查断线与超时，不访问远程机器。"""
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import time
import unittest

from remote import execute, ssh_arguments


class RemoteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.receipt = self.root/'receipt.json'

    def tearDown(self):
        self.temp.cleanup()

    def client(self, code, deadline=2):
        return execute([sys.executable, '-c', code], self.receipt, deadline)

    def test_success_does_not_claim_board_job_completion(self):
        value = self.client('print("launch acknowledged")')
        self.assertEqual(value['status'], 'remote-command-complete')
        self.assertEqual(value['remote_task_state'], 'unknown')
        self.assertIn('launch acknowledged', Path(str(self.receipt)+'.stdout').read_text())

    def test_disconnect_does_not_claim_job_failure_or_retry(self):
        value = self.client('raise SystemExit(255)')
        self.assertEqual(value['status'], 'ssh-error')
        self.assertEqual(value['remote_task_state'], 'unknown')
        self.assertFalse(value['automatic_retry'])
        self.assertEqual(json.loads(self.receipt.read_text()), value)

    def test_remote_command_failure(self):
        value = self.client('raise SystemExit(7)')
        self.assertEqual(value['status'], 'remote-command-failed')
        self.assertEqual(value['exit_code'], 7)

    def test_deadline_stops_child_even_if_parent_ignores_signal(self):
        pidfile = self.root/'child.pid'
        code = ('import subprocess,sys,signal,time; '
                'signal.signal(signal.SIGTERM,signal.SIG_IGN); '
                'child=subprocess.Popen([sys.executable,"-c","import time; time.sleep(30)"]); '
                f'open({str(pidfile)!r},"w").write(str(child.pid)); time.sleep(30)')
        start = time.monotonic()
        value = self.client(code, 0.4)
        self.assertEqual(value['status'], 'client-deadline')
        self.assertLess(time.monotonic()-start, 3)
        pid = int(pidfile.read_text())
        try:
            status = Path(f'/proc/{pid}/stat').read_text().split()[2]
            self.assertEqual(status, 'Z')
        except FileNotFoundError:
            pass
        finally:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    def test_existing_receipt_is_preserved(self):
        self.receipt.write_text('existing')
        with self.assertRaises(FileExistsError):
            self.client('raise SystemExit(0)')
        self.assertEqual(self.receipt.read_text(), 'existing')

    def test_ssh_skips_stale_mux_and_rejects_host_options(self):
        args = ssh_arguments('musepipro-wg', ['printf', 'a b; c'])
        self.assertIn('ControlPath=none', args)
        self.assertIn('ServerAliveCountMax=2', args)
        self.assertEqual(args[-1], "printf 'a b; c'")
        with self.assertRaises(ValueError):
            ssh_arguments('-oProxyCommand=anything', ['hostname'])


if __name__ == '__main__':
    unittest.main()
