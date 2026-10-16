"""核对来源文件、摘要和失败时的退出行为。"""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import call, patch
from urllib.error import URLError


SCRIPT = Path(__file__).resolve().parents[2] / 'spacemit/bench/qemu-screen/predictor/freeze-sources.py'
SPEC = importlib.util.spec_from_file_location('freeze_sources', SCRIPT)
freeze = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(freeze)

COMMIT = '1' * 40
API = 'https://api.github.com/repos/example/project/commits/v1'
RAW = f'https://raw.githubusercontent.com/example/project/{COMMIT}/'
SOURCES = [('example/project', 'v1', ['README.md', 'LICENSE'])]
ABC_SHA = 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
EMPTY_SHA = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'


class FreezeSourcesTests(unittest.TestCase):
    def test_success_records_exact_files_and_checksums(self):
        responses = [json.dumps({'sha': COMMIT}).encode(), b'abc', b'']
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'sources'
            with patch.object(freeze, 'SOURCES', SOURCES), patch.object(freeze, 'fetch', side_effect=responses) as fetch:
                freeze.main(out)
            self.assertEqual(fetch.call_args_list, [call(API), call(RAW + 'README.md'), call(RAW + 'LICENSE')])
            self.assertEqual((out / 'example--project--README.md').read_bytes(), b'abc')
            self.assertEqual((out / 'example--project--LICENSE').read_bytes(), b'')
            self.assertEqual(json.loads((out / 'sources.json').read_text()), [{
                'repository': 'example/project', 'requested_ref': 'v1', 'commit': COMMIT,
                'files': [
                    {'path': 'README.md', 'url': RAW + 'README.md',
                     'file': 'example--project--README.md', 'sha256': ABC_SHA},
                    {'path': 'LICENSE', 'url': RAW + 'LICENSE',
                     'file': 'example--project--LICENSE', 'sha256': EMPTY_SHA},
                ],
            }])
            metadata_sha = hashlib.sha256((out / 'sources.json').read_bytes()).hexdigest()
            self.assertEqual((out / 'SHA256SUMS').read_text(),
                             f'{EMPTY_SHA}  example--project--LICENSE\n'
                             f'{ABC_SHA}  example--project--README.md\n'
                             f'{metadata_sha}  sources.json\n')

    def test_network_failure_stops_without_a_receipt(self):
        for responses in ([URLError('offline')],
                          [json.dumps({'sha': COMMIT}).encode(), b'abc', URLError('offline')]):
            with self.subTest(responses=responses), tempfile.TemporaryDirectory() as directory:
                out = Path(directory) / 'sources'
                with patch.object(freeze, 'SOURCES', SOURCES), patch.object(freeze, 'fetch', side_effect=responses):
                    with self.assertRaises(URLError):
                        freeze.main(out)
                self.assertFalse((out / 'SHA256SUMS').exists())

    def test_bad_remote_metadata_stops_without_a_receipt(self):
        for response, error in [(b'{', json.JSONDecodeError), (b'{}', KeyError)]:
            with self.subTest(response=response), tempfile.TemporaryDirectory() as directory:
                out = Path(directory) / 'sources'
                with patch.object(freeze, 'SOURCES', SOURCES), patch.object(freeze, 'fetch', return_value=response):
                    with self.assertRaises(error):
                        freeze.main(out)
                self.assertFalse((out / 'SHA256SUMS').exists())

    def test_local_write_failure_stops_without_a_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'sources'
            with patch.object(freeze, 'SOURCES', SOURCES), \
                    patch.object(freeze, 'fetch', side_effect=[json.dumps({'sha': COMMIT}).encode(), b'abc']), \
                    patch.object(Path, 'write_bytes', side_effect=OSError('disk full')):
                with self.assertRaisesRegex(OSError, 'disk full'):
                    freeze.main(out)
            self.assertFalse((out / 'SHA256SUMS').exists())

    def test_existing_output_keeps_its_files(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            receipt = out / 'SHA256SUMS'
            receipt.write_bytes(b'original\n')
            with patch.object(freeze, 'fetch') as fetch:
                with self.assertRaises(FileExistsError):
                    freeze.main(out)
            fetch.assert_not_called()
            self.assertEqual(receipt.read_bytes(), b'original\n')


if __name__ == '__main__':
    unittest.main()
