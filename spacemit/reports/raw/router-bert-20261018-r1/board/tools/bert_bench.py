#!/usr/bin/env python3
"""对照 PyTorch 参考结果，测量 K1 BERT 分类完整时间。"""
import argparse
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

import diagnostic as base

LOGIT_ERROR_LIMIT = 0.02
REPEATS = 3


def verify_prediction(actual, reference):
    if actual['selected_token_ids'] != reference['selected_token_ids']:
        raise ValueError('native tokenization differs from the HF reference')
    error = max(abs(a - b) for a, b in zip(actual['logits'], reference['logits']))
    if error > LOGIT_ERROR_LIMIT:
        raise ValueError('native logits differ from the PyTorch reference: ' + str(error))
    if actual['category'] != reference['category']:
        raise ValueError('native category differs from the PyTorch reference')
    return error


def summary_times(values):
    return {'count': len(values), 'median_ms': statistics.median(values),
            'p95_ms': sorted(values)[math.ceil(0.95 * len(values)) - 1],
            'min_ms': min(values), 'max_ms': max(values)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('server', 'spert', 'tcm', 'router', 'head', 'model', 'reference', 'receipt', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--port', type=int, default=18120)
    args = parser.parse_args(argv)
    if not os.environ.get('TMUX') or os.environ.get('K1_PACKAGE_LOCK_FD') != '9':
        parser.error('run inside tmux with the package lock on FD 9')
    os.fstat(9)
    signal.signal(signal.SIGTERM, base.term_handler)
    active = subprocess.run(['pgrep', '-x', 'llama-server'], capture_output=True)
    if active.returncode != 1:
        raise RuntimeError('another server is active or pgrep failed')
    expected = json.loads(args.receipt.read_text())
    paths = {'model': args.model, 'head': args.head, 'reference': args.reference,
             'benchmark': Path(__file__), 'diagnostic': Path(base.__file__)}
    paths.update({'router_' + name: args.router / name for name in
        ('bert_runtime.py', 'bert_common.py', 'classifier.py', 'policy.py', 'proxy.py', 'train.py', 'model.json.gz')})
    if not isinstance(expected, dict) or set(expected) != set(paths):
        raise ValueError('benchmark input receipt fields differ')
    for name, path in paths.items():
        if base.sha256(path) != expected[name]:
            raise ValueError('benchmark input hash differs: ' + name)
    if base.sha256(args.server) != base.SERVER_SHA or base.sha256(args.spert / 'lib/libspert.so') != base.SPERT_SHA or base.sha256(args.tcm / 'libspine_tcm.so') != base.TCM_SHA:
        raise ValueError('native runtime identity differs')
    sys.path.insert(0, str(args.router))
    import bert_runtime
    import classifier
    import train as task_data
    client = bert_runtime.Client(args.head, f'http://127.0.0.1:{args.port}', base.DEADLINE_S)
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1', args.port)) == 0:
            raise RuntimeError('encoder port is occupied')
    references = json.loads(args.reference.read_text())
    if not isinstance(references, list) or not references:
        raise ValueError('reference is empty')
    seen = set()
    for row in references:
        if not isinstance(row, dict) or not isinstance(row.get('id'), str) or not re.fullmatch(r'[A-Za-z0-9_-]+', row['id']) or row['id'] in seen:
            raise ValueError('reference identifier differs')
        seen.add(row['id'])
        if not isinstance(row.get('text'), str) or not row['text'].strip() or row.get('label') not in classifier.LABELS or row.get('category') not in classifier.LABELS or row.get('partition') not in ('test', 'regression'):
            raise ValueError('reference text or label differs')
        row['text'].encode('utf-8')
        if not isinstance(row.get('logits'), list) or len(row['logits']) != len(classifier.LABELS) or any(type(v) not in (int, float) or not math.isfinite(v) for v in row['logits']):
            raise ValueError('reference logits differ')
        if not isinstance(row.get('selected_token_ids'), list) or not 2 <= len(row['selected_token_ids']) <= client.head['max_tokens'] or not all(type(v) is int and 0 <= v < client.head['vocab_size'] for v in row['selected_token_ids']):
            raise ValueError('reference token IDs differ')
    if {row['partition'] for row in references} != {'test', 'regression'}:
        raise ValueError('both reference partitions are required')
    args.output.mkdir(parents=True, exist_ok=False)
    baseline = classifier.load_model(args.router / 'model.json.gz')
    command = [str(args.server), '-m', str(args.model), '--host', '127.0.0.1', '--port', str(args.port),
        '--alias', 'router-bert', '--embedding', '--pooling', 'cls', '--embd-normalize', '-1',
        '--ctx-size', str(client.head['max_tokens']), '--batch-size', str(client.head['max_tokens']),
        '--ubatch-size', str(client.head['max_tokens']), '--parallel', '1', '--threads', '4',
        '--threads-batch', '4', '--flash-attn', 'off', '--log-verbosity', '4']
    libraries = f'{args.server.parent}:{args.tcm}:{args.spert / "lib"}'
    environment = base.clean_environment(os.environ, libraries, lowacc=False)
    base.save(args.output / 'launch.json', {'argv': command, 'environment': environment})
    base.save(args.output / 'protocol.json', {'repeats': REPEATS, 'reference_count': len(references),
        'logit_error_limit': LOGIT_ERROR_LIMIT, 'timing': 'tokenize HTTP, embedding HTTP, and linear head',
        'token_selection': 'head, middle, tail', 'native_type': 'F32'})
    process = None
    timings, baseline_timings, errors = [], [], []
    first_predictions = {}
    with (args.output / 'server.log').open('w') as log:
        try:
            process = subprocess.Popen(command, env=environment, stdout=log, stderr=subprocess.STDOUT)
            base.wait_ready(process, client.url)
            with client.opener.open(client.url + '/props', timeout=30) as response:
                properties = json.load(response)
            if properties['total_slots'] != 1 or properties['default_generation_settings']['n_ctx'] != client.head['max_tokens']:
                raise ValueError('encoder context or slot count differs')
            base.save(args.output / 'properties.json', properties)
            for round_no in range(REPEATS):
                folder = args.output / f'round-{round_no + 1}'
                folder.mkdir()
                offset = round_no * (len(references) // REPEATS)
                ordered = references[offset:] + references[:offset]
                for reference in ordered:
                    begin = time.perf_counter()
                    prediction = client.predict(reference['text'])
                    elapsed_ms = (time.perf_counter() - begin) * 1000
                    begin = time.perf_counter()
                    old = classifier.predict(baseline, reference['text'])
                    old_ms = (time.perf_counter() - begin) * 1000
                    base.save(folder / (reference['id'] + '.json'), {'prediction': prediction,
                        'elapsed_ms': elapsed_ms, 'baseline': old, 'baseline_ms': old_ms})
                    errors.append(verify_prediction(prediction, reference))
                    timings.append(elapsed_ms)
                    baseline_timings.append(old_ms)
                    if round_no == 0:
                        first_predictions[reference['text']] = prediction
                base.save(args.output / 'progress.json', {'completed_rounds': round_no + 1,
                    'completed_decisions': len(timings)})
                print(json.dumps({'round': round_no + 1, 'decisions': len(timings),
                    'maximum_logit_error': max(errors)}), flush=True)
            resources = base.resource_snapshot(process.pid)
        finally:
            if process is not None:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                base.save(args.output / 'server-exit.json', {'returncode': process.returncode})
    if process.returncode != 0:
        raise RuntimeError('encoder exited abnormally: ' + str(process.returncode))
    metrics = {partition: task_data.evaluate(client.head,
        [row for row in references if row['partition'] == partition],
        predict=lambda model, text: first_predictions[text]) for partition in ('test', 'regression')}
    base.save(args.output / 'summary.json', {'bert': summary_times(timings),
        'baseline_ngram': summary_times(baseline_timings), 'metrics': metrics,
        'maximum_logit_error': max(errors), 'resources': resources})
    return 0


if __name__ == '__main__':
    sys.exit(main())
