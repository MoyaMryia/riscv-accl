#!/usr/bin/env python3
"""检查归档仅在完成后可见，且完整归档保留已有文件。"""
import tempfile
from pathlib import Path
import unittest

import archive


class ArchiveTests(unittest.TestCase):
    def test_failure_keeps_partial_file_unpublished(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)/'batch'
            root.mkdir()
            target = Path(directory)/'board.tar.gz'
            def fail(handle):
                handle.write(b'partial')
                self.assertFalse(target.exists())
                raise RuntimeError('interruption')
            with self.assertRaises(RuntimeError):
                archive.publish(root, target, fail)
            self.assertFalse(target.exists())
            self.assertTrue(target.with_name(target.name+'.partial').exists())

    def test_complete_file_is_published_once(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)/'batch'
            root.mkdir()
            target = Path(directory)/'board.tar.gz'
            def build(handle):
                self.assertFalse(target.exists())
                handle.write(b'complete')
            value = archive.publish(root, target, build)
            self.assertEqual(value['bytes'], 8)
            self.assertEqual(target.read_bytes(), b'complete')
            self.assertFalse(target.with_name(target.name+'.partial').exists())
            with self.assertRaises(FileExistsError):
                archive.publish(root, target, build)


if __name__ == '__main__':
    unittest.main()
