#!/usr/bin/env python3
"""Measure first-token latency, decode stability, and memory on llama-server.

Run this on the target machine. Each invocation starts one server configuration.
JSONL records contain the full configuration and one record per request.
"""

import argparse
import concurrent.futures
import hashlib
import json
import os
import socket
import statistics
import subprocess
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path


def percentile(values, q):
    if not values:
        return None
    ordered = sorted(values)
    return ordered[round((len(ordered) - 1) * q)]


def stats(values):
    if not values:
        return {}
    return {
        'min': min(values), 'p50': percentile(values, .5),
        'p95': percentile(values, .95), 'p99': percentile(values, .99),
        'max': max(values), 'stdev': statistics.pstdev(values),
    }


def post_json(url, payload, timeout=120):
    request = urllib.request.Request(url, json.dumps(payload).encode(), {'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def wait_healthy(proc, url, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f'server exited with status {proc.returncode}')
        try:
            with urllib.request.urlopen(url + '/health', timeout=2) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(.5)
    raise TimeoutError('server did not become healthy')


def tokenize(url, text):
    result = post_json(url + '/tokenize', {'content': text, 'add_special': True})
    tokens = result['tokens']
    if not tokens or not all(isinstance(token, int) for token in tokens):
        raise RuntimeError('tokenize returned no integer tokens')
    return tokens


def make_prompt(url, length, prompt_text=None):
    if prompt_text is not None:
        tokens = tokenize(url, prompt_text)
        if len(tokens) < length:
            raise ValueError(f'prompt file has {len(tokens)} tokens, need {length}')
        return tokens[:length]
    seed = tokenize(url, 'The RISC-V vector extension processes multiple data elements per instruction. ' * 32)
    body = seed[1:] if len(seed) > 1 else seed
    return seed[:1] + (body * ((length + len(body) - 2) // len(body)))[:length - 1]


def process_status_kib(pid, field):
    try:
        for line in Path(f'/proc/{pid}/status').read_text().splitlines():
            if line.startswith(field + ':'):
                return int(line.split()[1])
    except (FileNotFoundError, ProcessLookupError):
        pass
    return None


def vmrss_kib(pid):
    return process_status_kib(pid, 'VmRSS')


def vmsize_kib(pid):
    return process_status_kib(pid, 'VmSize')


def mem_available_kib():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):
            return int(line.split()[1])
    return None


def sample_rss(pid, stop, values, interval):
    while not stop.is_set():
        value = vmrss_kib(pid)
        if value is not None:
            values.append((time.monotonic(), value, mem_available_kib()))
        stop.wait(interval)


def complete(url, prompt, n_predict, timeout, slot, ignore_eos, cache_prompt, pin_slot=False, capture_token_ids=False):
    payload = {
        'prompt': prompt, 'n_predict': n_predict, 'temperature': 0,
        'seed': 42, 'cache_prompt': cache_prompt, 'stream': True, 'ignore_eos': ignore_eos,
        'return_tokens': True,
    }
    if pin_slot:
        payload['id_slot'] = slot
    request = urllib.request.Request(url + '/completion', json.dumps(payload).encode(),
                                     {'Content-Type': 'application/json'})
    start = time.monotonic()
    first = None
    arrivals = []
    event_tokens = []
    token_ids = []
    parts = []
    final = None
    with urllib.request.urlopen(request, timeout=timeout) as response:
        for raw in response:
            if not raw.startswith(b'data: '):
                continue
            event = raw[6:].strip()
            if event == b'[DONE]':
                continue
            item = json.loads(event)
            now = time.monotonic()
            if item.get('stop'):
                final = item
                break
            if item.get('tokens') or item.get('content'):
                if first is None:
                    first = now
                arrivals.append(now)
                ids = item.get('tokens')
                event_tokens.append(len(ids) if isinstance(ids, list) and ids else 1)
                if isinstance(ids, list):
                    token_ids.extend(ids)
                parts.append(item.get('content', ''))
    end = time.monotonic()
    if final is None:
        raise RuntimeError('completion stream ended without final event')
    if pin_slot and final.get('id_slot') != slot:
        raise RuntimeError(f'requested slot {slot}, server returned {final.get("id_slot")}')
    gaps = [round((b - a) * 1000, 3) for a, b in zip(arrivals, arrivals[1:])]
    half = len(gaps) // 2
    first_half_tps = 1000 * sum(event_tokens[1:half + 1]) / sum(gaps[:half]) if half and sum(gaps[:half]) else None
    second_half_tps = 1000 * sum(event_tokens[half + 1:]) / sum(gaps[half:]) if gaps[half:] and sum(gaps[half:]) else None
    timings = final.get('timings', {})
    record = {
        'slot': slot, 'server_slot': final.get('id_slot'),
        'requested_slot': slot if pin_slot else None, 'wall_s': round(end - start, 4),
        'ttft_ms': round((first - start) * 1000, 3) if first is not None else None,
        'stream_events': len(arrivals), 'streamed_tokens': sum(event_tokens), 'gap_ms': stats(gaps),
        'first_half_tps': first_half_tps, 'second_half_tps': second_half_tps,
        'first_at': first, 'finished_at': end,
        'gaps_over_1s': sum(g > 1000 for g in gaps),
        'tokens_predicted': final.get('tokens_predicted'),
        'stop_type': final.get('stop_type'), 'timings': timings,
        'sha256': hashlib.sha256(''.join(parts).encode()).hexdigest(),
        'tokens_sha256': hashlib.sha256(json.dumps(token_ids, separators=(',', ':')).encode()).hexdigest() if token_ids else None,
        'error': final.get('error'),
    }
    if capture_token_ids:
        record['token_ids'] = token_ids
    if n_predict >= 512 and first is not None:
        record['event_trace'] = [[round((stamp - first) * 1000, 3), count]
                                 for stamp, count in zip(arrivals, event_tokens)]
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server', type=Path, required=True)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--contexts', type=int, nargs='+', default=[128])
    parser.add_argument('--slot-contexts', type=int, nargs='+', help='one prompt length per concurrent slot')
    parser.add_argument('--rotate-slot-contexts', action='store_true',
                        help='rotate the slot prompt lengths on successive repeats in one server process')
    parser.add_argument('--prompt-file', type=Path, help='tokenize this fixed UTF-8 text and take the first requested tokens')
    parser.add_argument('--capture-token-ids', action='store_true', help='save all streamed token IDs for correctness diagnosis')
    parser.add_argument('--n-predict', type=int, default=128)
    parser.add_argument('--repeats', type=int, default=1)
    parser.add_argument('--concurrency', type=int, default=1)
    parser.add_argument('--parallel', type=int, default=1)
    parser.add_argument('--ctx-size', type=int, default=8192)
    parser.add_argument('--threads', type=int, default=4)
    parser.add_argument('--server-log-verbosity', type=int, help='pass -lv to llama-server for diagnostic logging')
    parser.add_argument('--gpu-layers', type=int, help='explicit count of model layers to offload; omitted uses server default')
    parser.add_argument('--batch-size', type=int, default=32)
    parser.add_argument('--ubatch-size', type=int, default=32)
    parser.add_argument('--mode', choices=['plain', 'mtp'], default='plain')
    parser.add_argument('--spec-draft-n-max', type=int, default=3, help='maximum MTP draft tokens per verification step')
    parser.add_argument('--ignore-eos', action='store_true')
    parser.add_argument('--cache-prompt', action='store_true')
    parser.add_argument('--kv-unified', action='store_true')
    parser.add_argument('--cache-type-k', default='f16')
    parser.add_argument('--cache-type-v', default='f16')
    parser.add_argument('--port', type=int, default=18085)
    parser.add_argument('--timeout', type=int, default=7200)
    parser.add_argument('--sample-interval', type=float, default=.2)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--log', type=Path, required=True)
    args = parser.parse_args()
    if min(args.contexts) < 1 or args.n_predict < 1 or args.repeats < 1 or args.threads < 1:
        parser.error('contexts, n-predict, repeats, and threads must be positive')
    if args.server_log_verbosity is not None and args.server_log_verbosity < 0:
        parser.error('--server-log-verbosity must be nonnegative')
    if args.spec_draft_n_max < 1:
        parser.error('--spec-draft-n-max must be positive')
    if args.gpu_layers is not None and args.gpu_layers < 0:
        parser.error('--gpu-layers must be nonnegative')
    if args.concurrency < 1 or args.parallel < args.concurrency:
        parser.error('parallel must be at least concurrency')
    if not 1 <= args.ubatch_size <= args.batch_size:
        parser.error('require 1 <= ubatch-size <= batch-size')
    if args.slot_contexts and (len(args.slot_contexts) != args.concurrency or min(args.slot_contexts) < 1):
        parser.error('--slot-contexts requires one positive length per concurrent slot')
    if args.rotate_slot_contexts and not args.slot_contexts:
        parser.error('--rotate-slot-contexts requires --slot-contexts')
    max_prompt = max(args.slot_contexts) if args.slot_contexts else max(args.contexts)
    if max_prompt + args.n_predict > args.ctx_size // args.parallel:
        parser.error('context plus generation must fit the context per slot')
    if not args.server.is_file() or not args.model.is_file():
        parser.error('server and model must exist')
    if args.prompt_file and not args.prompt_file.is_file():
        parser.error('prompt file must exist')
    prompt_text = args.prompt_file.read_text(encoding='utf-8') if args.prompt_file else None
    with socket.socket() as probe:
        if probe.connect_ex(('127.0.0.1', args.port)) == 0:
            parser.error(f'port {args.port} is already in use')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.log.parent.mkdir(parents=True, exist_ok=True)
    url = f'http://127.0.0.1:{args.port}'
    command = [str(args.server.resolve()), '-m', str(args.model.resolve()),
               '-t', str(args.threads), '-c', str(args.ctx_size), '--parallel', str(args.parallel),
               '-b', str(args.batch_size), '-ub', str(args.ubatch_size), '-fa', 'on', '--host', '127.0.0.1',
               '--port', str(args.port), '-ctk', args.cache_type_k, '-ctv', args.cache_type_v]
    if args.gpu_layers is not None:
        command += ['-ngl', str(args.gpu_layers)]
    if args.server_log_verbosity is not None:
        command += ['-lv', str(args.server_log_verbosity)]
    if args.mode == 'mtp':
        command += ['--spec-type', 'draft-mtp', '--spec-draft-n-max', str(args.spec_draft_n_max)]
    if args.kv_unified:
        command += ['--kv-unified']
    config = {key: str(value) if isinstance(value, Path) else value
              for key, value in vars(args).items()}
    config['command'] = command
    config['slot_assignment'] = 'pinned' if args.slot_contexts else 'automatic'
    if prompt_text is not None:
        config['prompt_sha256'] = hashlib.sha256(prompt_text.encode()).hexdigest()
    config['runtime_env'] = {key: os.environ.get(key) for key in (
        'SPINE_MTP_WINDOW', 'SPINE_SPEC_MAX_CONTEXT', 'SPINE_SPEC_MAX_ACTIVE',
        'SPINE_SPEC_RS', 'SPINE_SPEC_LOWACC', 'SPINE_FA_WIDE_TILE', 'SPINE_KV_PAGE_GATHER') if os.environ.get(key) is not None}
    with args.log.open('wb') as log, args.output.open('a') as output:
        proc = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                stdin=subprocess.DEVNULL, env=os.environ.copy())
        stop = threading.Event()
        samples = []
        sampler = threading.Thread(target=sample_rss, args=(proc.pid, stop, samples, args.sample_interval))
        sampler.start()
        try:
            wait_healthy(proc, url, args.timeout)
            config['rss_loaded_kib'] = vmrss_kib(proc.pid)
            config['vms_loaded_kib'] = vmsize_kib(proc.pid)
            output.write(json.dumps({'kind': 'config', **config}, sort_keys=True) + '\n')
            output.flush()
            for context in args.contexts:
                for repeat in range(args.repeats):
                    slot_contexts = args.slot_contexts
                    if slot_contexts and args.rotate_slot_contexts:
                        offset = repeat % len(slot_contexts)
                        slot_contexts = slot_contexts[offset:] + slot_contexts[:offset]
                    prompts = ([make_prompt(url, length, prompt_text) for length in slot_contexts]
                               if slot_contexts else [make_prompt(url, context, prompt_text)] * args.concurrency)
                    before = time.monotonic()
                    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
                        futures = [pool.submit(complete, url, prompts[slot], args.n_predict,
                                               args.timeout, slot, args.ignore_eos, args.cache_prompt,
                                               bool(args.slot_contexts), args.capture_token_ids) for slot in range(args.concurrency)]
                        results = [future.result() for future in futures]
                    after = time.monotonic()
                    rss = [value for stamp, value, _ in samples if before <= stamp <= after]
                    available = [value for stamp, _, value in samples if before <= stamp <= after and value is not None]
                    decode_rss = [value for stamp, value, _ in samples if
                                  any(r['first_at'] is not None and r['first_at'] <= stamp <= r['finished_at']
                                      for r in results)]
                    decode_rss_delta = decode_rss[-1] - decode_rss[0] if len(decode_rss) >= 2 else None
                    for result in results:
                        result.pop('first_at')
                        result.pop('finished_at')
                    record = {'kind': 'measurement', 'label': args.label, 'mode': args.mode,
                              'context_tokens': context if not args.slot_contexts else 'mixed',
                              'slot_contexts': slot_contexts, 'repeat': repeat,
                              'concurrency': args.concurrency, 'results': results,
                              'rss_kib': stats(rss), 'rss_samples': len(rss),
                              'rss_decode_kib': stats(decode_rss), 'rss_decode_samples': len(decode_rss),
                              'rss_decode_delta_kib': decode_rss_delta,
                              'mem_available_kib': stats(available),
                              'vms_after_kib': vmsize_kib(proc.pid),
                              'elapsed_s': round(after - before, 3),
                              'aggregate_tps': round(sum(r['tokens_predicted'] or 0 for r in results)
                                                     / (after - before), 4)}
                    print(json.dumps(record, sort_keys=True), flush=True)
                    output.write(json.dumps(record, sort_keys=True) + '\n')
                    output.flush()
        finally:
            stop.set()
            sampler.join()
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()


if __name__ == '__main__':
    main()
