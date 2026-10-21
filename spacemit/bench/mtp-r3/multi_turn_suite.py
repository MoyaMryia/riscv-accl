#!/usr/bin/env python3
"""在固定多轮题集上测量完整回答质量。

每个会话使用独立服务器进程，轮次按顺序发送，历史逐轮累积。
单轮失败只终止该会话，其他会话继续执行。
"""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import urllib.request

import diagnostic as base
import multi_turn_cases as cases_module
from repetition_guard import RepeatGuard

SAVE_KEYS = ('answer', 'ttft_s', 'wall_s', 'finish_reason', 'usage', 'timings', 'server_slot')


class HttpClient:
    """把聊天模块包装成逐轮提问接口。"""

    def __init__(self, chat, url, model, max_tokens, timeout, context,
                 cache_prompt=False, guard_factory=None):
        self.chat = chat
        self.url = url
        self.model = model
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.context = context
        self.cache_prompt = cache_prompt
        self.guard_factory = guard_factory

    def ask(self, messages):
        payload = self.chat.request_body(messages, self.model, 0, self.max_tokens)
        payload.update(cache_prompt=self.cache_prompt,
                       stream_options={'include_usage': True}, verbose=True)
        prompt_count = self.chat.count_prompt_tokens(self.url, payload, self.timeout)
        if prompt_count + self.max_tokens > self.context:
            raise ValueError('turn does not fit in the context window')
        guard = self.guard_factory() if self.guard_factory is not None else None
        response = self.chat.complete(self.url, payload, self.timeout,
                                      display=False, guard=guard)
        return {'payload': payload, 'prompt_count': prompt_count, 'response': response}


def validate_turn(result, prompt_count, max_tokens, cache_prompt):
    """检查一次完整回答，返回词元指标。"""
    if result['finish_reason'] != 'stop':
        raise ValueError('completion did not stop naturally')
    answer = result['answer']
    if not isinstance(answer, str) or not answer.strip() or result.get('reasoning_text') \
            or '<think>' in answer:
        raise ValueError('answer is empty or contains reasoning text')
    usage, timing = result['usage'], result['timings']
    cached = usage['prompt_tokens_details']['cached_tokens']
    if type(cached) is not int or (not cache_prompt and cached != 0):
        raise ValueError('prompt cache reuse differs from the setting')
    prompt_n, completion_n = usage['prompt_tokens'], usage['completion_tokens']
    if type(prompt_n) is not int or prompt_n < 1 or prompt_n != prompt_count \
            or timing.get('prompt_n') != prompt_n:
        raise ValueError('prompt token counts differ or are invalid')
    if type(completion_n) is not int or not 0 < completion_n < max_tokens \
            or timing.get('predicted_n') != completion_n:
        raise ValueError('completion counts differ or the answer reaches the token cap')
    for key in ('prompt_ms', 'predicted_ms'):
        base.finite_positive(timing.get(key), key)
    for key in ('ttft_s', 'wall_s'):
        base.finite_positive(result.get(key), key)
    if result.get('server_slot') != 0:
        raise ValueError('server slot differs')
    return {'prompt_tokens': prompt_n, 'completion_tokens': completion_n,
            'cached_tokens': cached}


def run_conversation(client, conversation, save_turn=None):
    """按顺序执行一个会话，返回逐轮记录与会话状态。"""
    history = [{'role': 'system', 'content': cases_module.SYSTEM}]
    records = []
    status = 'passed'
    failure = None
    for index, turn in enumerate(conversation['turns'], 1):
        messages = history + [{'role': 'user', 'content': turn['user']}]
        try:
            reply = client.ask(messages)
            metrics = validate_turn(reply['response'], reply['prompt_count'],
                                    client.max_tokens, client.cache_prompt)
            quality = cases_module.assess(turn, reply['response']['answer'])
        except (RuntimeError, ValueError, OSError, TimeoutError) as error:
            failure = {'turn': index, 'status': 'incomplete',
                       'error': type(error).__name__ + ': ' + str(error)[:300]}
            status = 'incomplete'
            break
        record = {'turn': index, 'prompt_chars': len(turn['user']),
                  'prompt_tokens': metrics['prompt_tokens'],
                  'completion_tokens': metrics['completion_tokens'],
                  'cached_tokens': metrics['cached_tokens'],
                  'wall_s': reply['response']['wall_s'],
                  'ttft_s': reply['response']['ttft_s'],
                  'quality': quality}
        records.append(record)
        if save_turn is not None:
            save_turn(index, turn, reply, quality)
        history.extend([{'role': 'user', 'content': turn['user']},
                        {'role': 'assistant', 'content': reply['response']['answer']}])
        if not quality['passed']:
            failure = {'turn': index, 'status': 'failed',
                       'failures': quality['failures']}
            status = 'failed'
            break
    checks = [c for record in records for c in record['quality']['checks']]
    return {
        'conversation_id': conversation['conversation_id'],
        'category': conversation['category'],
        'status': status,
        'turns_planned': len(conversation['turns']),
        'turns_completed': len(records),
        'checks_passed': sum(c['matched'] if c['kind'] == 'require' else not c['matched']
                             for c in checks),
        'checks_total': len(checks),
        'failure': failure,
        'records': records,
    }


def summarize(results):
    """汇总会话状态，并给出批次门槛。"""
    counts = {'passed': 0, 'failed': 0, 'incomplete': 0}
    for result in results:
        counts[result['status']] += 1
    return {
        'conversations': {r['conversation_id']: r['status'] for r in results},
        'counts': counts,
        'turns_planned': sum(r['turns_planned'] for r in results),
        'turns_completed': sum(r['turns_completed'] for r in results),
        'checks_passed': sum(r['checks_passed'] for r in results),
        'checks_total': sum(r['checks_total'] for r in results),
        'gate_passed': counts['passed'] == len(results),
    }


