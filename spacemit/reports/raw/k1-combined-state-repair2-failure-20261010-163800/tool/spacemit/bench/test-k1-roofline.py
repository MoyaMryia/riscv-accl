#!/usr/bin/env python3
"""Check traffic accounting and rejection of incomplete bandwidth/timing evidence."""
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('roofline', HERE / 'k1-roofline.py')
roof = importlib.util.module_from_spec(spec); spec.loader.exec_module(roof)


def string(value):
    data = value.encode(); return struct.pack('<Q', len(data)) + data


def fixture(path, untied=False):
    meta = {'general.architecture': 'qwen35', 'qwen35.block_count': 2,
            'qwen35.nextn_predict_layers': 1, 'qwen35.attention.head_count_kv': 1,
            'qwen35.attention.key_length': 16, 'qwen35.attention.value_length': 16}
    tensors = [('blk.0.attn_q.weight', [32], 2), ('blk.0.attn_k_norm.weight', [16], 0),
               ('blk.1.nextn.eh_proj.weight', [32], 2), ('token_embd.weight', [32, 8], 2),
               ('output_norm.weight', [32], 0)]
    if untied:
        tensors.append(('output.weight', [32, 16], 2))
    data = b'GGUF' + struct.pack('<IQQ', 3, len(tensors), len(meta))
    for key, value in meta.items():
        data += string(key)
        data += struct.pack('<I', 8 if isinstance(value, str) else 4)
        data += string(value) if isinstance(value, str) else struct.pack('<I', value)
    for name, dims, kind in tensors:
        data += string(name) + struct.pack('<I', len(dims))
        data += b''.join(struct.pack('<Q', d) for d in dims) + struct.pack('<IQ', kind, 0)
    path.write_bytes(data + bytes(4096))


def memory_rows():
    return [dict(cpus='0,1,2,3', buffer_bytes=size * 1024**2, stage=stage,
                 round=repeat, validated=True, kernel='rvv_full_read', GB_per_s=6.0)
            for size in (256, 1024, 2304) for stage in ('before', 'after') for repeat in range(5)]


class RooflineTests(unittest.TestCase):
    def test_tied_head_and_draft_accounting(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'model.gguf'; fixture(path)
            result = roof.model_traffic(path)
            self.assertEqual(result['main_weight_read_proxy_bytes'], 18 + 64 + 144 + 128)
            self.assertEqual(result['mtp_draft_tensor_bytes'], 18)
            self.assertEqual(result['f16_kv_bytes_per_context_token'], 64)
            self.assertEqual(result['main_layers'], 1)

    def test_untied_head_does_not_stream_input_embedding_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'model.gguf'; fixture(path, untied=True)
            result = roof.model_traffic(path)
            self.assertEqual(result['main_weight_read_proxy_bytes'], 18 + 64 + 288 + 128)
            self.assertEqual(result['output_head'], 'output.weight')

    def test_truncated_header_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'model.gguf'; path.write_bytes(b'GGUF')
            with self.assertRaises(ValueError): roof.model_traffic(path)

    def test_incomplete_and_scalar_bandwidth_rejected(self):
        rows = memory_rows()
        self.assertEqual(roof.bandwidth_groups(rows)['1024']['median_GB_per_s'], 6.0)
        with self.assertRaises(ValueError): roof.bandwidth_groups(rows[:-1])
        duplicated = rows[:-1] + [rows[-2]]
        with self.assertRaises(ValueError): roof.bandwidth_groups(duplicated)
        rows[0]['kernel'] = 'host_full_read'
        with self.assertRaises(ValueError): roof.bandwidth_groups(rows)

    def test_roof_units_and_mismatched_output_rejected(self):
        traffic = {model: {'main_weight_read_proxy_bytes': 2e9, 'f16_kv_bytes_per_context_token': 1024}
                   for model in ('2B', '4B')}
        rows = [dict(model=model, context=context, route=route, repeat=repeat,
                     prompt_sha256='prompt', tokens_sha256='tokens', text_sha256='text',
                     decode_tps=2.0 if route == 0 else 2.5, prompt_tps=20, ttft_s=10)
                for model in ('2B', '4B') for context in (256, 2048)
                for route in (0, 3) for repeat in range(3)]
        result = roof.comparisons(rows, traffic, memory_rows())['comparisons'][0]
        self.assertEqual(result['weight_only_roof_tps'], 3.0)
        self.assertEqual(result['decode_throughput_gain_pct'], 25.0)
        self.assertAlmostEqual(result['arms']['3']['weight_only_streaming_ratio'], 2.5 / 3)
        rows[0]['tokens_sha256'] = 'different'
        with self.assertRaises(ValueError): roof.comparisons(rows, traffic, memory_rows())


if __name__ == '__main__':
    unittest.main()
