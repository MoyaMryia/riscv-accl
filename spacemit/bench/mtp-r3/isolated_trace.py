#!/usr/bin/env python3
"""让独立请求进程共享已有解码后端。"""
import json
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request

import batch_controller
import diagnostic as base
import router_cases
import trace_cases

DRAIN_S = 30
HTTP_S = 5


class BackendStateError(ValueError):
    pass


class BackendBusy(TimeoutError):
    pass


def slots(url):
    with urllib.request.urlopen(url + '/slots', timeout=HTTP_S) as response:
        value = json.load(response)
    if not isinstance(value, list) or len(value) != 1 or type(value[0].get('is_processing')) is not bool:
        raise BackendStateError('backend slot state is invalid')
    return value


def wait_idle(url, deadline_s=DRAIN_S):
    end = time.monotonic() + deadline_s
    while True:
        value = slots(url)
        if not value[0]['is_processing']:
            return value
        if time.monotonic() >= end:
            raise BackendBusy('backend remains active after the worker stopped')
        time.sleep(.1)


def timing_summary(queue, controller):
    indexed = {}
    for item, attempt in zip(queue, controller['attempts']):
        stage, repeat, case, arm = item
        folder = Path(attempt['attempt'])
        outcome_path = folder / 'outcome.json'
        record_path = folder / 'result.json'
        if attempt['reason'] not in ('complete', 'quality', 'quality_review_pending'):
            continue
        if not outcome_path.exists() or not record_path.exists():
            continue
        outcome = json.loads(outcome_path.read_text())
        if outcome.get('reason') not in ('complete', 'quality', 'quality_review_pending'):
            continue
        row = json.loads(record_path.read_text())
        indexed.setdefault((case['case_id'], repeat), {})[arm] = row
    paired = [arms for arms in indexed.values() if set(arms) == set(trace_cases.ARMS)]
    records = [arms[arm] for arms in paired for arm in trace_cases.ARMS]
    planned_pairs = len(queue) // len(trace_cases.ARMS)
    return {'complete_triplets': len(paired), 'excluded_triplets': planned_pairs - len(paired),
            'quality_review_pending': sum(r['quality']['passed'] is None for r in records),
            'adoption_gate': False if not controller['batch_success'] else None,
            'observations': trace_cases.summarize(records)}


def batch_status(controller):
    """返回可保存的批次结论；退出码由控制器定义。"""
    return {'exit_code': batch_controller.exit_code(controller),
            'batch_success': controller['batch_success'], 'planned': controller['planned'],
            'counts': controller['counts']}


def backend_hooks(args, processes, urls):
    """返回批次钩子。守卫共用逐请求锁；after 记录每个臂的停止原因。"""
    blocked = {}

    def guard(job):
        return args.lease.acquire(args.request_lock)

    def before(job):
        arm = job['dependency']
        if processes[arm].poll() is not None:
            return {'status': 'blocked', 'reason': 'backend_exited', 'evidence': {'pid': processes[arm].pid}}
        return blocked.get(arm)

    def after(job, folder, status):
        arm = job['dependency']
        try:
            value = wait_idle(urls[arm])
        except BackendBusy as error:
            base.save(folder / 'backend-busy.json', {'url': urls[arm], 'reason': str(error)})
            blocked[arm] = {'status': 'blocked', 'reason': 'backend_busy',
                            'evidence': str(folder / 'backend-busy.json')}
            return {'status': 'failed', 'reason': 'backend_busy'}
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, BackendStateError) as error:
            if isinstance(error, urllib.error.HTTPError):
                error.close()
            base.save(folder / 'backend-unavailable.json',
                      {'url': urls[arm], 'type': type(error).__name__, 'reason': str(error)})
            blocked[arm] = {'status': 'blocked', 'reason': 'backend_unavailable',
                            'evidence': str(folder / 'backend-unavailable.json')}
            return {'status': 'failed', 'reason': 'backend_unavailable'}
        base.save(folder / 'backend-idle.json', value)
        return None

    return guard, before, after


def run(args, cases, processes, urls, *, backend_root):
    legacy = {'case_id': 'legacy_unicode_runs', 'category': 'code', 'code_task': 'unicode_runs',
              'messages': args.legacy_data['messages'], 'required_facts': [], 'required_citations': []}
    queue = trace_cases.schedule(args.trace_plan, cases, legacy)
    inputs = args.output / 'job-inputs'
    inputs.mkdir()
    controller_root = args.output / 'batch'
    jobs = []
    for index, (stage, repeat, case, arm) in enumerate(queue):
        name = f'{index + 1:04d}-{case["case_id"]}-{arm}-r{repeat}'
        folder = controller_root / 'attempts' / name
        config = {'case': case, 'category': stage, 'round': repeat, 'arm': arm,
            'legacy': case is legacy, 'pid': processes[arm].pid, 'url': urls[arm],
            'log_path': str(backend_root / arm / 'server.log'), 'folder': str(folder),
            'max_tokens': args.max_tokens, 'prefix_rows': args.trace_plan['prefix_rows'],
            'chat': str(args.chat), 'assessment': str(args.cases_module), 'quality': str(args.quality)}
        path = inputs / (name + '.json')
        base.save(path, config)
        jobs.append({'id': name, 'argv': [sys.executable, '-u', str(Path(__file__).with_name('attempt_worker.py')),
            '--config', str(path)], 'dependency': arm,
            'timeout_s': 2 * base.DEADLINE_S + trace_cases.LOG_DRAIN_S
                         + trace_cases.TOKENIZE_S + router_cases.CHILD_TIMEOUT + DRAIN_S})
    base.save(args.output / 'batch-plan.json', {'jobs': jobs, 'retry_count': 0,
        'output_tokens': args.max_tokens, 'drain_deadline_s': DRAIN_S, 'worker_process_group': True})
    guard, before, after = backend_hooks(args, processes, urls)
    controller = batch_controller.run(jobs, controller_root, guard=guard, before=before, after=after)
    base.save(args.output / 'timing-summary.json', timing_summary(queue, controller))
    return controller
