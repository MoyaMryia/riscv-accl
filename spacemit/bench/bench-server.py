#!/usr/bin/env python3
"""Compare plain, MTP, and n-gram speculative decoding on a llama-server GGUF."""

import argparse
import hashlib
import json
import os
import re
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path


def prompts_ngram():
    source = (Path(__file__).resolve().parent / 'fixtures/ngram-mod.cpp').read_text()
    cpp = source[source.index('size_t common_ngram_mod::idx'):source.index('void common_ngram_mod::reset')]
    py = '''def aggregate_records(records):
    totals = {}
    for row in records:
        category = row["category"].strip().lower()
        amount = float(row.get("amount", 0))
        if category not in totals:
            totals[category] = 0.0
        totals[category] += amount
    result = []
    for category, amount in totals.items():
        result.append((category, round(amount, 2)))
    result.sort(key=lambda item: item[0])
    return result
'''
    return {
        'cpp_edit': 'Change 6364136223846793005ULL to 6364136223846793007ULL in the C++ source below. Return the complete updated source only, without commentary.\n\n' + cpp,
        'python_edit': 'Rename the loop variable row to item in this Python function. Return the entire updated function only, preserving the rest of the code.\n\n' + py,
        'prose': 'Explain how the RISC-V vector extension helps with matrix multiplication, including one concrete example and the limits of vectorization.',
    }


def prompts_frspec():
    return {
        'english': 'The theory of relativity states',
        'code': 'Write a Python function that computes Fibonacci numbers efficiently. Include a short explanation of its complexity.',
        'chinese': '请用中文解释RISC-V向量扩展如何加速矩阵乘法，并给一个具体例子。',
    }


def mode_flags(mode, ngram_min, ngram_max, draft_p_min, backend_sampling):
    if mode == 'plain':
        return []
    sampling = [] if backend_sampling else ['--no-spec-draft-backend-sampling']
    if mode == 'mtp':
        return ['--spec-type', 'draft-mtp', '--spec-draft-n-max', '3', '--spec-draft-p-min', str(draft_p_min)] + sampling
    ngram = ['--spec-ngram-mod-n-match', '16', '--spec-ngram-mod-n-min', str(ngram_min), '--spec-ngram-mod-n-max', str(ngram_max)]
    if mode == 'ngram':
        return ['--spec-type', 'ngram-mod'] + ngram
    if mode == 'combined':
        return ['--spec-type', 'ngram-mod,draft-mtp', '--spec-draft-n-max', '3', '--spec-draft-p-min', str(draft_p_min)] + sampling + ngram
    raise ValueError(mode)


def wait_healthy(proc, url, timeout=120):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f'server exited with code {proc.returncode}')
        try:
            with urllib.request.urlopen(url + '/health', timeout=2) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(1)
    raise TimeoutError('server health check timed out')


