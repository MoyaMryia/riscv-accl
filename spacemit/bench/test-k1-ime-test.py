#!/usr/bin/env python3
"""Check isolated build recipes and representative GGUF dimension handling."""
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('ime_test', HERE / 'k1-ime-test.py')
ime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ime)


class Isolation(unittest.TestCase):
    def test_compile_preserves_target_and_changes_only_source_output_dependencies(self):
        old = '/tool/g++ -DIME1 -I/include -O3 -march=rv64gcv -fPIC -MD -MT old.o -MF old.d -o old.o -c /old.cpp'
        self.assertEqual(ime.compile_argv(old, Path('/new.cpp'), Path('/new.o'), Path('/kernel')),
                         ['/tool/g++', '-DIME1', '-I/include', '-O3', '-march=rv64gcv', '-fPIC',
                          '-I/kernel', '-o', '/new.o', '-c', '/new.cpp'])

    def test_link_requires_exactly_one_replacement(self):
        old = ': && /tool/g++ -shared -Wl,-soname,libggml-cpu.so.0 untouched.o cpu/spacemit/ime1_kernels.cpp.o -o bin/libggml-cpu.so /base.so && :'
        result = ime.link_argv(old, Path('/new.so'), Path('/new.o'))
        self.assertIn('untouched.o', result)
        self.assertIn('/base.so', result)
        self.assertIn('-Wl,-soname,libggml-cpu.so.0', result)
        self.assertIn('/new.o', result)
        self.assertEqual(result[result.index('-o')+1], '/new.so')
        for bad in (old.replace('cpu/spacemit/ime1_kernels.cpp.o', 'other.o'),
                    old.replace('untouched.o', 'extra/spacemit/ime1_kernels.cpp.o'),
                    old.replace(': && ', '')):
            with self.assertRaises(ValueError): ime.link_argv(bad, Path('/new.so'), Path('/new.o'))

    def test_model_shapes_skip_vocabulary_and_reject_invalid_dimension(self):
        def string(value):
            data = value.encode()
            return struct.pack('<Q', len(data)) + data
        def gguf(ff):
            entries = [('tokenizer.ggml.tokens', 9, struct.pack('<IQ', 8, 2) + string('a') + string('b')),
                       ('qwen35.embedding_length', 4, struct.pack('<I', 2560)),
                       ('qwen35.feed_forward_length', 4, struct.pack('<I', ff))]
            return b'GGUF' + struct.pack('<IQQ', 3, 0, len(entries)) + b''.join(
                string(key) + struct.pack('<I', kind) + value for key, kind, value in entries)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'model.gguf'
            path.write_bytes(gguf(9216))
            self.assertEqual(ime.dimensions(path), {'embedding_length':2560, 'feed_forward_length':9216})
            for bad in (gguf(0), gguf(9217), gguf(9216)[:-1]):
                path.write_bytes(bad)
                with self.assertRaises(ValueError): ime.dimensions(path)


if __name__ == '__main__':
    unittest.main()
