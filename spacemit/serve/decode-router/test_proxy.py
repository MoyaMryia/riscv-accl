"""验证代理的本地 HTTP 路由和字节传输。"""
import gzip
import http.client
import json
from pathlib import Path
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import proxy


class StubServer(ThreadingHTTPServer):
    daemon_threads = False


class ProxyTests(unittest.TestCase):
    """用本地后端验证路由、响应流和并发门控。"""

    def setUp(self):
        self.stubs = []
        self.threads = []
        self.events = {}
        self.records = {}
        self.lock = threading.Lock()
        self.active = 0
        self.max_active = 0

    def tearDown(self):
        for event in self.events.values():
            event.set()
        for server in reversed(self.stubs):
            server.shutdown()
            server.server_close()
        for thread in self.threads:
            thread.join()

    def add_stub(self, name, status=200, streaming=False, delay_event=None,
                 first_chunk=b'data: first\n', final_chunk=b'data: [DONE]\n',
                 raw_body=None, content_encoding=None, redirect_to=None,
                 response_headers=None, truncate_response=False, unframed=False, chunked_response=False):
        owner = self
        self.events[name + '-done'] = threading.Event()
        self.events[name + '-entered'] = threading.Event()

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = self.rfile.read(int(self.headers['Content-Length']))
                with owner.lock:
                    owner.records[name] = (body, dict(self.headers))
                    owner.active += 1
                    owner.max_active = max(owner.max_active, owner.active)
                    owner.events[name + '-entered'].set()
                try:
                    if delay_event is not None:
                        if streaming:
                            self.send_response(status)
                            self.send_header('Content-Type', 'text/event-stream')
                            self.send_header('Content-Length', str(len(first_chunk) + len(final_chunk)))
                            self.end_headers()
                            self.wfile.write(first_chunk)
                            self.wfile.flush()
                            owner.events[name].set()
                            owner.events[name + '-release'].wait(5)
                            owner.events[name + '-done'].set()
                            self.wfile.write(final_chunk)
                            self.wfile.flush()
                        else:
                            owner.events[name].set()
                            delay_event.wait(5)
                            data = json.dumps({'backend': name}).encode()
                            self.send_response(status)
                            self.send_header('Content-Type', 'application/json')
                            self.send_header('Content-Length', str(len(data)))
                            self.end_headers()
                            self.wfile.write(data)
                    elif status >= 400:
                        data = b'upstream failure'
                        self.send_response(status)
                        self.send_header('Content-Type', 'text/plain')
                        self.send_header('Content-Length', str(len(data)))
                        self.end_headers()
                        self.wfile.write(data)
                    else:
                        data = raw_body if raw_body is not None else (
                            b'data: ' + name.encode() + b'\n\ndata: [DONE]\n'
                            if streaming else json.dumps({'backend': name}).encode())
                        self.send_response(status)
                        self.send_header('Content-Type', 'text/event-stream' if streaming else 'application/json')
                        if content_encoding is not None:
                            self.send_header('Content-Encoding', content_encoding)
                        if redirect_to is not None:
                            self.send_header('Location', redirect_to)
                        if chunked_response:
                            self.send_header('Transfer-Encoding', 'chunked')
                        elif not unframed:
                            self.send_header('Content-Length', str(len(data) + int(truncate_response)))
                        for key, value in (response_headers or {}).items():
                            self.send_header(key, value)
                        self.end_headers()
                        if chunked_response:
                            self.wfile.write(f'{len(data):x}\r\n'.encode() + data + b'\r\n')
                            if not truncate_response:
                                self.wfile.write(b'0\r\n\r\n')
                        else:
                            self.wfile.write(data)
                finally:
                    with owner.lock:
                        owner.active -= 1

            def log_message(self, *args):
                return

        server = StubServer(('127.0.0.1', 0), Handler)
        self.stubs.append(server)
        thread = threading.Thread(target=server.serve_forever)
        self.threads.append(thread)
        thread.start()
        return f'http://127.0.0.1:{server.server_port}'

    def start_proxy(self, backends, score_guard=False):
        model = {'min_score': 0.65}
        server = proxy.make_server(('127.0.0.1', 0), model, backends, 3, score_guard)
        self.stubs.append(server)
        thread = threading.Thread(target=server.serve_forever)
        self.threads.append(thread)
        thread.start()
        self.gateway = f'http://127.0.0.1:{server.server_port}'

    def send(self, body, mode=None, content_type='application/json'):
        headers = {'Content-Type': content_type}
        if mode is not None:
            headers['X-Decode-Mode'] = mode
        request = Request(self.gateway + '/v1/chat/completions', data=body, headers=headers)
        try:
            with urlopen(request, timeout=5) as response:
                return response.status, response.headers, response.read()
        except HTTPError as error:
            return error.code, error.headers, error.read()

    def test_bert_callback_uses_local_http_prediction_and_marks_response(self):
        prediction_server = self.add_prediction_server({'category': 'code', 'score': 0.91})
        endpoints = {name: self.add_stub(name) for name in ('direct', 'prefix')}
        calls = []

        def predictor(text):
            calls.append(text)
            with urlopen(prediction_server, timeout=2) as response:
                return json.load(response)

        server = proxy.make_server(('127.0.0.1', 0), {'min_score': 0.65}, endpoints, 3,
                                   predictor=predictor, classifier_name='bert')
        self.stubs.append(server)
        thread = threading.Thread(target=server.serve_forever)
        self.threads.append(thread)
        thread.start()
        self.gateway = f'http://127.0.0.1:{server.server_port}'
        with urlopen(self.gateway + '/health', timeout=5) as response:
            self.assertEqual(json.load(response)['classifier'], 'bert')
        status, headers, _ = self.send(b'{"messages":[{"role":"user","content":"code"}]}')
        self.assertEqual(status, 200)
        self.assertEqual(headers['X-Decode-Route'], 'prefix')
        self.assertEqual(headers['X-Classifier'], 'bert')
        self.assertEqual(calls, ['code'])
        status, manual_headers, _ = self.send(
            b'{"messages":[{"role":"user","content":"manual"}]}', 'direct')
        self.assertEqual(status, 200)
        self.assertEqual(manual_headers['X-Classifier'], 'bert')
        self.assertEqual(calls, ['code'])
        self.assertEqual(set(self.records), {'prefix', 'direct'})

    def add_prediction_server(self, value, status=200, delay=0):
        data = json.dumps(value).encode()

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if delay:
                    import time
                    time.sleep(delay)
                self.send_response(status)
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                try:
                    self.wfile.write(data)
                except BrokenPipeError:
                    pass

            def log_message(self, *args):
                return

        server = StubServer(('127.0.0.1', 0), Handler)
        self.stubs.append(server)
        thread = threading.Thread(target=server.serve_forever)
        self.threads.append(thread)
        thread.start()
        return f'http://127.0.0.1:{server.server_port}'

    def test_callback_failure_returns_502_without_decoder_request(self):
        endpoints = {name: self.add_stub(name) for name in ('direct', 'prefix')}
        for callback, expected in (
                (self.add_prediction_server({}, delay=0.2), 'timeout'),
                (self.add_prediction_server({}, status=503), 'http')):
            timeout = 0.03 if expected == 'timeout' else 2
            self.start_proxy_with_predictor(
                endpoints, lambda text, callback=callback, timeout=timeout:
                (urlopen(callback, timeout=timeout).read()))
            status, _, _ = self.send(b'{"messages":[{"role":"user","content":"x"}]}')
            self.assertEqual(status, 502)
            self.assertEqual(self.records, {})

    def start_proxy_with_predictor(self, backends, predictor):
        server = proxy.make_server(('127.0.0.1', 0), {'min_score': 0.65}, backends, 3,
                                   predictor=predictor, classifier_name='bert')
        self.stubs.append(server)
        thread = threading.Thread(target=server.serve_forever)
        self.threads.append(thread)
        thread.start()
        self.gateway = f'http://127.0.0.1:{server.server_port}'

    def test_cli_bert_arguments_require_a_matching_mode(self):
        from contextlib import redirect_stderr
        from io import StringIO

        base = ['--direct', 'http://127.0.0.1:19001', '--prefix', 'http://127.0.0.1:19002']
        for args in (base, ['--model', 'model.json.gz', '--bert-head', 'head.json', *base],
                     ['--bert-head', 'head.json', *base]):
            with self.subTest(args=args), redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                proxy.main(args)
        with self.assertRaisesRegex(ValueError, 'finite and positive'):
            proxy.main(['--bert-head', 'head.json', '--bert-url', 'http://127.0.0.1:19003',
                        '--bert-timeout', '0', *base])

    def test_manual_routes_forward_exact_bytes_and_hide_control_header(self):
        endpoints = {name: self.add_stub(name) for name in ('direct', 'prefix', 'full')}
        self.start_proxy(endpoints)
        payload = b'{ "messages" : [{"role":"user","content":"\xe4\xb8\xad\xe6\x96\x87  x"}], "temperature" : 0.25 }'
        for route in ('direct', 'prefix', 'full'):
            status, headers, _ = self.send(payload, route)
            self.assertEqual(status, 200)
            self.assertEqual(headers['X-Decode-Route'], route)
            sent, forwarded = self.records[route]
            self.assertEqual(sent, payload)
            self.assertNotIn('X-Decode-Mode', forwarded)

    def test_auto_routing_and_manual_bypass_use_fixed_predictions(self):
        endpoints = {name: self.add_stub(name) for name in ('direct', 'prefix', 'full')}
        self.start_proxy(endpoints)
        predictions = iter([
            {'category': 'code', 'score': 0.9},
            {'category': 'qa', 'score': 0.9},
            {'category': 'text', 'score': 0.9},
            {'category': 'code', 'score': 0.4},
        ])
        calls = []
        original = proxy.classifier.predict
        proxy.classifier.predict = lambda model, text: (calls.append(text), next(predictions))[1]
        try:
            payload = b'{"messages":[{"role":"user","content":"x"}]}'
            for expected in ('prefix', 'full', 'direct', 'prefix'):
                status, headers, _ = self.send(payload)
                self.assertEqual(status, 200)
                self.assertEqual(headers['X-Decode-Route'], expected)
            self.assertEqual(calls, ['x'] * 4)
            before = len(calls)
            self.send(payload, 'direct')
            self.assertEqual(len(calls), before)
        finally:
            proxy.classifier.predict = original

    def test_score_guard_is_explicit_and_disabled_by_default(self):
        endpoints = {name: self.add_stub(name) for name in ('direct', 'prefix')}
        original = proxy.classifier.predict
        proxy.classifier.predict = lambda model, text: {'category': 'code', 'score': .4}
        try:
            for guard, route, reason in ((False, 'prefix', 'class_map'), (True, 'direct', 'low_score')):
                self.start_proxy(endpoints, score_guard=guard)
                status, headers, _ = self.send(b'{"messages":[{"role":"user","content":"x"}]}')
                self.assertEqual(status, 200)
                self.assertEqual(headers['X-Decode-Route'], route)
                self.assertEqual(headers['X-Route-Reason'], reason)
        finally:
            proxy.classifier.predict = original

    def test_invalid_requests_do_not_reach_upstream_and_health_is_gateway_only(self):
        self.start_proxy({'direct': 'http://127.0.0.1:1', 'prefix': 'http://127.0.0.1:2'})
        with urlopen(self.gateway + '/health', timeout=5) as response:
            self.assertEqual(response.status, 200)
        payload = b'{"messages":[{"role":"user","content":"x"}]}'
        for body, mode, content_type, expected in (
                (b'{bad', None, 'application/json', 400),
                (payload, 'full', 'application/json', 400),
                (payload, None, 'text/plain', 415),
                (payload, None, 'application/json', 400)):
            if expected == 400 and body == payload and mode is None:
                request = Request(self.gateway + '/v1/chat/completions', data=body,
                                  headers={'Content-Type': content_type, 'Content-Length': '1048577'})
                try:
                    urlopen(request, timeout=5)
                except HTTPError as error:
                    self.assertEqual(error.code, 413)
                continue
            self.assertEqual(self.send(body, mode, content_type)[0], expected)
        self.assertEqual(self.records, {})

    def test_upstream_error_preserves_selected_route_without_retry(self):
        endpoints = {'direct': self.add_stub('direct', status=503),
                     'prefix': self.add_stub('prefix')}
        self.start_proxy(endpoints)
        payload = b'{"messages":[{"role":"user","content":"x"}]}'
        status, _, _ = self.send(payload, 'direct')
        self.assertEqual(status, 503)
        self.assertEqual(set(self.records), {'direct'})

    def test_upstream_redirect_does_not_follow_another_backend(self):
        prefix = self.add_stub('prefix')
        direct = self.add_stub('direct', status=302, redirect_to=prefix + '/v1/chat/completions')
        self.start_proxy({'direct': direct, 'prefix': prefix})
        status, _, _ = self.send(b'{"messages":[{"role":"user","content":"x"}]}', 'direct')
        self.assertEqual(status, 302)
        self.assertEqual(set(self.records), {'direct'})

    def test_stream_reaches_client_before_stub_finishes(self):
        self.events['stream'] = threading.Event()
        self.events['stream-release'] = threading.Event()
        endpoint = self.add_stub('stream', streaming=True, delay_event=self.events['stream-release'])
        self.start_proxy({'direct': endpoint, 'prefix': self.add_stub('prefix')})
        payload = b'{"messages":[{"role":"user","content":"x"}]}'
        request = Request(self.gateway + '/v1/chat/completions', data=payload,
                          headers={'Content-Type': 'application/json', 'X-Decode-Mode': 'direct'})
        response = urlopen(request, timeout=5)
        try:
            self.assertEqual(response.readline(), b'data: first\n')
            self.assertTrue(self.events['stream'].is_set())
        finally:
            self.events['stream-release'].set()
            rest = response.read()
            response.close()
        self.assertEqual(rest, b'data: [DONE]\n')

    def test_newline_free_bytes_reach_client_before_backend_finishes(self):
        self.events['binary'] = threading.Event()
        self.events['binary-release'] = threading.Event()
        endpoint = self.add_stub('binary', streaming=True, delay_event=self.events['binary-release'],
                                 first_chunk=b'first', final_chunk=b'last')
        self.start_proxy({'direct': endpoint, 'prefix': self.add_stub('prefix')})
        request = Request(self.gateway + '/v1/chat/completions',
            data=b'{"messages":[{"role":"user","content":"x"}]}',
            headers={'Content-Type': 'application/json', 'X-Decode-Mode': 'direct'})
        response = urlopen(request, timeout=5)
        try:
            self.assertEqual(response.read1(5), b'first')
            self.assertFalse(self.events['binary-done'].is_set())
            self.events['binary-release'].set()
            self.assertEqual(response.read(), b'last')
        finally:
            self.events['binary-release'].set()
            response.close()

    def test_compressed_body_keeps_encoding_header_and_bytes(self):
        original = b'{"backend":"direct"}'
        compressed = gzip.compress(original, mtime=0)
        endpoint = self.add_stub('gzip', raw_body=compressed, content_encoding='gzip',
                                 response_headers={'Content-Language': 'zh', 'Cache-Control': 'no-store'})
        self.start_proxy({'direct': endpoint, 'prefix': self.add_stub('prefix')})
        status, headers, body = self.send(b'{"messages":[{"role":"user","content":"x"}]}', 'direct')
        self.assertEqual(status, 200)
        self.assertEqual(headers['Content-Encoding'], 'gzip')
        self.assertEqual(headers['Content-Language'], 'zh')
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertEqual(body, compressed)
        self.assertEqual(gzip.decompress(body), original)

    def test_truncated_upstream_body_is_not_clean_downstream_eof(self):
        endpoint = self.add_stub('truncated', truncate_response=True)
        self.start_proxy({'direct': endpoint, 'prefix': self.add_stub('prefix')})
        with self.assertRaises(http.client.IncompleteRead):
            self.send(b'{"messages":[{"role":"user","content":"x"}]}', 'direct')
        self.assertEqual(set(self.records), {'truncated'})

    def test_chunked_upstream_and_missing_terminal_chunk(self):
        for broken in (False, True):
            name = 'broken-chunk' if broken else 'valid-chunk'
            endpoint = self.add_stub(name, chunked_response=True, truncate_response=broken)
            self.start_proxy({'direct': endpoint, 'prefix': self.add_stub('prefix')})
            payload = b'{"messages":[{"role":"user","content":"x"}]}'
            if broken:
                with self.assertRaises(http.client.IncompleteRead):
                    self.send(payload, 'direct')
            else:
                status, _, body = self.send(payload, 'direct')
                self.assertEqual(status, 200)
                self.assertEqual(json.loads(body)['backend'], name)

    def test_unframed_upstream_is_rejected(self):
        endpoint = self.add_stub('unframed', unframed=True)
        self.start_proxy({'direct': endpoint, 'prefix': self.add_stub('prefix')})
        status, _, _ = self.send(b'{"messages":[{"role":"user","content":"x"}]}', 'direct')
        self.assertEqual(status, 502)
        self.assertEqual(set(self.records), {'unframed'})
        self.assertEqual(proxy.response_length('0'), 0)
        for value in ('-1', 'bad'):
            with self.assertRaises(http.client.HTTPException):
                proxy.response_length(value)

    def test_global_gate_limits_two_clients_to_one_active_upstream(self):
        self.events['one'] = threading.Event()
        self.events['one-release'] = threading.Event()
        first = self.add_stub('one', delay_event=self.events['one-release'])
        second = self.add_stub('two')
        self.start_proxy({'direct': first, 'prefix': second})
        payload = b'{"messages":[{"role":"user","content":"x"}]}'
        outcomes = []
        def send_mode(mode):
            outcomes.append(self.send(payload, mode)[0])
        clients = [threading.Thread(target=send_mode, args=(mode,)) for mode in ('direct', 'prefix')]
        clients[0].start()
        try:
            self.assertTrue(self.events['one'].wait(3))
            clients[1].start()
            self.assertFalse(self.events['two-entered'].wait(.3))
            self.events['one-release'].set()
            for client in clients:
                client.join(5)
            self.assertEqual(outcomes, [200, 200])
            self.assertEqual(self.max_active, 1)
        finally:
            self.events['one-release'].set()
            for client in clients:
                if client.ident is not None:
                    client.join()


if __name__ == '__main__':
    unittest.main()
