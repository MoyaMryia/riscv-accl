#!/usr/bin/env python3
"""Check sampled attribution and incomplete-profile rejection without inference."""
import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import Mock

spec = importlib.util.spec_from_file_location('profile', Path(__file__).with_name('profile-k1-prefill.py'))
profile = importlib.util.module_from_spec(spec); spec.loader.exec_module(profile)


def sample(period, names):
    return f'llama-server 123/124 1.234: {period} cpu-clock:u: \n' + ''.join(
        f'\t 123abc {name} (/tmp/libggml-cpu.so)\n' for name in names) + '\n'


class Attribution(unittest.TestCase):
    def test_perf_acknowledgment_with_board_terminator(self):
        for ack in (b'ack\n', b'ack\n\0', b'bad\n'):
            r, w = os.pipe(); ar, aw = os.pipe()
            try:
                os.write(aw, ack)
                proc = Mock(); proc.poll.return_value = None
                if ack == b'bad\n':
                    with self.assertRaises(RuntimeError): profile.control(proc, w, ar, 'enable')
                else:
                    profile.control(proc, w, ar, 'enable')
                    self.assertEqual(os.read(r, 32), b'enable\n')
            finally:
                for fd in (r, w, ar, aw): os.close(fd)

    def test_weights_and_disjoint_groups(self):
        text = (sample(10, ['ggml_vec_dot_f32', 'ggml_compute_forward_gated_delta_net']) +
                sample(20, ['memcpy2d', 'flash_attn_impl']) +
                sample(30, ['ime_gemm', 'compute_mul_mat']) +
                sample(40, ['[unknown]'])) * 25
        s = profile.summarize(text)
        self.assertEqual(s['samples'], 100)
        self.assertEqual(s['cpu_share_pct'], {'recurrent_visible_stack': 10,
                         'attention_visible_stack': 20, 'matmul_visible_stack': 30,
                         'other_or_unattributed': 40})
        self.assertEqual(s['attention_copy_visible_cpu_pct'], 20)
        self.assertEqual(s['unknown_leaf_samples_pct'], 25)
        self.assertEqual(sum(x['cpu_pct'] for x in s['top_self']), 100)

    def test_missing_parents_stay_unattributed(self):
        s = profile.summarize(sample(10, ['ggml_vec_dot_f32']) * 100)
        self.assertEqual(s['cpu_share_pct'], {'other_or_unattributed': 100})
        self.assertEqual(s['multi_frame_samples_pct'], 0)

    def test_empty_and_incomplete_capture_rejected(self):
        for text in ('', sample(10, ['flash_attn_impl']), sample(10, []) * 100,
                     sample(0, ['flash_attn_impl']) * 100):
            with self.assertRaises(ValueError): profile.summarize(text)


if __name__ == '__main__':
    unittest.main()
