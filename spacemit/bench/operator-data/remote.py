#!/usr/bin/env python3
"""限制远程客户端等待时间，并保留任务状态未知的事实。"""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
import sys


def timestamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def ssh_arguments(host, command):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.@:-]*', host):
        raise ValueError('invalid host')
    if not command:
        raise ValueError('missing remote command')
    return ['ssh', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectionAttempts=1',
            '-o', 'ConnectTimeout=10', '-o', 'ServerAliveInterval=5',
            '-o', 'ServerAliveCountMax=2', '-o', 'ControlMaster=no',
            '-o', 'ControlPath=none', '--', host, shlex.join(command)]


def stop_group(process):
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=0.5)
        except subprocess.TimeoutExpired:
            pass
    process.wait()


def execute(arguments, receipt, deadline):
    if deadline <= 0:
        raise ValueError('deadline must be positive')
    receipt = Path(receipt)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    value = {'schema': 1, 'status': 'client-start', 'started_at_utc': timestamp(),
             'arguments': arguments, 'deadline_seconds': deadline,
             'remote_task_state': 'unknown', 'automatic_retry': False}
    with receipt.open('x') as handle:
        json.dump(value, handle, indent=2)
        handle.write('\n')
    process = None
    try:
        with Path(str(receipt)+'.stdout').open('x') as out, Path(str(receipt)+'.stderr').open('x') as err:
            process = subprocess.Popen(arguments, stdin=subprocess.DEVNULL, stdout=out,
                                       stderr=err, start_new_session=True)
            try:
                code = process.wait(timeout=deadline)
                value['exit_code'] = code
                value['status'] = ('remote-command-complete' if code == 0 else
                                   'ssh-error' if code == 255 else 'remote-command-failed')
            except subprocess.TimeoutExpired:
                stop_group(process)
                value.update(status='client-deadline', exit_code=124)
            except KeyboardInterrupt:
                stop_group(process)
                value.update(status='client-interrupted', exit_code=130)
    except OSError as error:
        if process is not None and process.poll() is None:
            stop_group(process)
        value.update(status='client-error', exit_code=125, error=str(error))
    value['finished_at_utc'] = timestamp()
    temporary = Path(str(receipt)+'.tmp')
    temporary.write_text(json.dumps(value, indent=2)+'\n')
    temporary.replace(receipt)
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--deadline', type=float, default=60)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    result = execute(ssh_arguments(args.host, command), args.receipt, args.deadline)
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(result['exit_code'] if result['exit_code'] >= 0 else 125)
