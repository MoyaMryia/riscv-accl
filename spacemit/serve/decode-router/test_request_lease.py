"""检查服务请求与诊断请求的互斥边界。"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.request

import request_lease


class RequestLeaseTests(unittest.TestCase):
    def test_post_waits_for_diagnostic_lease_then_returns_numeric_result(self):
        arrived = threading.Event()
        entered = threading.Event()
        results = []
        class Handler(BaseHTTPRequestHandler):
            def setup(self):
                super().setup()
                arrived.set()
            def do_POST(self):
                entered.set()
                self.rfile.read(int(self.headers['Content-Length']))
                self.send_response(200)
                self.send_header('Content-Length', '1')
                self.end_headers()
                self.wfile.write(b'7')
            def log_message(self, *args): pass
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'request.lock'
            server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
            request_lease.install(server, path)
            loop = threading.Thread(target=server.serve_forever)
            loop.start()
            def client():
                req = urllib.request.Request(f'http://127.0.0.1:{server.server_port}/', data=b'{}')
                with urllib.request.urlopen(req, timeout=5) as response:
                    results.append((response.status, int(response.read())))
            try:
                with request_lease.acquire(path):
                    thread = threading.Thread(target=client)
                    thread.start()
                    self.assertTrue(arrived.wait(2))
                    self.assertFalse(entered.is_set())
                thread.join(5)
                self.assertFalse(thread.is_alive())
                self.assertTrue(entered.is_set())
                self.assertEqual(results, [(200, 7)])
            finally:
                server.shutdown()
                loop.join(5)
                server.server_close()


if __name__ == '__main__':
    unittest.main()
