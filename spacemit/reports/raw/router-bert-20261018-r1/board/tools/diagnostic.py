#!/usr/bin/env python3
"""测量 r3 直接解码、纯 MTP、禁用草稿和低接受率回退的完整回答。"""
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import signal
import socket
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request

SERVER_SHA = 'f254f174919c0a97ef34366f116705f6d22574cab4c2bfc39928c0d315b5bfbd'
SPERT_SHA = '0db8febc30aa49d6915c174a8f65b076dbbc7f61a4a3a6e18319eb0aa289b7fe'
TCM_SHA = 'cafb7ae99e0490e3df2f5b29c44c41e87dc07413a85bf19e7f4e68c0e99c4e2b'
CONFIG = {'threads': 4, 'ubatch': 32, 'mask': 3}
CONTEXT = 12288
MODELS = ('2B', '4B')
ARMS = ('direct', 'mtp', 'loaded_off', 'mtp_lowacc')
REPEATS = 3
DEADLINE_S = 1800
HEALTH_TIMEOUT_S = 240
MAX_TOKENS = 2048
CODE_CHECKS = 106
DRAFT_MAX = 3
LOG_VERBOSITY = 4


def deadline_handler(signum, frame):
    raise TimeoutError('request deadline expired')


def term_handler(signum, frame):
    raise RuntimeError('received SIGTERM')


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def clean_environment(source, library_path, lowacc, drafting=True, trace=False):
    env = {k: source[k] for k in ('PATH', 'HOME', 'LANG', 'LC_ALL', 'LC_CTYPE', 'TZ', 'TMPDIR')
           if k in source}
    env.update(LD_LIBRARY_PATH=str(library_path), SPINE_SPEC_RS='0',
               SPINE_SPEC_LOWACC='1' if lowacc else '0',
               SPINE_SPEC_MAX_ACTIVE='1' if drafting else '0')
    if trace:
        env['LLAMA_TRACE'] = '1'
    return env


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def verify_inputs(args, model_names=MODELS, extra_tools=None):
    os.fstat(9)
    if os.environ.get('K1_PACKAGE_LOCK_FD') != '9':
        raise RuntimeError('K1_PACKAGE_LOCK_FD must equal 9')
    active = subprocess.run(['pgrep', '-x', 'llama-server'], capture_output=True)
    if active.returncode == 0:
        raise RuntimeError('another llama-server is active')
    if active.returncode != 1:
        raise RuntimeError('pgrep failed')
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1', args.port)) == 0:
            raise RuntimeError('the selected port is occupied')
    tool_paths = {'diagnostic': Path(__file__), 'chat': args.chat,
                  'quality': args.quality, 'effective': args.effective}
    tool_paths.update(extra_tools or {})
    tools = {name: {'path': str(path), 'sha256': sha256(path)} for name, path in tool_paths.items()}
    if {name: item['sha256'] for name, item in tools.items()} != json.loads(args.tool_receipt.read_text()):
        raise ValueError('tool hashes differ from the local tool receipt')
    server_sha = sha256(args.server)
    if server_sha != SERVER_SHA:
        raise ValueError('server differs from r3')
    manifest = json.loads(args.manifest.read_text())
    models, identities = {}, {}
    for name in model_names:
        item = manifest['models'][name]
        path = args.models / item['filename']
        digest = sha256(path)
        if digest != item['sha256']:
            raise ValueError('model differs from manifest: ' + name)
        models[name] = path
        identities[name] = {'path': str(path), 'sha256': digest, 'bytes': path.stat().st_size}
    receipt = json.loads(args.build_receipt.read_text())
    if receipt['binaries']['llama-server'] != server_sha:
        raise ValueError('build receipt identifies another server')
    dependencies = {}
    for path, expected in ((args.spert / 'lib/libspert.so', SPERT_SHA),
                           (args.tcm / 'libspine_tcm.so', TCM_SHA)):
        if expected not in receipt['dependencies'].values() or sha256(path) != expected:
            raise ValueError('runtime dependency differs: ' + str(path))
        dependencies[str(path.resolve())] = expected
    return models, {'server': {'path': str(args.server), 'sha256': server_sha},
                    'models': identities, 'dependencies': dependencies,
                    'build_receipt': receipt,
                    'tools': tools,
                    'hardware': {'uname': list(os.uname()),
                                 'cpuinfo': Path('/proc/cpuinfo').read_text(),
                                 'meminfo': Path('/proc/meminfo').read_text(), 'uid': os.getuid()}}


