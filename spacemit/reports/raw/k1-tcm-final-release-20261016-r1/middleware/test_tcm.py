"""用内存夹具检查接口；这些检查不证明硬件 TCM 可用。"""
from contextlib import nullcontext
import ctypes as C
import os
from pathlib import Path
import threading
import unittest
from unittest.mock import patch
import tcm


class FakeLibrary:
    def __init__(self):
        self.data = C.create_string_buffer(32)
        self.available, self.fake, self.releases = True, False, 0
        self.bad_info, self.no_pointer = False, False

    def spine_tcm_runtime_layout_info(self, output):
        output._obj.blk_size, output._obj.blk_num = 32, 1
        output._obj.is_fake_tcm = self.fake
        return 0

    def spine_tcm_runtime_is_available(self):
        return self.available

    def spine_tcm_runtime_mem_try_wait(self, index, timeout):
        return 0 if self.no_pointer else C.addressof(self.data)

    def spine_tcm_runtime_mem_info(self, index, output):
        output._obj.id, output._obj.va = index, C.addressof(self.data)
        output._obj.size, output._obj.is_acquired = 32, 1
        return -1 if self.bad_info else 0

    def spine_tcm_runtime_mem_release(self, index):
        self.releases += 1
        return 0


class Tests(unittest.TestCase):
    def setUp(self):
        self.lib = FakeLibrary()
        self.runtime = tcm.Runtime.__new__(tcm.Runtime)
        self.runtime.pid, self.runtime.path = os.getpid(), Path('/fixture')
        self.runtime.lib = self.lib
        lock = patch('tcm.common_lock', side_effect=lambda *a, **k: nullcontext())
        lock.start()
        self.addCleanup(lock.stop)

    def lease(self):
        return patch('tcm.real_mapping', return_value='test-fixture-only')

    def test_roundtrip_and_release(self):
        with self.lease(), self.runtime.acquire(0) as block:
            block.write(b'abcd', 28)
            self.assertEqual(block.read(4, 28), b'abcd')
            self.assertEqual(block.read(0, 32), b'')
        self.assertEqual(self.lib.releases, 1)
        with self.assertRaises(tcm.TCMError):
            block.read(1)

    def test_bounds(self):
        with self.lease(), self.runtime.acquire(0) as block:
            for size, offset in ((-1, 0), (33, 0), (1, 32), (1, -1), (1, True)):
                with self.assertRaises(ValueError):
                    block.read(size, offset)
            with self.assertRaises(ValueError):
                block.write(b'abc', 30)
            with self.assertRaises(TypeError):
                block.write('abc')

    def test_no_fake_or_unavailable(self):
        for available, fake in ((True, True), (False, False)):
            self.lib.available, self.lib.fake = available, fake
            with self.assertRaises(tcm.TCMError), self.runtime.acquire(0):
                self.fail('禁止普通内存回退。')
        self.assertEqual(self.lib.releases, 0)

    def test_releases_after_exception(self):
        with self.assertRaisesRegex(ValueError, 'fixture'), self.lease(), self.runtime.acquire(0):
            raise ValueError('fixture')
        self.assertEqual(self.lib.releases, 1)

    def test_bad_metadata_releases(self):
        self.lib.bad_info = True
        with self.assertRaises(tcm.TCMError), self.runtime.acquire(0):
            self.fail('禁止错误元数据。')
        self.assertEqual(self.lib.releases, 1)

    def test_rejects_anonymous_mapping(self):
        with patch('pathlib.Path.read_text', return_value='1000-2000 rw-p 00000000 00:00 0\n'):
            with self.assertRaises(tcm.TCMError):
                tcm.real_mapping(0x1000, 16)
        with self.assertRaises(tcm.TCMError), self.runtime.acquire(0):
            self.fail('夹具不是硬件。')
        self.assertEqual(self.lib.releases, 1)

    def test_requires_complete_device_mapping(self):
        with patch('pathlib.Path.read_text', return_value='1000-2000 rw-s 00000000 00:05 110 /dev/tcm\n'):
            self.assertIn('/dev/tcm', tcm.real_mapping(0x1000, 0x1000))
            with self.assertRaises(tcm.TCMError):
                tcm.real_mapping(0x1000, 0x1001)

    def test_timeout_and_index(self):
        for index, timeout in ((-1, 1), (1, 1), (True, 1), (0, -1), (0, 10000001)):
            with self.assertRaises(ValueError), self.runtime.acquire(index, timeout):
                self.fail('禁止错误范围。')
        self.lib.no_pointer = True
        with self.assertRaises(tcm.TCMError), self.runtime.acquire(0, 0):
            self.fail('没有块。')
        self.assertEqual(self.lib.releases, 0)

    def test_rejects_forked_runtime(self):
        self.runtime.pid += 1
        with self.assertRaises(tcm.TCMError), self.runtime.acquire(0):
            self.fail('必须重新初始化。')

    def test_rejects_other_thread(self):
        errors = []
        with self.lease(), self.runtime.acquire(0) as block:
            def other():
                try:
                    block.read(1)
                except tcm.TCMError as error:
                    errors.append(str(error))
            thread = threading.Thread(target=other)
            thread.start()
            thread.join()
        self.assertEqual(len(errors), 1)


if __name__ == '__main__':
    unittest.main()
