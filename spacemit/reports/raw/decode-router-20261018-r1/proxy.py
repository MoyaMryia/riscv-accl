#!/usr/bin/env python3
"""把文本请求转发到已配置的解码后端。"""
import argparse
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import threading
import time
import urllib.error
import urllib.request

import classifier
import policy

MAX_BODY_BYTES = 1024 * 1024
RELAY_BYTES = 64 * 1024
BODY_TIMEOUT_S = 10
DEFAULT_UPSTREAM_TIMEOUT_S = 1800


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None


def make_server(address, model, backends, upstream_timeout, score_guard=False):
    gate = threading.Lock()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    class Handler(BaseHTTPRequestHandler):
        def json_response(self, status, value):
            data = json.dumps(value, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            self.close_connection = True

        def do_GET(self):
            if self.path == '/health':
                self.json_response(200, {'gateway': 'ready', 'routes': list(backends), 'score_guard': score_guard})
            else:
                self.json_response(404, {'error': 'unknown endpoint'})

        def do_POST(self):
            if self.path != '/v1/chat/completions':
                self.json_response(404, {'error': 'unknown endpoint'})
                return
            if self.headers.get('Content-Type', '').split(';')[0].strip().lower() != 'application/json':
                self.json_response(415, {'error': 'use application/json'})
                return
            length = self.headers.get('Content-Length')
            if length is None:
                self.json_response(411, {'error': 'Content-Length is required'})
                return
            try:
                count = int(length)
            except ValueError:
                self.json_response(400, {'error': 'Content-Length must be an integer'})
                return
            if count > MAX_BODY_BYTES:
                self.json_response(413, {'error': 'request body exceeds the limit'})
                return
            if count <= 0:
                self.json_response(400, {'error': 'request body is empty'})
                return
            self.connection.settimeout(BODY_TIMEOUT_S)
            try:
                data = self.rfile.read(count)
                if len(data) != count:
                    raise ValueError('request body is truncated')
                payload = json.loads(data)
                text = policy.request_text(payload)
                mode = policy.check_mode(self.headers.get('X-Decode-Mode', 'auto').strip(), backends)
            except TimeoutError:
                self.json_response(408, {'error': 'request body timeout'})
                return
            except ValueError as error:
                self.json_response(400, {'error': str(error)})
                return
            prediction = None
            classify_ms = 0.0
            if mode == 'auto':
                begin = time.perf_counter()
                prediction = classifier.predict(model, text)
                decision = policy.choose(model, prediction, backends, score_guard=score_guard)
                classify_ms = (time.perf_counter() - begin) * 1000
            else:
                decision = {'route': mode, 'reason': 'manual'}
            route = decision['route']
            request = urllib.request.Request(backends[route] + '/v1/chat/completions', data=data,
                                              headers={'Content-Type': 'application/json'}, method='POST')
            started = False
            status = 'upstream_error'
            queued = time.monotonic()
            with gate:
                wait_ms = (time.monotonic() - queued) * 1000
                try:
                    with opener.open(request, timeout=upstream_timeout) as response:
                        self.send_response(response.status)
                        self.send_header('Content-Type', response.headers.get('Content-Type', 'application/json'))
                        for name in ('Content-Encoding', 'Content-Language', 'Cache-Control'):
                            value = response.headers.get(name)
                            if value is not None:
                                self.send_header(name, value)
                        self.send_header('X-Decode-Route', route)
                        self.send_header('X-Route-Reason', decision['reason'])
                        self.send_header('X-Classify-Ms', f'{classify_ms:.6f}')
                        self.send_header('Connection', 'close')
                        self.end_headers()
                        started = True
                        while True:
                            chunk = response.read1(RELAY_BYTES)
                            if not chunk:
                                break
                            self.wfile.write(chunk)
                            self.wfile.flush()
                        status = 'relayed'
                except urllib.error.HTTPError as error:
                    error.close()
                    self.json_response(error.code, {'error': 'upstream rejected the request', 'upstream_status': error.code})
                except BrokenPipeError:
                    status = 'connection_closed'
                except (OSError, http.client.HTTPException) as error:
                    if not started:
                        self.json_response(502, {'error': 'upstream unavailable', 'type': type(error).__name__})
                    else:
                        self.log_error('relay transport failed: %s', type(error).__name__)
                finally:
                    self.close_connection = True
                    print(json.dumps({'route': route, 'reason': decision['reason'], 'score_guard': score_guard,
                        'category': prediction['category'] if prediction else None,
                        'score': prediction['score'] if prediction else None,
                        'classify_ms': classify_ms, 'queue_ms': wait_ms, 'status': status}), flush=True)

    return ThreadingHTTPServer(address, Handler)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', required=True)
    parser.add_argument('--direct', required=True)
    parser.add_argument('--prefix', required=True)
    parser.add_argument('--full')
    parser.add_argument('--score-guard', action='store_true')
    parser.add_argument('--port', type=int, default=18090)
    parser.add_argument('--upstream-timeout', type=float, default=DEFAULT_UPSTREAM_TIMEOUT_S)
    args = parser.parse_args(argv)
    if not 0 < args.port < 65536 or not math.isfinite(args.upstream_timeout) or args.upstream_timeout <= 0:
        parser.error('use a valid port and a positive timeout')
    backends = policy.check_backends({name: getattr(args, name) for name in policy.ROUTES if getattr(args, name)})
    model = classifier.load_model(args.model)
    server = make_server(('127.0.0.1', args.port), model, backends, args.upstream_timeout, args.score_guard)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
