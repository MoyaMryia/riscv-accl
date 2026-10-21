#!/usr/bin/env python3
"""核验打包工具的身份记录、成员核对与覆盖保护。"""

import hashlib
import importlib.util
import json
import tarfile
import tempfile
import unittest
from pathlib import Path


SPEC = importlib.util.spec_from_file_location('package_artifact', Path(__file__).with_name('package-artifact.py'))
PACKAGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGE)


class PackTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.gguf = self.root / 'model.gguf'
        self.gguf.write_bytes(b'GGUF' + bytes(range(64)))
        self.receipts = self.root / 'receipts'
        (self.receipts / 'nested').mkdir(parents=True)
        (self.receipts / 'input-receipt.json').write_text('{"a": 1}')
        (self.receipts / 'nested' / 'output-receipt.json').write_text('{"b": 2}')
        self.output = self.root / 'out'

    def digest(self, path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    def test_package_records_every_member(self):
        archive, receipt_path = PACKAGE.pack(self.gguf, self.receipts, 'demo', self.output)
        receipt = json.loads(receipt_path.read_text())
        self.assertEqual(receipt['artifact_sha256'], self.digest(self.gguf))
        self.assertEqual(receipt['archive_sha256'], self.digest(archive))
        self.assertEqual(receipt['members'], 4)
        with tarfile.open(archive, 'r:gz') as tar:
            names = sorted(tar.getnames())
        self.assertEqual(names, ['demo.manifest.json', 'model/model.gguf',
                                 'receipts/input-receipt.json',
                                 'receipts/nested/output-receipt.json'])

    def test_manifest_hashes_match_sources(self):
        archive, _ = PACKAGE.pack(self.gguf, self.receipts, 'demo', self.output)
        manifest = json.loads((self.output / 'demo.manifest.json').read_text())
        digests = {item['path']: item['sha256'] for item in manifest['files']}
        self.assertEqual(digests['model/model.gguf'], self.digest(self.gguf))
        self.assertEqual(digests['receipts/input-receipt.json'],
                         self.digest(self.receipts / 'input-receipt.json'))
        with tarfile.open(archive, 'r:gz') as tar:
            self.assertEqual(tar.getmember('model/model.gguf').mtime, 0)

    def test_existing_output_is_refused(self):
        PACKAGE.pack(self.gguf, self.receipts, 'demo', self.output)
        with self.assertRaises(ValueError):
            PACKAGE.pack(self.gguf, self.receipts, 'demo', self.output)

    def test_wrong_expected_digest_is_refused(self):
        with self.assertRaises(ValueError):
            PACKAGE.pack(self.gguf, self.receipts, 'demo', self.output,
                         expect_sha256='0' * 64)
        self.assertFalse((self.output / 'demo.tar.gz').exists())

    def test_missing_receipts_are_refused(self):
        with self.assertRaises(ValueError):
            PACKAGE.pack(self.gguf, self.root / 'absent', 'demo', self.output)

    def test_invalid_name_is_refused(self):
        with self.assertRaises(ValueError):
            PACKAGE.pack(self.gguf, self.receipts, '../escape', self.output)


if __name__ == '__main__':
    unittest.main()
