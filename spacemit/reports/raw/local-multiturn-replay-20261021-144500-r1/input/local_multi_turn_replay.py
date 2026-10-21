#!/usr/bin/env python3
"""在本机逐请求重放六个失败请求，保存回答和 v1 对照结果，交由人工复核质量。"""
import argparse
import http.client
import json
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

import batch_controller as controller
import diagnostic as base
import multi_turn_batch as batch
from multi_turn_suite import stop_server

FAILED_REQUESTS = 6
STREAM_FAILURES = (
    'completion stream ended without the DONE event',
    'completion stream ended without a finish reason',
)


def read_json(path):
    """读取一个外部 JSON 文件。"""
    return json.loads(path.read_text(encoding='utf-8'))


def source_requests(source):
    """从源批次读取失败轮次，保留完整请求和原始规则。"""
    assessment = base.load_module('replay_source_v1', source / 'multi_turn_cases.py')
    cases = read_json(source / 'cases.json')
    if cases != assessment.read_cases():
        raise ValueError('source cases differ from the frozen assessment')
    conversations = {item['conversation_id']: item for item in cases}
    attempts = [item for item in read_json(source / 'batch/summary.json')['attempts']
                if item['status'] == 'failed']
    if len(attempts) != FAILED_REQUESTS:
        raise ValueError('source must contain exactly six failed attempts')
    selected, seen = [], set()
    for item in attempts:
        identifier = item['id']
        if not isinstance(identifier, str) or not controller.ID_PATTERN.fullmatch(identifier) or identifier in seen:
            raise ValueError('source attempt ids must be safe and unique')
        seen.add(identifier)
        result_root = source / 'batch/attempts' / identifier / 'result'
        results = read_json(result_root / 'summary.json')['results']
        if len(results) != 1 or results[0]['status'] != 'failed':
            raise ValueError('source attempt must contain one failed conversation')
        result = results[0]
        conversation = conversations[result['conversation_id']]
        index = result['failure']['turn']
        if type(index) is not int or not 1 <= index <= len(conversation['turns']):
            raise ValueError('source failure turn is invalid')
        turn = conversation['turns'][index - 1]
        request = result_root / 'conversations' / result['conversation_id'] / f'turn-{index}/request.json'
        payload = read_json(request)
        messages = payload.get('messages')
        if not isinstance(messages, list) or not messages or any(
                not isinstance(message, dict) or message.get('role') not in ('system', 'user', 'assistant')
                or not isinstance(message.get('content'), str) for message in messages):
            raise ValueError('source messages are invalid')
        if messages[-1] != {'role': 'user', 'content': turn['user']}:
            raise ValueError('source request differs from the failed turn')
        if payload.get('cache_prompt') is not False or payload.get('stream') is not True \
                or payload.get('id_slot') != 0 \
                or payload.get('chat_template_kwargs', {}).get('enable_thinking') is not False:
            raise ValueError('source request settings differ from the replay protocol')
        cap = payload.get('max_tokens')
        if type(cap) is not int or not 0 < cap < base.CONTEXT:
            raise ValueError('source max_tokens is invalid')
        if not isinstance(payload.get('model'), str) or not payload['model']:
            raise ValueError('source model alias is absent')
        selected.append({'id': identifier, 'model': read_json(result_root / 'protocol.json')['model'],
                         'conversation_id': result['conversation_id'], 'turn_index': index,
                         'rule': turn, 'request': str(request), 'alias': payload['model'],
                         'original_quality': read_json(request.parent / 'quality.json')})
    return selected


def verify_models(directory, manifest, names):
    """对每个所需模型核对一次清单中的 SHA-256。"""
    identities = {}
    for name in sorted(set(names)):
        item = manifest['models'][name]
        filename = item['filename']
        if not isinstance(filename, str) or Path(filename).name != filename:
            raise ValueError('manifest model filename must be a basename')
        path = directory / filename
        digest = base.sha256(path)
        if digest != item['sha256']:
            raise ValueError('model differs from manifest: ' + name)
        identities[name] = {'path': str(path), 'sha256': digest, 'bytes': path.stat().st_size}
    return identities


