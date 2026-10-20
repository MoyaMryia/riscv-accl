"""让交互请求与诊断请求共用逐请求文件锁。"""
from contextlib import contextmanager
import fcntl


@contextmanager
def acquire(path):
    with path.open('a') as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        yield


def install(server, path):
    parent = server.RequestHandlerClass

    class LeasedHandler(parent):
        def do_POST(self):
            with acquire(path):
                super().do_POST()

    server.RequestHandlerClass = LeasedHandler
