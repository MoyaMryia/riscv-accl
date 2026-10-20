#!/usr/bin/env python3
"""运行彼此独立的请求，并保存每次尝试的结果。"""
import argparse
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
from contextlib import nullcontext

TERMINATE_GRACE_S = 5
STATUSES = ('passed', 'failed', 'incomplete', 'blocked', 'unattempted')
ID_PATTERN = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]*$')


def _save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def _validate_jobs(jobs):
    if not isinstance(jobs, list) or not jobs:
        raise ValueError('jobs must be a non-empty list')
    seen = set()
    for job in jobs:
        if not isinstance(job, dict) or set(job) != {'id', 'argv', 'timeout_s', 'dependency'}:
            raise ValueError('each job must contain id, argv, timeout_s, and dependency')
        if not isinstance(job['id'], str) or not ID_PATTERN.fullmatch(job['id']) or job['id'] in seen:
            raise ValueError('job ids must be safe and unique')
        seen.add(job['id'])
        if not isinstance(job['argv'], list) or not job['argv'] or any(not isinstance(arg, str) for arg in job['argv']):
            raise ValueError('job argv must be a non-empty list of strings')
        timeout = job['timeout_s']
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError('job timeout_s must be finite and positive')
        if not isinstance(job['dependency'], str):
            raise ValueError('job dependency must be a string')


def _counts(statuses):
    counts = {status: 0 for status in STATUSES}
    for item in statuses:
        counts[item['status']] += 1
    return counts


def _outcome(path):
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or data.get('status') not in ('passed', 'failed', 'incomplete'):
        return None
    if 'reason' in data and not isinstance(data['reason'], str):
        return None
    return data


def _worker_status(returncode, outcome):
    if outcome is None:
        return 'failed', 'worker_crash' if returncode < 0 else 'worker_exit' if returncode else 'worker_protocol'
    reported = outcome['status']
    if reported == 'incomplete':
        return 'incomplete', outcome.get('reason', 'worker_incomplete')
    if reported == 'failed':
        return 'failed', outcome.get('reason', 'worker_failed')
    if returncode != 0:
        return 'failed', 'worker_exit'
    return 'passed', outcome.get('reason', 'passed')


def _terminate(process):
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=TERMINATE_GRACE_S)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


def run(jobs, output, *, guard=None, before=None, after=None):
    """按输入顺序运行全部任务，并返回含最终门禁的 summary。"""
    _validate_jobs(jobs)
    root = Path(output)
    root.mkdir(parents=True, exist_ok=False)
    attempts = root / 'attempts'
    attempts.mkdir()
    _save(root / 'plan.json', jobs)
    statuses = []

    def save_progress(last_id):
        settled = len(statuses)
        counts = _counts(statuses)
        counts['unattempted'] = len(jobs) - settled
        _save(root / 'progress.json', {'settled': settled, 'planned': len(jobs),
                                       'counts': counts, 'last_id': last_id})

    save_progress(None)
    for job in jobs:
        folder = attempts / job['id']
        folder.mkdir()
        result = {'id': job['id'], 'status': None, 'reason': None,
                  'attempt': str(folder), 'stdout': str(folder / 'stdout.log'),
                  'stderr': str(folder / 'stderr.log'),
                  'exit_status': str(folder / 'exit-status.json')}
        blocked = before(job) if before is not None else None
        if blocked is not None:
            if not isinstance(blocked, dict) or blocked.get('status') != 'blocked' or not isinstance(blocked.get('reason'), str):
                raise ValueError('before must return None or a blocked result with a reason')
            result.update(status='blocked', reason=blocked['reason'], evidence=blocked.get('evidence'))
            (folder / 'stdout.log').write_text('', encoding='utf-8')
            (folder / 'stderr.log').write_text('', encoding='utf-8')
            _save(folder / 'exit-status.json', {'returncode': None})
        else:
            context = guard(job) if guard is not None else nullcontext()
            with context:
                with (folder / 'stdout.log').open('wb') as stdout, (folder / 'stderr.log').open('wb') as stderr:
                    timed_out = False
                    spawn_failed = False
                    try:
                        process = subprocess.Popen(job['argv'], stdout=stdout, stderr=stderr,
                                                   start_new_session=True)
                    except OSError as error:
                        spawn_failed = True
                        returncode = None
                        stderr.write((type(error).__name__ + ': ' + str(error) + '\n').encode())
                    else:
                        try:
                            returncode = process.wait(timeout=job['timeout_s'])
                        except subprocess.TimeoutExpired:
                            timed_out = True
                            _terminate(process)
                            returncode = process.returncode
                _save(folder / 'exit-status.json', {'returncode': returncode,
                                                    'timed_out': timed_out, 'spawn_failed': spawn_failed})
                if spawn_failed:
                    result.update(status='failed', reason='worker_spawn')
                elif timed_out:
                    result.update(status='incomplete', reason='timeout')
                else:
                    status, reason = _worker_status(returncode, _outcome(folder / 'outcome.json'))
                    result.update(status=status, reason=reason)
                if after is not None:
                    cleanup = after(job, folder, result['status'])
                    if cleanup is not None:
                        if not isinstance(cleanup, dict) or cleanup.get('status') not in ('failed', 'incomplete'):
                            raise ValueError('after must return None or a failure result')
                        result['worker_status'] = {'status': result['status'], 'reason': result['reason']}
                        result.update(status=cleanup['status'], reason=cleanup['reason'])
        _save(folder / 'status.json', result)
        statuses.append(result)
        save_progress(job['id'])
        print(json.dumps({'settled': len(statuses), 'planned': len(jobs), 'id': job['id'],
                          'status': result['status'], 'reason': result['reason']}), flush=True)

    counts = _counts(statuses)
    batch_success = all(item['status'] == 'passed' for item in statuses)
    summary = {'planned': len(jobs), 'settled': len(statuses), 'counts': counts,
               'batch_success': batch_success, 'attempts': statuses}
    _save(root / 'summary.json', summary)
    return summary


def exit_code(summary):
    return 0 if summary['batch_success'] else 2


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    plan = json.loads(Path(args.plan).read_text(encoding='utf-8'))
    jobs = plan['jobs'] if isinstance(plan, dict) else plan
    return exit_code(run(jobs, args.output))


if __name__ == '__main__':
    sys.exit(main())
