"""验证 GGUF 追加草稿头检查器。"""

import hashlib
import json
import os
import struct
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from model_head_check import compare_models
import diagnostic as base


def _string(value):
    data = value.encode("utf-8")
    return struct.pack("<Q", len(data)) + data


def _fixture(path, with_head, data_change=False, metadata_change=False,
             dims_change=False, truncate=False):
    entries = [("general.alignment", struct.pack("<I", 32)),
               ("test.labels", struct.pack("<I", 8) + struct.pack("<Q", 2)
                + _string("alpha") + _string("beta"))]
    if metadata_change:
        entries[1] = (entries[1][0], entries[1][1][:-1] + b"!")
    kv = b"".join(_string(key) + struct.pack("<I", 4 if key.endswith("alignment") else 9) + value
                   for key, value in entries)
    shared = [("token_embd.weight", (32, 4), 2, 0),
              ("layer.weight", (2,), 0, 96)]
    if dims_change:
        shared[1] = ("layer.weight", (3,), 0, 96)
    head_offset = 128
    tensors = shared + ([ ("blk.1.nextn.shared_head_head.weight", (32, 2), 2, head_offset) ]
                        if with_head else [])
    header = b"GGUF" + struct.pack("<IQQ", 3, len(tensors), len(entries)) + kv
    for name, dims, tensor_type, offset in tensors:
        header += _string(name) + struct.pack("<I", len(dims))
        header += struct.pack("<" + "Q" * len(dims), *dims)
        header += struct.pack("<IQ", tensor_type, offset)
    data_start = (len(header) + 31) // 32 * 32
    header += b"\0" * (data_start - len(header))
    image = bytes(range(128))
    if data_change:
        image = image[:5] + b"X" + image[6:]
    if with_head:
        image += image[:36]
    contents = header + image
    if truncate:
        contents = contents[:-1]
    path.write_bytes(contents)
    return contents


class ModelHeadCheckTests(unittest.TestCase):
    def test_valid_pair_and_full_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            full_path = Path(directory) / "full.gguf"
            prefix_path = Path(directory) / "prefix.gguf"
            full_bytes = _fixture(full_path, False)
            _fixture(prefix_path, True)
            with mock.patch('builtins.open', wraps=open) as opened:
                result = compare_models(full_path, prefix_path)
            self.assertEqual(opened.call_args_list, [mock.call(full_path, 'rb'), mock.call(prefix_path, 'rb')])
            self.assertEqual(result["full_sha256"], hashlib.sha256(full_bytes).hexdigest())
            self.assertEqual(result["full_bytes"], len(full_bytes))
            self.assertEqual(result["shared_tensors"], 2)
            self.assertEqual(result["shared_data_bytes"], 128)
            self.assertEqual(result["prefix_head"], {
                "name": "blk.1.nextn.shared_head_head.weight",
                "shape": (32, 2), "type": 2})
            self.assertEqual(result["vocabulary_rows"], 4)

    def test_entry_identity_gate_rejects_missing_prefix_head_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prefix = root / 'prefix.gguf'
            contents = _fixture(prefix, True)
            expected = hashlib.sha256(contents).hexdigest()
            prefix.write_bytes(contents[:-36])
            helpers = {}
            for name in ('chat', 'quality', 'effective'):
                path = root / (name + '.py')
                path.write_text('# 固定辅助模块。\n')
                helpers[name] = path
            manifest = root / 'manifest.json'
            manifest.write_text(json.dumps({'models': {'2B': {'filename': prefix.name, 'sha256': expected}}}))
            pins = {'diagnostic': base.sha256(Path(base.__file__)),
                    **{name: base.sha256(path) for name, path in helpers.items()}}
            receipt = root / 'tools.json'
            receipt.write_text(json.dumps(pins))
            args = SimpleNamespace(server=Path('/server'), models=root, manifest=manifest,
                                   port=1, tool_receipt=receipt, **helpers)
            digest = base.sha256
            def sha(path):
                return base.SERVER_SHA if path == Path('/server') else digest(path)
            with mock.patch.dict(os.environ, {'K1_PACKAGE_LOCK_FD': '9'}), \
                 mock.patch.object(base.os, 'fstat'), \
                 mock.patch.object(base.subprocess, 'run', return_value=SimpleNamespace(returncode=1)), \
                 mock.patch.object(base.socket, 'socket') as socket, \
                 mock.patch.object(base, 'sha256', side_effect=sha):
                socket.return_value.__enter__.return_value.connect_ex.return_value = 1
                with self.assertRaisesRegex(ValueError, 'model differs from manifest'):
                    base.verify_inputs(args, model_names=('2B',))

    def test_rejects_changed_shared_content(self):
        for options in ({"data_change": True}, {"metadata_change": True},
                        {"dims_change": True}, {"truncate": True}):
            with self.subTest(options=options), tempfile.TemporaryDirectory() as directory:
                full_path = Path(directory) / "full.gguf"
                prefix_path = Path(directory) / "prefix.gguf"
                _fixture(full_path, False, **options)
                _fixture(prefix_path, True)
                with self.assertRaises(ValueError):
                    compare_models(full_path, prefix_path)

    def test_rejects_invalid_external_header(self):
        for change in (lambda b: b'BAD!' + b[4:],
                       lambda b: b[:4] + struct.pack('<I', 4) + b[8:],
                       lambda b: b[:12]):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                full_path = Path(directory) / 'full.gguf'
                prefix_path = Path(directory) / 'prefix.gguf'
                data = _fixture(full_path, False)
                _fixture(prefix_path, True)
                full_path.write_bytes(change(data))
                with self.assertRaises(ValueError):
                    compare_models(full_path, prefix_path)


if __name__ == "__main__":
    unittest.main()