def local_environment(server):
    """移除继承的模型开关，明确设置本机动态库路径。"""
    env = {key: os.environ[key] for key in ('PATH', 'HOME', 'LANG', 'LC_ALL', 'LC_CTYPE', 'TZ', 'TMPDIR')
           if key in os.environ}
    env.update(LD_LIBRARY_PATH=str(server.parent), K1_PACKAGE_LOCK_FD='9')
    return env


def runtime_identity(server, env):
    """记录本机二进制、实际链接库、构建来源和系统信息。"""
    linked = subprocess.run(['ldd', str(server)], env=env, capture_output=True, text=True, check=True)
    if 'not found' in linked.stdout:
        raise ValueError('server has unresolved shared libraries')
    paths = {Path(value).resolve() for value in re.findall(r'(/[^\s()]+)', linked.stdout)}
    paths.update(path.resolve() for path in server.parent.glob('*.so*') if path.is_file())
    cache = server.parent.parent / 'CMakeCache.txt'
    if cache.is_file():
        build = {'cmake_cache_path': str(cache), 'cmake_cache': cache.read_text()}
    else:
        version = subprocess.run([str(server), '--version'], env=env, capture_output=True,
                                 text=True, check=True, timeout=30)
        build = {'version_stdout': version.stdout, 'version_stderr': version.stderr}
    return {'runtime': 'local-linux-x86-cpu',
            'server': {'path': str(server), 'sha256': base.sha256(server)},
            'dependencies': {str(path): base.sha256(path) for path in sorted(paths)},
            'ldd': linked.stdout, 'build': build, 'uname': list(os.uname()),
            'cpuinfo': Path('/proc/cpuinfo').read_text(), 'meminfo': Path('/proc/meminfo').read_text()}


def server_argv(server, model_path, alias, port):
    """固定 CPU、批次、上下文、KV 和草稿参数，使用模型内置模板。"""
    return [str(server), '-m', model_path, '--alias', alias, '--host', '127.0.0.1',
            '--port', str(port), '--n-gpu-layers', '0', '--threads', '4', '--threads-batch', '4',
            '--batch-size', '32', '--ubatch-size', '32', '--ctx-size', str(base.CONTEXT),
            '--parallel', '1', '--cache-type-k', 'f16', '--cache-type-v', 'f16',
            '--flash-attn', 'on', '--spec-type', 'none']


def prepare(args):
    """在任何模型请求前冻结全部请求、规则、参数和任务。"""
    selected = source_requests(args.source_batch)
    manifest = read_json(args.manifest)
    models = verify_models(args.models, manifest, [item['model'] for item in selected])
    env = local_environment(args.server)
    identity = runtime_identity(args.server, env)
    root = args.output
    root.mkdir(parents=True, exist_ok=False)
    configs = root / 'configs'
    configs.mkdir()
    for source, target in ((args.source_batch / 'multi_turn_cases.py', root / 'assessment_v1.py'),
                           (args.chat, root / 'chat.py')):
        shutil.copyfile(source, target)
    tools = {str(path): base.sha256(path) for path in
             (Path(__file__), Path(controller.__file__), Path(batch.__file__), Path(base.__file__),
              root / 'assessment_v1.py', root / 'chat.py')}
    base.save(root / 'identity.json', {**identity, 'models': models, 'manifest': manifest, 'tools': tools})
    jobs = []
    for item in selected:
        folder = configs / item['id']
        folder.mkdir()
        shutil.copyfile(item['request'], folder / 'request.json')
        attempt = root / 'batch/attempts' / item['id']
        config = {**item, 'source_request': item['request'], 'request': str(folder / 'request.json'),
                  'attempt': str(attempt), 'timeout_s': args.timeout,
                  'assessment': str(root / 'assessment_v1.py'), 'chat': str(root / 'chat.py'),
                  'url': f'http://127.0.0.1:{args.port}', 'environment': env,
                  'argv': server_argv(args.server, models[item['model']]['path'], item['alias'], args.port)}
        path = folder / 'config.json'
        base.save(path, config)
        jobs.append({'id': item['id'], 'argv': [sys.executable, str(Path(__file__).resolve()),
                                              '--worker', str(path)],
                     'timeout_s': args.timeout + base.HEALTH_TIMEOUT_S + batch.CLEANUP_BUDGET_S,
                     'dependency': 'local-server'})
    base.save(root / 'jobs.json', jobs)
    base.save(root / 'protocol.json', {'purpose': 'diagnostic', 'assessment': 'frozen-v1',
                                      'answer_review': 'manual', 'source_batch': str(args.source_batch),
                                      'planned': len(jobs), 'timeout_s': args.timeout, 'retries': 0})
    return jobs


