"""提供真实 TCM 块的用户态访问接口，不提供普通内存回退。"""
import argparse
from contextlib import contextmanager
import ctypes as C
import fcntl
import json
import os
from pathlib import Path
import threading
import time


LOCK = Path.home() / 'Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock'


class TCMError(RuntimeError):
    """记录设备、运行库、块所有权或访问范围错误。"""


class Layout(C.Structure):
    _fields_ = [('blk_size', C.c_size_t), ('blk_num', C.c_size_t), ('is_fake_tcm', C.c_int)]


class BlockInfo(C.Structure):
    _fields_ = [('id', C.c_int), ('va', C.c_void_p), ('size', C.c_size_t),
                ('phys_addr', C.c_uint64), ('cpu_affinity_mask', C.c_uint64),
                ('owner_tid', C.c_int), ('is_acquired', C.c_int)]


@contextmanager
def common_lock(timeout=5.0):
    """取得固定共用锁；允许复用当前进程继承的同一把锁。"""
    if timeout < 0:
        raise ValueError('等待时间不能小于 0。')
    try:
        inherited = (os.environ.get('K1_PACKAGE_LOCK_FD') == '9'
                     and os.fstat(9).st_ino == LOCK.stat().st_ino
                     and os.fstat(9).st_dev == LOCK.stat().st_dev
                     and 'FLOCK  ADVISORY  WRITE' in Path('/proc/self/fdinfo/9').read_text())
    except OSError:
        inherited = False
    if inherited:
        yield
        return
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with LOCK.open('a') as handle:
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise TCMError('共用锁正在使用，未访问 TCM。') from None
                time.sleep(0.05)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def device_status():
    result = {}
    for name in ('/dev/tcm', '/dev/tcm_sync_mem'):
        path = Path(name)
        item = {'exists': path.exists(), 'readable': os.access(path, os.R_OK),
                'writable': os.access(path, os.W_OK)}
        if path.exists():
            st = path.stat()
            item.update(mode=oct(st.st_mode & 0o777), uid=st.st_uid, gid=st.st_gid)
        result[name] = item
    return result


def real_mapping(address, size):
    """要求整个块位于当前进程的可读写 /dev/tcm 映射内。"""
    for line in Path('/proc/self/maps').read_text().splitlines():
        fields = line.split(maxsplit=5)
        start, end = (int(value, 16) for value in fields[0].split('-'))
        if (start <= address and address + size <= end and fields[1].startswith('rw')
                and len(fields) == 6 and fields[5] == '/dev/tcm'):
            return line
    raise TCMError('块没有完整的可读写 /dev/tcm 映射，拒绝访问。')