def finite_positive(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError(field + ' must be finite and positive')


def validate_response(result, prompt_count, arm, *, max_tokens=MAX_TOKENS):
    if result['finish_reason'] != 'stop':
        raise ValueError('completion did not stop naturally')
    answer = result['answer']
    if not isinstance(answer, str) or not answer.strip() or result.get('reasoning_text') or '<think>' in answer:
        raise ValueError('answer is empty or contains reasoning text')
    usage, timing = result['usage'], result['timings']
    if usage['prompt_tokens_details']['cached_tokens'] != 0:
        raise ValueError('prompt cache reuse is not zero')
    prompt_n, completion_n = usage['prompt_tokens'], usage['completion_tokens']
    if type(prompt_n) is not int or prompt_n < 1 or prompt_n != prompt_count or timing.get('prompt_n') != prompt_n:
        raise ValueError('prompt token counts differ or are invalid')
    if type(completion_n) is not int or not 0 < completion_n < max_tokens or timing.get('predicted_n') != completion_n:
        raise ValueError('completion counts differ or the answer reaches the token cap')
    for key in ('prompt_ms', 'predicted_ms'):
        finite_positive(timing.get(key), key)
    for key in ('ttft_s', 'wall_s'):
        finite_positive(result.get(key), key)
    if result.get('server_slot') != 0:
        raise ValueError('server slot differs')
    generated, accepted = timing.get('draft_n', 0), timing.get('draft_n_accepted', 0)
    if type(generated) is not int or type(accepted) is not int or not 0 <= accepted <= generated:
        raise ValueError('draft counts are invalid')
    if arm in ('direct', 'loaded_off') and generated != 0:
        raise ValueError('zero-draft arm reports drafts')
    if arm in ('mtp', 'mtp_lowacc') and generated == 0:
        raise ValueError('MTP arm reports no drafts')
    return {'prompt_tokens': prompt_n, 'completion_tokens': completion_n,
            'draft_n': generated, 'draft_n_accepted': accepted}


def summarize(records):
    summary = {'models': {}, 'quality_gate': all(r['quality']['passed'] for r in records)}
    for model in MODELS:
        rows = [r for r in records if r['model'] == model]
        if len({r['metrics']['prompt_tokens'] for r in rows}) != 1:
            raise ValueError('paired input token counts differ: ' + model)
        arms = {}
        for arm in ARMS:
            selected = [r for r in rows if r['arm'] == arm]
            response = [r['response'] for r in selected]
            metrics = [r['metrics'] for r in selected]
            generated = sum(r['draft_n'] for r in metrics)
            accepted = sum(r['draft_n_accepted'] for r in metrics)
            arms[arm] = {
                'repeats': len(selected),
                'wall_mean_s': statistics.mean(r['wall_s'] for r in response),
                'wall_median_s': statistics.median(r['wall_s'] for r in response),
                'ttft_mean_s': statistics.mean(r['ttft_s'] for r in response),
                'prefill_ms_mean': statistics.mean(r['timings']['prompt_ms'] for r in response),
                'decode_ms_mean': statistics.mean(r['timings']['predicted_ms'] for r in response),
                'prompt_tokens': [r['prompt_tokens'] for r in metrics],
                'completion_tokens': [r['completion_tokens'] for r in metrics],
                'draft_n': generated, 'draft_accepted': accepted,
                'draft_acceptance': accepted / generated if generated else None,
                'quality_checks': [r['quality'] for r in selected],
            }
        direct = {r['round']: r for r in rows if r['arm'] == 'direct'}
        for arm in ARMS[1:]:
            paired = [100 * (1 - r['response']['wall_s'] / direct[r['round']]['response']['wall_s'])
                      for r in rows if r['arm'] == arm]
            arms[arm]['wall_reduction_vs_direct_pct'] = statistics.mean(paired)
        arms['loaded_off']['overhead_vs_direct_pct'] = -arms['loaded_off']['wall_reduction_vs_direct_pct']
        summary['models'][model] = arms
    return summary


def resource_snapshot(pid):
    status = Path(f'/proc/{pid}/status').read_text()
    memory = Path('/proc/meminfo').read_text()
    hwm = int(re.search(r'^VmHWM:\s+(\d+) kB$', status, re.M)[1])
    available = int(re.search(r'^MemAvailable:\s+(\d+) kB$', memory, re.M)[1])
    return {'server_vm_hwm_kib': hwm, 'memavailable_kib': available}


def wait_ready(process, url):
    end = time.monotonic() + HEALTH_TIMEOUT_S
    while time.monotonic() < end:
        if process.poll() is not None:
            raise RuntimeError('server exited before health became ready')
        try:
            with urllib.request.urlopen(url + '/health', timeout=2) as response:
                if response.status == 200:
                    return
        except urllib.error.HTTPError as error:
            if error.code != 503:
                raise
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(.5)
    raise TimeoutError('server health deadline expired')


def verify_speculation(text, arm):
    snapshots = list(map(int, re.findall(r'\bn_rs_seq\s*=\s*(\d+)', text)))
    outputs = list(map(int, re.findall(r'\bn_outputs_max\s*=\s*(\d+)', text)))
    if not snapshots:
        raise ValueError('RS snapshot records are absent; use diagnostic log verbosity')
    if any(snapshots):
        raise ValueError('RS snapshot configuration differs')
    target_log, draft_log = text.split('K1_EFFECTIVE_DEFAULTS', 1)
    target_outputs = list(map(int, re.findall(r'\bn_outputs_max\s*=\s*(\d+)', target_log)))
    draft_outputs = list(map(int, re.findall(r'\bn_outputs_max\s*=\s*(\d+)', draft_log)))
    cache_pattern = r'llama_kv_cache:\s+size\s*=.*?\(\s*\d+ cells,\s*(\d+) layers'
    cache_layers = list(map(int, re.findall(cache_pattern, text)))
    draft_cache_layers = list(map(int, re.findall(cache_pattern, draft_log)))
    if arm != 'direct' and (len(snapshots) < 2 or 1 not in draft_cache_layers or not draft_outputs):
        raise ValueError('single-layer MTP cache initialization is absent')
    if arm == 'direct' and 1 in cache_layers:
        raise ValueError('direct arm has an MTP cache')
    expected = 1 if arm == 'direct' else DRAFT_MAX + 1
    if not target_outputs or target_outputs[-1] != expected or any(n != 1 for n in draft_outputs):
        raise ValueError('target or draft output capacity differs')
    return {'context_records': len(snapshots), 'rs_values': snapshots,
            'output_capacities': outputs, 'kv_cache_layers': cache_layers,
            'target_output_capacity': target_outputs[-1], 'draft_output_capacities': draft_outputs}


def run_one(args, libs, chat, effective, quality, model, arm, round_no, request_data, model_path, output,
            *, assess=None, trace=False):
    folder = output / model / arm / f'round-{round_no}'
    folder.mkdir(parents=True)
    log_path = folder / 'server.log'
    extra = []
    if arm != 'direct':
        extra = ['--spec-type', 'draft-mtp', '--spec-draft-n-max', str(DRAFT_MAX),
                 '--spec-draft-p-min', '0.0']
    argv = list(map(str, [args.server, '-m', model_path, '--alias', 'local',
                         '--host', '127.0.0.1', '--port', args.port,
                         '--log-verbosity', LOG_VERBOSITY, *extra]))
    env = clean_environment(os.environ, libs, arm == 'mtp_lowacc', arm != 'loaded_off', trace)
    save(folder / 'launch.json', {'argv': argv, 'environment': env})
    url = f'http://127.0.0.1:{args.port}'
    started = time.monotonic()
    process = None
    with log_path.open('w') as log:
        try:
            process = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, env=env)
            wait_ready(process, url)
            startup_s = time.monotonic() - started
            startup_log = log_path.read_text()
            actual = effective.verify(startup_log, CONFIG)
            speculation = verify_speculation(startup_log, arm)
            observed_env = dict(part.split('=', 1) for part in
                                Path(f'/proc/{process.pid}/environ').read_text().split('\0') if part)
            if any(observed_env.get(k) != v for k, v in env.items()):
                raise ValueError('server environment differs from launch record')
            with urllib.request.urlopen(url + '/props', timeout=30) as response:
                props = json.load(response)
            save(folder / 'properties.json', {'effective_defaults': actual, 'properties': props,
                                              'speculation': speculation})
            if props['total_slots'] != 1 or props['default_generation_settings']['n_ctx'] != CONTEXT:
                raise ValueError('runtime slot count or context differs')
            payload = chat.request_body(request_data['messages'], 'local', 0, MAX_TOKENS)
            payload.update(cache_prompt=False, stream_options={'include_usage': True}, verbose=True)
            save(folder / 'request.json', payload)
            before = resource_snapshot(process.pid)
            old_handler = signal.signal(signal.SIGALRM, deadline_handler)
            signal.alarm(DEADLINE_S)
            try:
                prompt_count = chat.count_prompt_tokens(url, payload, DEADLINE_S)
                if prompt_count + MAX_TOKENS > CONTEXT:
                    raise ValueError('complete input and output do not fit')
                response = chat.complete(url, payload, DEADLINE_S, display=False)
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            save(folder / 'answer.json', response)
            (folder / 'answer.txt').write_text(response['answer'])
            metrics = validate_response(response, prompt_count, arm)
            if assess is None:
                code = quality.check_code('unicode_runs', response['answer'])
                if code.get('pass') is True and code.get('checks') != CODE_CHECKS:
                    raise ValueError('functional check coverage differs')
                code_result = {'passed': code.get('pass') is True, 'result': code}
                save(folder / 'code-test.json', code_result)
            else:
                code_result = assess(response['answer'])
                save(folder / 'quality.json', code_result)
            record = {'model': model, 'arm': arm, 'round': round_no,
                      'startup_s': startup_s, 'resources_before_request': before,
                      'resources_after_request': resource_snapshot(process.pid),
                      'response': response, 'metrics': metrics, 'quality': code_result}
        finally:
            if process is not None:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                save(folder / 'server-exit.json', {'returncode': process.returncode})
    if process.returncode != 0:
        raise RuntimeError('server exited with code ' + str(process.returncode))
    record['fallback_events'] = re.findall(r'disable speculation after \d+ accepted in \d+ verification steps',
                                            log_path.read_text())
    save(folder / 'result.json', record)
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('output', 'server', 'models', 'spert', 'tcm', 'manifest', 'request', 'build-receipt',
                 'chat', 'quality', 'effective', 'tool-receipt'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--port', type=int, default=18086)
    args = parser.parse_args(argv)
    if not os.environ.get('TMUX') or not 0 < args.port < 65536:
        parser.error('use tmux and a valid port')
    signal.signal(signal.SIGTERM, term_handler)
    args.output.mkdir(parents=True, exist_ok=False)
    models, identities = verify_inputs(args)
    save(args.output / 'identity.json', identities)
    chat = load_module('mtp_r3_chat', args.chat)
    quality = load_module('mtp_r3_quality', args.quality)
    effective = load_module('mtp_r3_effective', args.effective)
    source_request = json.loads(args.request.read_text())
    source_request = source_request.get('request', source_request)
    messages = source_request['messages']
    save(args.output / 'protocol.json', {'config': CONFIG, 'context': CONTEXT, 'repeats': REPEATS,
         'arms': list(ARMS), 'models': list(MODELS), 'request_deadline_s': DEADLINE_S,
         'max_tokens': MAX_TOKENS, 'case': 'unicode_runs', 'messages': messages,
         'memory_measurement': 'VmHWM includes process load and request', 'rs_snapshots': 0,
         'log_verbosity': LOG_VERBOSITY})
    libs = f'{args.server.parent}:{args.tcm}:{args.spert / "lib"}'
    records = []
    planned = len(MODELS) * len(ARMS) * REPEATS
    for model in MODELS:
        for round_no in range(1, REPEATS + 1):
            order = list(ARMS) if model == '2B' else list(reversed(ARMS))
            offset = (round_no - 1) % len(order)
            for arm in order[offset:] + order[:offset]:
                print(model, arm, round_no, flush=True)
                record = run_one(args, libs, chat, effective, quality, model, arm, round_no,
                                 {'messages': messages}, models[model], args.output)
                records.append(record)
                save(args.output / 'progress.json', {'completed': len(records), 'planned': planned,
                                                    'last': [model, arm, round_no]})
    summary = summarize(records)
    summary['records'] = records
    save(args.output / 'summary.json', summary)
    return 0 if summary['quality_gate'] else 2


if __name__ == '__main__':
    sys.exit(main())