def request_once(chat, config, payload, folder):
    """让词元计数和完整生成共享同一个信号硬期限。"""
    old = signal.signal(signal.SIGALRM, base.deadline_handler)
    try:
        signal.setitimer(signal.ITIMER_REAL, config['timeout_s'])
        count = chat.count_prompt_tokens(config['url'], payload, config['timeout_s'])
        base.save(folder / 'prompt-count.json', {'prompt_tokens': count})
        if count + payload['max_tokens'] > base.CONTEXT:
            raise ValueError('source request exceeds the context')
        response = chat.complete(config['url'], payload, config['timeout_s'], display=False,
                                 stream_path=folder / 'stream.sse')
        return count, response
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)


def recover_partial_answer(folder, error):
    """从原始流恢复可解析的回答前缀，记录异常和恢复中断位置。"""
    stream = folder / 'stream.sse'
    if not stream.exists():
        return
    parts = []
    interruption = None
    with stream.open('rb') as source:
        for number, raw in enumerate(source, 1):
            if not raw.startswith(b'data: '):
                continue
            data = raw[6:].strip()
            if data == b'[DONE]':
                break
            try:
                event = json.loads(data)
                if not isinstance(event, dict) or event.get('error'):
                    raise ValueError('invalid completion event or server error')
                dict(event.get('usage') or {})
                dict(event.get('timings') or {})
                choices = event.get('choices', [])
                if not isinstance(choices, list):
                    raise ValueError('completion choices must be a list')
                fragments = []
                for choice in choices:
                    if not isinstance(choice, dict):
                        raise ValueError('completion choice must be an object')
                    delta = choice.get('delta')
                    if delta is None:
                        continue
                    if not isinstance(delta, dict):
                        raise ValueError('completion delta must be an object')
                    content = delta.get('content')
                    if content is not None and not isinstance(content, str):
                        raise ValueError('completion content must be text')
                    if content:
                        content.encode('utf-8')
                        fragments.append(content)
            except (TypeError, ValueError) as damaged:
                interruption = {'line': number, 'reason': type(damaged).__name__ + ': ' + str(damaged)}
                break
            parts.extend(fragments)
    answer = ''.join(parts)
    (folder / 'answer.partial.txt').write_text(answer, encoding='utf-8')
    base.save(folder / 'partial-answer.json', {
        'complete': False, 'answer': answer, 'answer_chars': len(answer),
        'failure_reason': type(error).__name__ + ': ' + str(error),
        'recovery_interruption': interruption})