def completion(url, prompt, n_predict):
    payload = json.dumps({
        'prompt': prompt, 'n_predict': n_predict, 'temperature': 0,
        'seed': 42, 'cache_prompt': False,
    }).encode()
    request = urllib.request.Request(url + '/completion', payload, {'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server', type=Path, required=True, help='built llama-server executable')
    parser.add_argument('--model', type=Path, required=True, help='GGUF to use for all modes')
    parser.add_argument('--model-label', help='label for output records; defaults to model filename')
    parser.add_argument('--prompt-set', choices=('ngram', 'frspec'), default='ngram')
    parser.add_argument('--prompt', action='append', help='run only this prompt name; repeatable')
    parser.add_argument('--modes', nargs='+', choices=('plain', 'ngram', 'mtp', 'combined'), default=['plain', 'ngram', 'mtp', 'combined'])
    parser.add_argument('--ngram-min', type=int, default=16)
    parser.add_argument('--ngram-max', type=int, default=16, help='maximum n-gram draft length (default: 16)')
    parser.add_argument('--n-predict', type=int, default=160)
    parser.add_argument('--draft-p-min', type=float, default=0.0, help='MTP draft confidence threshold (default: 0)')
    parser.add_argument('--draft-backend-sampling', choices=('on', 'off'), default='on')
    parser.add_argument('--batch-size', type=int, default=32)
    parser.add_argument('--ubatch-size', type=int, default=32)
    parser.add_argument('--port', type=int, default=18085)
    parser.add_argument('--output', type=Path, help='append JSONL results here')
    parser.add_argument('--log-dir', type=Path, default=Path('/tmp'))
    args = parser.parse_args()
    if not 0.0 <= args.draft_p_min <= 1.0:
        parser.error('--draft-p-min must be between 0 and 1')
    if not 1 <= args.ngram_min <= args.ngram_max <= 1024:
        parser.error('require 1 <= --ngram-min <= --ngram-max <= 1024')
    if not 1 <= args.ubatch_size <= args.batch_size:
        parser.error('require 1 <= --ubatch-size <= --batch-size')
    if any(mode in ('ngram', 'combined') for mode in args.modes) and args.batch_size <= args.ngram_max:
        parser.error('--batch-size must exceed --ngram-max to hold sampled and draft tokens')

    if not args.server.is_file() or not args.model.is_file():
        parser.error('server executable and model GGUF must exist')
    prompts = prompts_ngram() if args.prompt_set == 'ngram' else prompts_frspec()
    if args.prompt:
        unknown = set(args.prompt) - set(prompts)
        if unknown:
            parser.error(f'unknown prompts: {sorted(unknown)}')
        prompts = {key: prompts[key] for key in args.prompt}
    args.log_dir.mkdir(parents=True, exist_ok=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
    label = args.model_label or args.model.stem
    url = f'http://127.0.0.1:{args.port}'
    with socket.socket() as probe:
        if probe.connect_ex(('127.0.0.1', args.port)) == 0:
            parser.error(f'port {args.port} is already in use')

    hashes = {}
    for mode in args.modes:
        safe_label = re.sub(r'[^A-Za-z0-9_.-]', '_', label)
        log_path = args.log_dir / f'bench-server-{safe_label}-{mode}.log'
        command = [
            str(args.server.resolve()), '-m', str(args.model.resolve()),
            '-t', '4', '-c', '8192', '--parallel', '1',
            '-b', str(args.batch_size), '-ub', str(args.ubatch_size), '-fa', 'on',
            '--host', '127.0.0.1', '--port', str(args.port),
        ] + mode_flags(mode, args.ngram_min, args.ngram_max, args.draft_p_min, args.draft_backend_sampling == 'on')
        with log_path.open('wb') as log:
            proc = subprocess.Popen(command, cwd=args.server.resolve().parent, env=os.environ.copy(),
                                    stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
            try:
                wait_healthy(proc, url)
                for name, prompt in prompts.items():
                    started = time.monotonic()
                    result = completion(url, prompt, args.n_predict)
                    timings = result.get('timings', {})
                    digest = hashlib.sha256(result.get('content', '').encode()).hexdigest()
                    record = {
                        'model': label, 'mode': mode, 'prompt': name,
                        'ngram_min': args.ngram_min if mode in ('ngram', 'combined') else None,
                        'ngram_max': args.ngram_max if mode in ('ngram', 'combined') else None,
                        'batch_size': args.batch_size, 'ubatch_size': args.ubatch_size,
                        'draft_p_min': args.draft_p_min if mode in ('mtp', 'combined') else None,
                        'draft_backend_sampling': args.draft_backend_sampling if mode in ('mtp', 'combined') else None,
                        'prompt_tokens': timings.get('prompt_n'),
                        'tokens': result.get('tokens_predicted'),
                        'tps': timings.get('predicted_per_second'),
                        'draft_n': timings.get('draft_n'),
                        'accepted': timings.get('draft_n_accepted'),
                        'wall_s': round(time.monotonic() - started, 2),
                        'stop_type': result.get('stop_type'), 'sha256': digest,
                    }
                    line = json.dumps(record, sort_keys=True)
                    print(line, flush=True)
                    if args.output:
                        with args.output.open('a') as stream:
                            stream.write(line + '\n')
                    if name in hashes and hashes[name] != digest:
                        raise RuntimeError(f'greedy output changed for {name}: {hashes[name]} -> {digest}')
                    hashes[name] = digest
            finally:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()


if __name__ == '__main__':
    main()
