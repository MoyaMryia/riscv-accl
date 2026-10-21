#!/usr/bin/env python3
"""用独立进程执行每个固定多轮会话，保留失败并继续其余会话。"""
import argparse
import fcntl
import json
import os
from pathlib import Path
from contextlib import contextmanager
import signal
import sys
import time

import batch_controller as controller
import diagnostic as base
import multi_turn_cases as cases_module
import multi_turn_suite as suite

RUNTIME_KEYS = ('server', 'models', 'spert', 'tcm', 'manifest', 'build_receipt', 'lock')
CLEANUP_BUDGET_S = 120


def prepare_jobs(root, runtime, models):
    """在执行前保存每个会话的参数与截止时间。"""
    config_root = root / 'configs'
    config_root.mkdir()
    jobs = []
    for model in models:
        for conversation in cases_module.read_cases():
            identifier = model.lower() + '-' + conversation['conversation_id']
            attempt = root / 'batch' / 'attempts' / identifier
            arguments = ['--output', str(attempt / 'result'), '--model', model,
                         '--conversation', conversation['conversation_id'],
                         '--timeout', str(runtime['turn_timeout_s'])]
            for key in RUNTIME_KEYS:
                if key != 'lock':
                    arguments.extend(['--' + key.replace('_', '-'), runtime[key]])
            for key, filename in (('chat', 'chat.py'), ('quality', 'quality.py'),
                                  ('effective', 'effective.py'), ('tool-receipt', 'tools.json')):
                arguments.extend(['--' + key, str(root / filename)])
            config = config_root / (identifier + '.json')
            base.save(config, {'arguments': arguments, 'attempt': str(attempt),
                               'turns_planned': len(conversation['turns']),
                               'lock': runtime['lock']})
            jobs.append({'id': identifier,
                         'argv': [sys.executable, str(root / Path(__file__).name),
                                  '--worker', str(config)],
                         'timeout_s': len(conversation['turns']) * runtime['turn_timeout_s']
                                      + base.HEALTH_TIMEOUT_S + CLEANUP_BUDGET_S,
                         'dependency': model})
    return jobs


def summarize_quality(root, jobs):
    """按模型汇总已保存的逐轮质量，不把未执行或待复核轮次计为正确。"""
    grouped = {}
    for job in jobs:
        model = job['dependency']
        item = grouped.setdefault(model, {'records': [], 'planned': 0})
        config = json.loads((root / 'configs' / (job['id'] + '.json')).read_text())
        item['planned'] += config['turns_planned']
        folder = root / 'batch' / 'attempts' / job['id'] / 'result' / 'conversations'
        for path in sorted(folder.glob('*/turn-*/quality.json')):
            item['records'].append({'quality': json.loads(path.read_text())})
    return {'assessment_version': cases_module.ASSESSMENT_VERSION, 'quality_acceptance': None,
            'models': {model: suite.quality_statistics(item['records'], item['planned'])
                       for model, item in grouped.items()}}


def worker(config_path):
    """持锁执行一个会话。内部错误由外层控制器记录。"""
    config = json.loads(config_path.read_text())
    attempt = Path(config['attempt'])
    base.save(attempt / 'process.json', {'pgid': os.getpgrp()})
    status = suite.main(config['arguments'])
    result = json.loads((attempt / 'result' / 'summary.json').read_text())
    conversation = result['results'][0]
    base.save(attempt / 'outcome.json', {'status': conversation['status'],
                                       'reason': 'conversation_' + conversation['status']})
    return status


@contextmanager
def board_lock(path):
    """在工作进程计时前持锁，清理全部子进程后释放。"""
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT, 0o664)
    if descriptor != 9:
        os.dup2(descriptor, 9)
        os.close(descriptor)
    print('WAIT_LOCK', flush=True)
    try:
        fcntl.flock(9, fcntl.LOCK_EX)
        os.environ['K1_PACKAGE_LOCK_FD'] = '9'
        print('LOCK_ACQUIRED', flush=True)
        yield
    finally:
        os.close(9)


def group_active(group):
    """检查进程组是否仍有未退出的成员。"""
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():
            continue
        try:
            fields = (path / 'stat').read_text().rsplit(')', 1)[1].split()
        except (FileNotFoundError, ProcessLookupError):
            continue
        if int(fields[2]) == group and fields[0] != 'Z':
            return True
    return False


def cleanup(job, folder, status):
    """终止同组子进程，确认退出后才允许下一会话。"""
    record = folder / 'process.json'
    if not record.exists():
        return
    group = json.loads(record.read_text())['pgid']
    if type(group) is not int or group <= 1 or group == os.getpgrp():
        raise ValueError('worker process group is invalid')
    try:
        os.killpg(group, signal.SIGKILL)
    except ProcessLookupError:
        pass
    deadline = time.monotonic() + controller.TERMINATE_GRACE_S
    while group_active(group):
        if time.monotonic() >= deadline:
            base.save(folder / 'cleanup.json', {'pgid': group, 'exited': False})
            return {'status': 'incomplete', 'reason': 'worker_cleanup_timeout'}
        time.sleep(.05)
    base.save(folder / 'cleanup.json', {'pgid': group, 'exited': True})


def lifecycle_hooks():
    """清理超时后保留证据，并阻止依赖同一板端资源的后续任务。"""
    blocked = []

    def before(job):
        if blocked:
            return {'status': 'blocked', 'reason': 'worker_cleanup_timeout',
                    'evidence': list(blocked)}

    def after(job, folder, status):
        failure = cleanup(job, folder, status)
        if failure is not None:
            blocked.append(str(folder / 'cleanup.json'))
        return failure

    return before, after


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path)
    parser.add_argument('--job', type=Path)
    parser.add_argument('--runtime', type=Path)
    parser.add_argument('--models', nargs='+', choices=base.MODELS, default=list(base.MODELS))
    args = parser.parse_args(argv)
    if args.worker is not None:
        return worker(args.worker)
    if args.job is None or args.runtime is None or not os.environ.get('TMUX'):
        parser.error('use tmux and provide --job and --runtime')
    if len(set(args.models)) != len(args.models):
        parser.error('models must be unique')
    runtime = json.loads(args.runtime.read_text())
    for key in RUNTIME_KEYS:
        if not isinstance(runtime.get(key), str) or not Path(runtime[key]).is_absolute():
            parser.error('runtime paths must be absolute: ' + key)
    timeout = runtime.get('turn_timeout_s')
    if type(timeout) is not int or timeout <= 0:
        parser.error('turn_timeout_s must be a positive integer')
    root = args.job.resolve()
    jobs = prepare_jobs(root, runtime, args.models)
    before, after = lifecycle_hooks()
    with board_lock(runtime['lock']):
        summary = controller.run(jobs, root / 'batch', before=before, after=after, pass_fds=(9,))
    base.save(root / 'quality-summary.json', summarize_quality(root, jobs))
    return controller.exit_code(summary)


if __name__ == '__main__':
    sys.exit(main())