def worker(config_path):
    """独立执行一个请求；内部异常传播到批次控制器。"""
    config = read_json(config_path)
    attempt = Path(config['attempt'])
    base.save(attempt / 'process.json', {'pgid': os.getpgrp()})
    signal.signal(signal.SIGTERM, base.term_handler)
    folder = attempt / 'result'
    folder.mkdir()
    shutil.copyfile(config['request'], folder / 'request.json')
    payload = read_json(folder / 'request.json')
    chat = base.load_module('local_replay_chat', Path(config['chat']))
    assessment = base.load_module('local_replay_assessment', Path(config['assessment']))
    base.save(folder / 'launch.json', {'argv': config['argv'], 'environment': config['environment']})
    process = None
    try:
        with (folder / 'server.log').open('w') as log:
            process = subprocess.Popen(config['argv'], env=config['environment'], stdout=log,
                                       stderr=subprocess.STDOUT, pass_fds=(9,))
        base.wait_ready(process, config['url'])
        with urllib.request.urlopen(config['url'] + '/props', timeout=30) as response:
            props = json.load(response)
        base.save(folder / 'props.json', props)
        if props['total_slots'] != 1 or props['default_generation_settings']['n_ctx'] != base.CONTEXT:
            raise ValueError('runtime slot count or context differs')
        try:
            count, response = request_once(chat, config, payload, folder)
        except RuntimeError as error:
            if str(error) not in STREAM_FAILURES:
                raise
            raise urllib.error.URLError(str(error)) from error
        base.save(folder / 'answer.json', response)
        (folder / 'answer.txt').write_text(response['answer'], encoding='utf-8')
        metrics = base.validate_response(response, count, 'direct', max_tokens=payload['max_tokens'])
        metrics['cached_tokens'] = response['usage']['prompt_tokens_details']['cached_tokens']
        quality = assessment.assess(config['rule'], response['answer'])
        base.save(folder / 'quality-v1.json', quality)
        result = {'status': 'passed', 'reason': 'complete_for_manual_review', 'v1_quality': quality,
                  'metrics': metrics, 'wall_s': response['wall_s'], 'ttft_s': response['ttft_s'],
                  'timings': response['timings']}
    except (TimeoutError, urllib.error.URLError, ConnectionError, http.client.IncompleteRead,
            http.client.BadStatusLine, http.client.LineTooLong) as error:
        recover_partial_answer(folder, error)
        result = {'status': 'incomplete', 'reason': type(error).__name__ + ': ' + str(error)}
    except Exception as error:
        recover_partial_answer(folder, error)
        raise
    finally:
        if process is not None:
            stop_server(process)
            base.save(folder / 'exit.json', {'returncode': process.returncode})
    result.update(purpose='diagnostic', quality_gate=None, quality_review='pending',
                  conversation_id=config['conversation_id'], turn=config['turn_index'])
    base.save(folder / 'summary.json', result)
    base.save(attempt / 'outcome.json', {'status': result['status'],
                                       'reason': result['reason']})
    return 0 if result['status'] == 'passed' else 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path)
    for name in ('output', 'source-batch', 'server', 'models', 'manifest', 'chat'):
        parser.add_argument('--' + name, type=Path)
    parser.add_argument('--port', type=int, default=18260)
    parser.add_argument('--timeout', type=int, default=900)
    args = parser.parse_args(argv)
    if args.worker is not None:
        return worker(args.worker)
    for name in ('output', 'source_batch', 'server', 'models', 'manifest', 'chat'):
        path = getattr(args, name)
        if path is None:
            parser.error('--' + name.replace('_', '-') + ' is required')
        setattr(args, name, path.resolve())
    if args.output.exists() or not 0 < args.port < 65536 or args.timeout <= 0:
        parser.error('use a new output directory, a valid port, and a positive timeout')
    if sys.platform != 'linux' or os.uname().machine not in ('x86_64', 'i686'):
        parser.error('use Linux x86')
    with batch.board_lock(str(Path(tempfile.gettempdir()) / 'riscv-accl-local-inference.lock')):
        with socket.socket() as sock:
            if sock.connect_ex(('127.0.0.1', args.port)) == 0:
                raise ValueError('the selected port is occupied')
        jobs = prepare(args)
        before, after = batch.lifecycle_hooks()
        summary = controller.run(jobs, args.output / 'batch', before=before, after=after, pass_fds=(9,))
        status = controller.exit_code(summary)
        base.save(args.output / 'batch_status.json', {'batch_status': status, 'purpose': 'diagnostic',
                                                    'counts': summary['counts'], 'quality_gate': None})
    return status


if __name__ == '__main__':
    sys.exit(main())
