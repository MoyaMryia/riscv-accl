#!/usr/bin/env python3
"""顺序执行冻结的长上下文请求，隔离失败，保留独立人工复核入口。"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import http.client
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from types import SimpleNamespace

import batch_controller as controller
import diagnostic as base
import local_multi_turn_replay as replay
import long_context_cases as cases_module
import multi_turn_batch as batch
import multi_turn_suite as suite


class MemoryViolation(RuntimeError):
    """内存越界时停止当前请求。"""


class ExecutionFailure(RuntimeError):
    """请求证据表明执行不完整。"""


def memory_sample(pid=None):
    """从系统文件读取字节单位的内存快照。"""
    memory = {}
    for line in Path('/proc/meminfo').read_text().splitlines():
        key, value = line.split(':', 1)
        if key in ('MemAvailable', 'MemTotal', 'SwapTotal', 'SwapFree'):
            memory[key] = int(value.split()[0]) * 1024
    row = {key: memory[key] for key in ('MemAvailable', 'MemTotal', 'SwapTotal', 'SwapFree')}
    row['rss_bytes'] = 0
    if pid is not None:
        status = Path(f'/proc/{pid}/status').read_text()
        rss = re.search(r'^VmRSS:\s+(\d+) kB$', status, re.M)
        if rss is None:
            raise ProcessLookupError('服务器状态中缺少 RSS')
        row['rss_bytes'] = int(rss[1]) * 1024
    import time
    row['time_unix_s'] = time.time()
    return row


class MemorySampler:
    """逐秒落盘；线程异常终止服务器，并由主线程重新抛出。"""

    def __init__(self, process, folder, notify, sample=memory_sample):
        self.process = process
        self.folder = folder
        self.notify = notify
        self.sample = sample
        self.stopped = threading.Event()
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.future = None
        self.error = None

    def start(self):
        self.future = self.executor.submit(self.run)

    def run(self):
        try:
            with (self.folder / 'memory.jsonl').open('x', encoding='utf-8') as stream:
                while not self.stopped.is_set():
                    if self.process.poll() is not None:
                        return
                    try:
                        row = self.sample(self.process.pid)
                    except (FileNotFoundError, ProcessLookupError):
                        if self.process.poll() is not None:
                            return
                        raise
                    limits = cases_module.MEMORY_LIMITS
                    row['violation'] = (row['MemAvailable'] < limits['running_available_bytes']
                                        or row['rss_bytes'] > limits['rss_bytes'])
                    stream.write(json.dumps(row, ensure_ascii=False) + '\n')
                    stream.flush()
                    if row['violation']:
                        base.save(self.folder / 'memory-violation.json', row)
                        raise MemoryViolation('运行内存越界')
                    if self.stopped.wait(limits['sample_interval_s']):
                        return
        finally:
            error = sys.exc_info()[1]
            if error is not None:
                self.error = error
                try:
                    base.save(self.folder / 'memory-error.json',
                              {'type': type(error).__name__, 'error': str(error)})
                finally:
                    try:
                        if self.process.poll() is None:
                            self.process.terminate()
                    finally:
                        self.notify()

    def close(self):
        self.stopped.set()
        self.executor.shutdown(wait=True)
        self.future.result()


def prepare_jobs(root, runtime, models, cases):
    """在首个请求前冻结全部配置、零重试协议和任务。"""
    (root / 'configs').mkdir()
    jobs = []
    for model in models:
        for case in cases:
            identifier = model.lower() + '-' + case['case_id']
            attempt = root / 'batch' / 'attempts' / identifier
            config_path = root / 'configs' / (identifier + '.json')
            config = {'runtime': runtime, 'model': model, 'case': case,
                      'attempt': str(attempt), 'root': str(root), 'port': 18088}
            base.save(config_path, config)
            jobs.append({'id': identifier,
                         'argv': [sys.executable, str(root / Path(__file__).name),
                                  '--worker', str(config_path)],
                         'timeout_s': cases_module.LEVELS[case['level']]['deadline_s']
                                      + base.HEALTH_TIMEOUT_S + batch.CLEANUP_BUDGET_S,
                         'dependency': model})
    base.save(root / 'protocol.json', {'jobs': jobs, 'levels': cases_module.LEVELS,
                                      'max_tokens': cases_module.MAX_TOKENS,
                                      'memory_limits': cases_module.MEMORY_LIMITS,
                                      'retries': 0, 'quality_review': 'pending',
                                      'gate_scope': 'execution_only'})
    return jobs


def resource_hooks(root, sample=memory_sample):
    """复用进程组清理；共享启动内存不足时阻止后续依赖项。"""
    previous_before, after = batch.lifecycle_hooks()
    blocked = []

    def before(job):
        cleanup_failure = previous_before(job)
        if cleanup_failure is not None:
            return cleanup_failure
        if not blocked:
            row = sample()
            evidence = root / ('startup-memory-' + job['id'] + '.json')
            base.save(evidence, row)
            if row['MemAvailable'] < cases_module.MEMORY_LIMITS['startup_available_bytes']:
                blocked.append(str(evidence))
        if blocked:
            return {'status': 'blocked', 'reason': 'shared_startup_memory', 'evidence': list(blocked)}
    return before, after


def verify_effective(effective, text, context):
    """按档位核对实际上下文与其余默认配置。"""
    return effective.verify(text, base.CONFIG, context=context)


def request_once(chat, url, case, folder):
    """先保存请求；分词与生成共用档位硬期限。"""
    spec = cases_module.LEVELS[case['level']]
    payload = dict(case['payload_settings'], messages=case['messages'])
    base.save(folder / 'request.json', payload)
    old = signal.signal(signal.SIGALRM, base.deadline_handler)
    try:
        signal.setitimer(signal.ITIMER_REAL, spec['deadline_s'])
        count = chat.count_prompt_tokens(url, payload, spec['deadline_s'])
        base.save(folder / 'prompt-count.json', {'prompt_tokens': count,
                                               'local_token_count': case['local_token_count']})
        try:
            cases_module.check_count(count, case['level'])
        except ValueError as error:
            raise ExecutionFailure(str(error)) from error
        try:
            response = chat.complete(url, payload, spec['deadline_s'], display=False,
                                     stream_path=folder / 'stream.sse')
        except RuntimeError as error:
            if str(error) not in replay.STREAM_FAILURES:
                raise
            raise ExecutionFailure(str(error)) from error
        base.save(folder / 'answer.json', response)
        (folder / 'answer.txt').write_text(response['answer'], encoding='utf-8')
        try:
            metrics = suite.validate_turn(response, count, cases_module.MAX_TOKENS, False)
        except ValueError as error:
            raise ExecutionFailure(str(error)) from error
        base.save(folder / 'metrics.json', dict(metrics, wall_s=response['wall_s'],
                                               ttft_s=response['ttft_s'], timings=response['timings']))
        base.save(folder / 'quality.json', {'passed': None, 'method': 'independent_review_required',
                                           'reference': case['reference']})
        return {'status': 'passed', 'reason': 'complete_for_manual_review'}
    except BaseException as error:
        replay.recover_partial_answer(folder, error)
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)


def execute(config, folder):
    """每个案例启动一个服务器，退出前停止服务器并回收采样线程。"""
    root = Path(config['root'])
    runtime = config['runtime']
    args = SimpleNamespace(**{key: Path(value) for key, value in runtime.items()})
    args.port = config['port']
    for key, filename in (('chat', 'chat.py'), ('quality', 'quality.py'),
                          ('effective', 'effective.py'), ('tool_receipt', 'tools.json')):
        setattr(args, key, root / filename)
    models, identity = base.verify_inputs(args, model_names=(config['model'],), extra_tools={
        'long_context_batch': Path(__file__), 'long_context_cases': Path(cases_module.__file__)})
    base.save(folder / 'identity.json', identity)
    chat = base.load_module('long_context_chat', args.chat)
    effective = base.load_module('long_context_effective', args.effective)
    spec = cases_module.LEVELS[config['case']['level']]
    argv = list(map(str, [args.server, '-m', models[config['model']], '--alias', 'local',
                         '--host', '127.0.0.1', '--port', args.port, '-c', spec['context'],
                         '--log-verbosity', base.LOG_VERBOSITY]))
    libraries = f'{args.server.parent}:{args.tcm}:{args.spert / "lib"}'
    env = base.clean_environment(os.environ, libraries, False, drafting=False)
    base.save(folder / 'launch.json', {'argv': argv, 'environment': env})
    process = None
    sampler = None
    cleanup_started = False

    def interrupt(signum, frame):
        if not cleanup_started:
            raise sampler.error

    old_interrupt = signal.signal(signal.SIGUSR1, interrupt)
    try:
        with (folder / 'server.log').open('x') as log:
            process = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT,
                                       env=env, pass_fds=(9,))
        sampler = MemorySampler(process, folder, notify=lambda: os.kill(os.getpid(), signal.SIGUSR1))
        sampler.start()
        url = f'http://127.0.0.1:{args.port}'
        base.wait_ready(process, url)
        text = (folder / 'server.log').read_text()
        actual = verify_effective(effective, text, spec['context'])
        base.save(folder / 'effective.json', {'defaults': actual,
                                             'speculation': base.verify_speculation(text, 'direct')})
        with urllib.request.urlopen(url + '/props', timeout=30) as response:
            props = json.load(response)
        base.save(folder / 'props.json', props)
        if props['total_slots'] != 1 or props['default_generation_settings']['n_ctx'] != spec['context']:
            raise ExecutionFailure('服务器槽位或上下文不同')
        return request_once(chat, url, config['case'], folder)
    finally:
        cleanup_started = True
        primary = sys.exc_info()[1]
        try:
            try:
                if process is not None:
                    suite.stop_server(process)
                    base.save(folder / 'exit.json', {'returncode': process.returncode})
                    if process.returncode not in (0, -signal.SIGTERM):
                        raise ExecutionFailure('服务器退出状态异常：' + str(process.returncode))
            except BaseException as error:
                base.save(folder / 'server-cleanup-error.json',
                          {'type': type(error).__name__, 'error': str(error)})
                if primary is None:
                    raise
        finally:
            active = sys.exc_info()[1]
            try:
                try:
                    if sampler is not None:
                        sampler.close()
                except BaseException as error:
                    if error is not active:
                        base.save(folder / 'sampler-cleanup-error.json',
                                  {'type': type(error).__name__, 'error': str(error)})
                    if active is None:
                        raise
            finally:
                signal.signal(signal.SIGUSR1, old_interrupt)


def worker(config_path):
    """内部错误向控制器传播；可处理的传输失败保存为非零退出。"""
    config = json.loads(config_path.read_text())
    attempt = Path(config['attempt'])
    base.save(attempt / 'process.json', {'pgid': os.getpgrp()})
    folder = attempt / 'result'
    folder.mkdir()
    signal.signal(signal.SIGTERM, base.term_handler)
    try:
        result = execute(config, folder)
    except (ExecutionFailure, MemoryViolation, TimeoutError, urllib.error.URLError,
            ConnectionError, http.client.IncompleteRead, http.client.BadStatusLine,
            http.client.LineTooLong) as error:
        result = {'status': 'incomplete', 'reason': type(error).__name__ + ': ' + str(error)}
    base.save(attempt / 'outcome.json', result)
    return 0 if result['status'] == 'passed' else 2


def run_batch(root, runtime, models):
    """冻结后持锁执行，根状态明确保留人工质量门禁。"""
    cases = cases_module.read_cases(root / 'cases.json')
    jobs = prepare_jobs(root, runtime, models, cases)
    before, after = resource_hooks(root)
    with batch.board_lock(runtime['lock']):
        summary = controller.run(jobs, root / 'batch', before=before, after=after, pass_fds=(9,))
    base.save(root / 'batch-status.json', dict(summary, quality_acceptance=None,
                                             quality_review='pending', gate_scope='execution_only'))
    return controller.exit_code(summary)


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
        parser.error('必须在 tmux 中提供 --job 与 --runtime')
    if len(set(args.models)) != len(args.models):
        parser.error('模型列表必须唯一')
    runtime = json.loads(args.runtime.read_text())
    if not isinstance(runtime, dict) or set(runtime) != set(batch.RUNTIME_KEYS):
        parser.error('运行配置必须使用 multi_turn_batch.RUNTIME_KEYS')
    for key, value in runtime.items():
        if not isinstance(value, str) or not Path(value).is_absolute():
            parser.error('运行路径必须为绝对路径：' + key)
    return run_batch(args.job.resolve(), runtime, args.models)


if __name__ == '__main__':
    raise SystemExit(main())