class Runtime:
    """封装固定厂商 ABI；对象不能跨进程复用。"""
    def __init__(self, library):
        self.path = Path(library).resolve(strict=True)
        self.pid = os.getpid()
        with common_lock():
            self.lib = C.CDLL(str(self.path), mode=C.RTLD_GLOBAL)
            specs = {'version': (C.c_char_p, []), 'is_available': (C.c_int, []),
                     'layout_info': (C.c_int, [C.POINTER(Layout)]),
                     'mem_info': (C.c_int, [C.c_int, C.POINTER(BlockInfo)]),
                     'mem_try_wait': (C.c_void_p, [C.c_int, C.c_size_t]),
                     'mem_release': (C.c_int, [C.c_int])}
            for name, (restype, argtypes) in specs.items():
                fn = getattr(self.lib, 'spine_tcm_runtime_' + name)
                fn.restype, fn.argtypes = restype, argtypes

    def _process(self):
        if os.getpid() != self.pid:
            raise TCMError('对象来自其他进程，必须重新创建运行库对象。')

    def status(self):
        self._process()
        with common_lock():
            layout = Layout()
            code = self.lib.spine_tcm_runtime_layout_info(C.byref(layout))
            return {'library': str(self.path), 'uid': os.getuid(), 'pid': self.pid,
                    'version': self.lib.spine_tcm_runtime_version().decode(),
                    'available': bool(self.lib.spine_tcm_runtime_is_available()),
                    'layout_status': code, 'block_size': layout.blk_size,
                    'block_count': layout.blk_num, 'fake': bool(layout.is_fake_tcm),
                    'devices': device_status()}

    @contextmanager
    def acquire(self, block_id, timeout_us=1000000):
        """按厂商交接协议申请一块真实 TCM，并在退出时释放。"""
        self._process()
        if type(block_id) is not int or type(timeout_us) is not int or not 0 <= timeout_us <= 10000000:
            raise ValueError('块编号必须是整数，等待时间必须在 0～10000000 微秒内。')
        with common_lock():
            layout = Layout()
            if (self.lib.spine_tcm_runtime_layout_info(C.byref(layout)) != 0
                    or not self.lib.spine_tcm_runtime_is_available() or layout.is_fake_tcm
                    or layout.blk_size == 0):
                raise TCMError('真实 TCM 不可用，拒绝普通内存回退。请检查设备权限和运行库。')
            if not 0 <= block_id < layout.blk_num:
                raise ValueError('块编号超出运行库报告的范围。')
            address = self.lib.spine_tcm_runtime_mem_try_wait(block_id, timeout_us)
            if not address:
                raise TCMError('块申请失败或超时。')
            block = None
            try:
                info = BlockInfo()
                if (self.lib.spine_tcm_runtime_mem_info(block_id, C.byref(info)) != 0
                        or info.id != block_id or info.va != address
                        or not 0 < info.size <= layout.blk_size or not info.is_acquired):
                    raise TCMError('块元数据与申请结果不一致，拒绝访问。')
                real_mapping(address, info.size)
                block = Block(address, info.size)
                yield block
            finally:
                if block is not None:
                    block.active = False
                code = self.lib.spine_tcm_runtime_mem_release(block_id)
                if code != 0:
                    raise TCMError('块释放失败，状态码为 ' + str(code))


class Block:
    """限制读写范围及调用线程；不向调用方提供裸指针。"""
    def __init__(self, address, size):
        self._address, self.size = address, size
        self._owner = (os.getpid(), threading.get_ident())
        self.active = True

    def _range(self, offset, size):
        if not self.active or self._owner != (os.getpid(), threading.get_ident()):
            raise TCMError('块已释放或调用线程不拥有此块。')
        if type(offset) is not int or type(size) is not int or not 0 <= offset <= self.size or not 0 <= size <= self.size - offset:
            raise ValueError('读写范围超出块边界。')

    def read(self, size, offset=0):
        self._range(offset, size)
        return C.string_at(self._address + offset, size)

    def write(self, data, offset=0):
        if not isinstance(data, bytes):
            raise TypeError('写入内容必须是 bytes。')
        self._range(offset, len(data))
        C.memmove(self._address + offset, data, len(data))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library', type=Path, default=Path.home() / 'Projects/llm-bench/.toolchain/spine-tcm/libspine_tcm.so.3.0.1')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('status')
    read = sub.add_parser('read')
    read.add_argument('block', type=int)
    read.add_argument('--size', type=int, default=16)
    read.add_argument('--offset', type=int, default=0)
    args = parser.parse_args()
    try:
        if not os.environ.get('TMUX'):
            raise TCMError('命令行检查必须在 tmux 中执行。')
        runtime = Runtime(args.library)
        if args.command == 'status':
            result = runtime.status()
        else:
            with runtime.acquire(args.block) as block:
                result = {'block': args.block, 'offset': args.offset, 'size': args.size,
                          'hex': block.read(args.size, args.offset).hex(), 'backend': 'real-tcm'}
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (TCMError, OSError, ValueError, AttributeError) as error:
        parser.exit(2, str(error) + '\n')


if __name__ == '__main__':
    main()
