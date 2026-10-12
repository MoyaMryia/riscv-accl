#!/usr/bin/env python3
"""Regression check for physical slot assignment in lifecycle measurements."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def serve(port):
    # Windows 'a'-mode appends seek-then-write and two handler threads can
    # clobber each other's lines; serialize the request log.
    log_lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            self.send_response(200 if self.path == '/health' else 404)
            self.end_headers()

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            self.send_response(200)
            self.end_headers()
            if self.path == '/tokenize':
                self.wfile.write(json.dumps({'tokens': [1, 2, 3]}).encode())
                return
            with log_lock, open(os.environ['SLOT_TEST_REQUESTS'], 'a') as output:
                output.write(json.dumps(body) + '\n')
            assigned = body.get('id_slot', 1)
            if os.environ.get('SLOT_TEST_WRONG'):
                assigned = 1 - assigned
            for item in (
                {'tokens': [len(body['prompt'])], 'content': str(len(body['prompt']))},
                {'stop': True, 'id_slot': assigned, 'tokens_predicted': 1,
                 'stop_type': 'limit', 'timings': {'predicted_per_second': 1.0}},
            ):
                self.wfile.write(b'data: ' + json.dumps(item).encode() + b'\n\n')
                self.wfile.flush()
    ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()


def check():
    import socket
    root = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix='lifecycle-slots-') as directory:
        tmp = Path(directory)
        serve_copy = tmp / 'slot-test-server.py'
        shutil.copyfile(Path(__file__).resolve(), serve_copy)
        server = tmp / ('server.bat' if os.name == 'nt' else 'server')
        if os.name == 'nt':
            server.write_text(f'@echo off\r\n"{sys.executable}" "{serve_copy}" --serve %*\r\n')
        else:
            server.write_text(f'#!/bin/sh\nexec {sys.executable} {serve_copy} --serve "$@"\n')
            server.chmod(0o755)
        model = tmp / 'model.gguf'
        model.touch()
        for mode in ('pinned', 'wrong', 'automatic'):
            with socket.socket() as probe:
                probe.bind(('127.0.0.1', 0))
                port = probe.getsockname()[1]
            output = tmp / f'{mode}.jsonl'
            requests = tmp / f'{mode}-requests.jsonl'
            env = dict(os.environ, SLOT_TEST_REQUESTS=str(requests))
            if mode == 'wrong':
                env['SLOT_TEST_WRONG'] = '1'
            command = [sys.executable, str(root / 'bench-lifecycle.py'),
                       '--server', str(server), '--model', str(model), '--label', mode,
                       '--contexts', '2', '--ctx-size', '64', '--parallel', '2',
                       '--concurrency', '2', '--repeats', '2', '--n-predict', '1',
                       '--port', str(port), '--output', str(output),
                       '--log', str(tmp / f'{mode}.log')]
            if mode != 'automatic':
                command += ['--slot-contexts', '2', '3', '--rotate-slot-contexts']
            run = subprocess.run(command, env=env, capture_output=True, text=True)
            if mode == 'wrong':
                assert run.returncode != 0 and 'requested slot' in run.stderr, run.stderr
                continue
            assert run.returncode == 0, run.stderr
            rows = [json.loads(line) for line in output.read_text().splitlines()]
            bodies = [json.loads(line) for line in requests.read_text().splitlines()]
            if mode == 'pinned':
                assert rows[0]['slot_assignment'] == 'pinned'
                assert [row['slot_contexts'] for row in rows[1:]] == [[2, 3], [3, 2]]
                for round_index in range(2):
                    observed = {body['id_slot']: len(body['prompt']) for body in bodies[2*round_index:2*round_index+2]}
                    assert observed == ({0: 2, 1: 3} if round_index == 0 else {0: 3, 1: 2}), observed
                assert all(result['server_slot'] == result['requested_slot'] == result['slot']
                           for row in rows[1:] for result in row['results'])
            else:
                assert rows[0]['slot_assignment'] == 'automatic'
                assert all('id_slot' not in body for body in bodies)
                assert all(result['server_slot'] == 1 and result['requested_slot'] is None
                           for row in rows[1:] for result in row['results'])
            audit = subprocess.run([sys.executable, str(root / 'audit-lifecycle.py'), str(output),
                                    '--require-identical', '--require-token-ids'], capture_output=True, text=True)
            assert audit.returncode == 0, audit.stdout + audit.stderr
            if mode == 'pinned':
                rows[1]['results'][0]['server_slot'] = 1
                output.write_text(''.join(json.dumps(row) + '\n' for row in rows))
                audit = subprocess.run([sys.executable, str(root / 'audit-lifecycle.py'), str(output)],
                                       capture_output=True, text=True)
                assert audit.returncode != 0 and 'pinned request' in audit.stdout, audit.stdout
        print('PASS: pinned rotation, returned-slot audit, mismatch rejection, automatic assignment')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--serve', action='store_true')
    parser.add_argument('--port', type=int)
    args, _ = parser.parse_known_args()
    if args.serve:
        serve(args.port)
    else:
        check()
