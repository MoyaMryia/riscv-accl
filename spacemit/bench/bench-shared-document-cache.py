#!/usr/bin/env python3
"""Compare a new question on a cached document with a forced-cold answer."""

import argparse
import hashlib
import importlib.util
import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

HELPER_PATH = Path(__file__).with_name('bench-lifecycle.py')
spec = importlib.util.spec_from_file_location('bench_lifecycle', HELPER_PATH)
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)

QUESTIONS = (
    'Question A: Summarize what llama.cpp does in one sentence. Answer using the document above.',
    'Question B: According to the document, how can a user build and run llama.cpp? Answer briefly using the document above.',
)


def write_record(handle, record):
    handle.write(json.dumps(record, sort_keys=True) + '\n')
    handle.flush()


def without_special(url, text):
    result = bench.post_json(url + '/tokenize', {'content': text, 'add_special': False})
    tokens = result['tokens']
    if not tokens or not all(isinstance(item, int) for item in tokens):
        raise RuntimeError('question tokenization failed')
    return tokens


def run(args):
    if args.output.exists() or args.log.exists():
        raise FileExistsError('refusing to overwrite an existing output or log')
    if not args.server.is_file() or not args.model.is_file() or not args.document.is_file():
        raise FileNotFoundError('server, model, or document is missing')
    if args.context + 256 > args.ctx_size:
        raise ValueError('context allocation must allow the document, question, and 32 outputs')
    with socket.socket() as probe:
        if probe.connect_ex(('127.0.0.1', args.port)) == 0:
            raise RuntimeError(f'port {args.port} is already in use')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.log.parent.mkdir(parents=True, exist_ok=True)
    content = args.document.read_text(encoding='utf-8')
    document_sha = hashlib.sha256(content.encode()).hexdigest()
    command = [str(args.server), '-m', str(args.model), '-t', '4', '-c', str(args.ctx_size),
               '--parallel', '1', '-b', '32', '-ub', '32', '-fa', 'on', '--host', '127.0.0.1',
               '--port', str(args.port), '-ctk', 'f16', '-ctv', 'f16']
    config = {'kind': 'config', 'model_size': args.model_size, 'context': args.context,
              'ctx_size': args.ctx_size, 'n_predict': 32, 'questions': QUESTIONS,
              'document': str(args.document), 'document_sha256': document_sha,
              'command': command, 'SPINE_FA_WIDE_TILE': os.environ.get('SPINE_FA_WIDE_TILE')}
    url = f'http://127.0.0.1:{args.port}'
    with args.log.open('wb') as log, args.output.open('w') as output:
        proc = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                stdin=subprocess.DEVNULL, env=os.environ.copy())
        stop = threading.Event()
        samples = []
        sampler = threading.Thread(target=bench.sample_rss,
                                   args=(proc.pid, stop, samples, .2), daemon=True)
        sampler.start()
        try:
            bench.wait_healthy(proc, url, args.timeout)
            config['rss_loaded_kib'] = bench.vmrss_kib(proc.pid)
            config['vms_loaded_kib'] = bench.vmsize_kib(proc.pid)
            document_tokens = bench.tokenize(url, content)
            if len(document_tokens) < args.context:
                raise ValueError(f'document has {len(document_tokens)} tokens; need {args.context}')
            prefix = document_tokens[:args.context]
            question_tokens = [without_special(url, '\n\n' + q) for q in QUESTIONS]
            assert question_tokens[0] != question_tokens[1]
            prompts = [prefix + suffix for suffix in question_tokens]
            if max(map(len, prompts)) + 32 > args.ctx_size:
                raise ValueError('document and question exceed context allocation')
            config['document_tokens_available'] = len(document_tokens)
            config['prefix_token_sha256'] = hashlib.sha256(json.dumps(prefix).encode()).hexdigest()
            config['question_token_counts'] = list(map(len, question_tokens))
            config['prompt_lengths'] = list(map(len, prompts))
            write_record(output, config)
            # B has not been sent when the cached B request begins. Thus its only
            # possible shared content in this single slot is the document in A.
            for name, prompt, cache_prompt in (
                ('question_a_cold', prompts[0], True),
                ('question_b_warm', prompts[1], True),
                ('question_b_cold_control', prompts[1], False),
            ):
                before = time.monotonic()
                result = bench.complete(url, prompt, 32, args.timeout, 0, True,
                                        cache_prompt, True, True)
                after = time.monotonic()
                rss = [value for stamp, value, _ in samples if before <= stamp <= after]
                available = [value for stamp, _, value in samples
                             if before <= stamp <= after and value is not None]
                result.pop('first_at')
                result.pop('finished_at')
                record = {'kind': 'measurement', 'name': name, 'cache_prompt': cache_prompt,
                          'prompt_tokens': len(prompt), 'result': result,
                          'rss_kib': bench.stats(rss),
                          'mem_available_kib': bench.stats(available)}
                write_record(output, record)
        finally:
            stop.set()
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
            sampler.join(timeout=2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server', type=Path, required=True)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--model-size', choices=['2B', '4B'], required=True)
    parser.add_argument('--document', type=Path, required=True)
    parser.add_argument('--context', type=int, required=True)
    parser.add_argument('--ctx-size', type=int, required=True)
    parser.add_argument('--timeout', type=int, required=True)
    parser.add_argument('--port', type=int, default=18085)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--log', type=Path, required=True)
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    run(args)


if __name__ == '__main__':
    main()