def serve(args, models, arm='direct'):
    """启动一个服务器进程，返回 (process, url, folder)。"""
    folder = args.output / 'servers' / f'server-{args.port}'
    folder.mkdir(parents=True)
    log_path = folder / 'server.log'
    libraries = f'{args.server.parent}:{args.tcm}:{args.spert / "lib"}'
    argv = list(map(str, [args.server, '-m', models[args.model], '--alias', 'local',
                          '--host', '127.0.0.1', '--port', args.port,
                          '--log-verbosity', base.LOG_VERBOSITY]))
    env = base.clean_environment(os.environ, libraries, False, arm != 'loaded_off')
    base.save(folder / 'launch.json', {'argv': argv, 'environment': env})
    log = log_path.open('w')
    process = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, env=env)
    try:
        base.wait_ready(process, f'http://127.0.0.1:{args.port}')
    except BaseException:
        log.close()
        process.terminate()
        process.wait()
        raise
    log.close()
    url = f'http://127.0.0.1:{args.port}'
    with urllib.request.urlopen(url + '/props', timeout=30) as response:
        props = json.load(response)
    base.save(folder / 'properties.json', props)
    if props['total_slots'] != 1 or props['default_generation_settings']['n_ctx'] != args.context:
        process.terminate()
        process.wait()
        raise ValueError('runtime slot count or context differs')
    return process, url, folder


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('output', 'server', 'models', 'spert', 'tcm', 'manifest',
                 'build-receipt', 'chat', 'quality', 'effective', 'tool-receipt'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--port', type=int, default=18088)
    parser.add_argument('--model', choices=('2B', '4B'), default='2B')
    parser.add_argument('--max-tokens', type=int, default=1024)
    parser.add_argument('--timeout', type=int, default=900)
    parser.add_argument('--context', type=int, default=12288)
    parser.add_argument('--cache-prompt', action='store_true')
    parser.add_argument('--guard-window', type=int, default=3)
    parser.add_argument('--guard-min-chars', type=int, default=20)
    args = parser.parse_args(argv)
    if not os.environ.get('TMUX') or not 0 < args.port < 65536:
        parser.error('use tmux and a valid port')
    if not 0 < args.max_tokens < args.context:
        parser.error('max tokens must be smaller than the context')
    signal.signal(signal.SIGTERM, base.term_handler)
    args.output.mkdir(parents=True, exist_ok=False)
    models, identities = base.verify_inputs(args, model_names=(args.model,), extra_tools={
        'suite': Path(__file__), 'assessment': Path(cases_module.__file__)})
    base.save(args.output / 'identity.json', identities)
    chat = base.load_module('multi_turn_chat', args.chat)
    cases = cases_module.read_cases()
    base.save(args.output / 'cases.json', cases)
    base.save(args.output / 'protocol.json', {
        'model': args.model, 'conversations': len(cases),
        'turns': cases_module.planned_turns(cases), 'config': base.CONFIG,
        'context': args.context, 'max_tokens': args.max_tokens,
        'timeout_s': args.timeout, 'cache_prompt': args.cache_prompt,
        'repeat_guard': {'window': args.guard_window, 'min_chars': args.guard_min_chars}})
    results, settled, planned = [], 0, len(cases)
    for conversation in cases:
        folder = args.output / 'conversations' / conversation['conversation_id']
        folder.mkdir(parents=True)
        try:
            process, url, server_folder = serve(args, models)
        except (RuntimeError, ValueError, OSError) as error:
            results.append({'conversation_id': conversation['conversation_id'],
                            'category': conversation['category'], 'status': 'incomplete',
                            'turns_planned': len(conversation['turns']), 'turns_completed': 0,
                            'checks_passed': 0, 'checks_total': 0,
                            'failure': {'turn': 0, 'status': 'incomplete',
                                        'error': type(error).__name__ + ': ' + str(error)[:300]},
                            'records': []})
            settled += 1
            base.save(args.output / 'progress.json',
                      {'planned': planned, 'settled': settled,
                       'last': conversation['conversation_id'], 'status': 'incomplete'})
            continue
        client = HttpClient(chat, url, 'local', args.max_tokens, args.timeout, args.context,
                            args.cache_prompt,
                            guard_factory=lambda: RepeatGuard(args.guard_window,
                                                              args.guard_min_chars))
        try:
            def save_turn(index, turn, reply, quality):
                turn_folder = folder / f'turn-{index}'
                turn_folder.mkdir()
                base.save(turn_folder / 'request.json', reply['payload'])
                base.save(turn_folder / 'answer.json',
                          {k: v for k, v in reply['response'].items() if k in SAVE_KEYS})
                (turn_folder / 'answer.txt').write_text(reply['response']['answer'])
                base.save(turn_folder / 'quality.json', quality)

            result = run_conversation(client, conversation, save_turn)
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            base.save(server_folder / 'exit.json', {'returncode': process.returncode})
        results.append(result)
        base.save(folder / 'result.json', result)
        settled += 1
        base.save(args.output / 'progress.json',
                  {'planned': planned, 'settled': settled,
                   'last': conversation['conversation_id'], 'status': result['status']})
    summary = summarize(results)
    summary['results'] = results
    base.save(args.output / 'summary.json', summary)
    print('MULTI_TURN_' + ('PASSED' if summary['gate_passed'] else 'FAILED'),
          json.dumps(summary['counts'], ensure_ascii=False))
    return 0 if summary['gate_passed'] else 2


if __name__ == '__main__':
    sys.exit(main())
