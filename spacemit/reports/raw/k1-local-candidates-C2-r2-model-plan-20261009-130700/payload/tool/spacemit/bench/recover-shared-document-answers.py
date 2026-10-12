#!/usr/bin/env python3
"""Recover readable answers from archived token IDs without rerunning prefill."""

import argparse
import hashlib
import importlib.util
import json
import os
import socket
import subprocess
from pathlib import Path

spec = importlib.util.spec_from_file_location('bench_lifecycle', Path(__file__).with_name('bench-lifecycle.py'))
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--port', type=int, default=18086)
    parser.add_argument('--document', type=Path, help='local copy of the benchmark corpus')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('refusing to overwrite existing output')
    config, *runs = [json.loads(line) for line in args.record.read_text().splitlines() if line.strip()]
    if [r['name'] for r in runs] != ['question_a_cold', 'question_b_warm', 'question_b_cold_control']:
        raise ValueError('record does not have the expected three requests')
    answers = {}
    if all(isinstance(record['result'].get('text'), str) for record in runs[1:]):
        for record in runs[1:]:
            result = record['result']
            name = 'warm' if record['name'] == 'question_b_warm' else 'cold'
            answers[name] = result['text']
            answers[name + '_hash_matches_stream'] = (
                hashlib.sha256(result['text'].encode()).hexdigest() == result['sha256'])
    else:
        command = config['command']
        server, model = command[0], command[command.index('-m') + 1]
        with socket.socket() as probe:
            if probe.connect_ex(('127.0.0.1', args.port)) == 0:
                raise RuntimeError('detokenize port already in use')
        url = f'http://127.0.0.1:{args.port}'
        launch = [server, '-m', model, '-t', '4', '-c', '512', '--parallel', '1',
                  '--host', '127.0.0.1', '--port', str(args.port), '-ctk', 'f16', '-ctv', 'f16']
        log_path = args.output.with_suffix('.server.log')
        with log_path.open('wb') as log:
            proc = subprocess.Popen(launch, stdout=log, stderr=subprocess.STDOUT,
                                    stdin=subprocess.DEVNULL, env=os.environ.copy())
            try:
                bench.wait_healthy(proc, url, 180)
                for record in runs[1:]:
                    result = record['result']
                    response = bench.post_json(url + '/detokenize', {'tokens': result['token_ids']})
                    content = response.get('content')
                    if not isinstance(content, str):
                        raise ValueError('detokenize did not return content')
                    name = 'warm' if record['name'] == 'question_b_warm' else 'cold'
                    answers[name] = content
                    answers[name + '_hash_matches_stream'] = (
                        hashlib.sha256(content.encode()).hexdigest() == result['sha256'])
            finally:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
    document = (args.document or Path(config['document'])).read_text(encoding='utf-8')
    start = document.index('## Quick start')
    end = document.index('## Description', start)
    evidence = document[start:end].strip()
    case = {'case_id': f"{config['model_size']}-{config['context']}-changed-question",
            'question': config['questions'][1], 'evidence': evidence,
            'warm_answer': answers['warm'], 'cold_answer': answers['cold'],
            'warm_hash_matches_stream': answers['warm_hash_matches_stream'],
            'cold_hash_matches_stream': answers['cold_hash_matches_stream'],
            'source_record': str(args.record), 'document_sha256': config['document_sha256']}
    args.output.write_text(json.dumps(case, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f"Recovered {case['case_id']}: warm hash match "
          f"{case['warm_hash_matches_stream']}, cold hash match "
          f"{case['cold_hash_matches_stream']}")


if __name__ == '__main__':
    main()
