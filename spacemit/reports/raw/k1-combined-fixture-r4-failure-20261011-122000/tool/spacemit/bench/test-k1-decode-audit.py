#!/usr/bin/env python3
"""Verify diagnostic boundaries, worker pairing and incomplete-stream rejection."""
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('audit', Path(__file__).with_name('k1-decode-audit.py'))
audit = importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)


def row(ith, weight, begin, pointer='0x100', activation='ffn_norm-0'):
    return dict(ith=ith, nth=4, weight=weight, activation=activation, input=pointer,
                begin_ns=begin, packing_input_bytes=128, m=1, n=64, k=32,
                buffer_size=0, copy_bytes=0, total_ns=100,
                section_ns=[10, 0, 60, 10, 0], section_calls=[1, 0, 1, 1, 0])


class Checks(unittest.TestCase):
    def test_pair_lifetime_and_crossing_boundary(self):
        rows = []
        for t in (0, 100):
            for i in range(4):
                rows += [row(i, 'blk.0.ffn_gate.weight', t+10+i),
                         row(i, 'blk.0.ffn_up.weight', t+20+i)]
        self.assertEqual(audit.paired_branches(rows, 15)['adjacent_same_input_pairs'], 1)
        self.assertEqual(audit.paired_branches(rows)['adjacent_same_input_pairs'], 2)
        rows[-1]['activation'] = 'different'
        with self.assertRaisesRegex(ValueError, 'identity'):
            audit.paired_branches(rows)

    def test_pointer_reuse_does_not_pair_different_layers(self):
        rows = [r for i in range(4) for r in [row(i, 'blk.0.ffn_gate.weight', 10+i), row(i, 'blk.1.ffn_up.weight', 20+i)]]
        self.assertEqual(audit.paired_branches(rows)['adjacent_same_input_pairs'], 0)
        with self.assertRaisesRegex(ValueError, 'counts'):
            audit.paired_branches(rows[:-1])

    def test_no_overlapping_worker_wall_time_claim(self):
        value = audit.aggregate([row(i, 'head', 10+i) for i in range(4)])
        self.assertEqual(value['worker_elapsed_ns'], 400)
        self.assertAlmostEqual(value['elapsed_fraction']['activation_quantization'], .1)
        self.assertNotIn('wall_time_saving', value)

    def test_startup_probe_is_separate_and_gap_records_rejected(self):
        rows = []
        for i in range(4):
            warm = row(i, 'startup', 10+i); warm['m'] = 2
            pre = row(i, 'prefill', 300+i); pre['m'] = 32
            rows += [warm, pre, row(i, 'blk.0.ffn_gate.weight', 600+i), row(i, 'blk.0.ffn_up.weight', 800+i)]
        req = dict(server_ready_ns=200, request_start_ns=250, first_token_ns=500, request_end_ns=1000)
        result = audit.audit_summary(rows, req)
        self.assertEqual(result['startup_compatibility_probe']['records'], 4)
        self.assertEqual(result['request_only_records'], 12)
        self.assertEqual(result['ffn_pairs']['adjacent_same_input_pairs'], 1)
        warm = rows[0]; warm['begin_ns'] = 205
        with self.assertRaisesRegex(ValueError, 'clock'):
            audit.audit_summary(rows, req)

    def test_reject_prefill_samples_in_decode_recording(self):
        text = 'llama-server 123 11.001000: 5012562 cpu-clock:u:\n\t10 leaf (lib.so)\n'
        window = dict(enable_sent_ns=11_000_000_000, disable_ack_ns=12_000_000_000)
        self.assertEqual(audit.verify_sample_window(text, window)['timed_samples'], 1)
        with self.assertRaisesRegex(ValueError, 'outside'):
            audit.verify_sample_window(text, dict(enable_sent_ns=12_000_000_000, disable_ack_ns=13_000_000_000))

    def test_stale_perf_nul_ack(self):
        class Proc:
            def poll(self): return None
        with patch.object(audit.select, 'select', return_value=([2], [], [])), patch.object(audit.os, 'write'), patch.object(audit.os, 'read', side_effect=[b'\0', b'ack\n\0']):
            audit.perf_control(Proc(), 1, 2, 'disable')

    def test_stream_callback_and_truncation_audit(self):
        def response(count):
            events = [dict(tokens=[i], content='a', stop=False) for i in range(count)]
            events += [dict(stop=True, stop_type='limit', tokens_predicted=count, id_slot=0,
                            timings=dict(cache_n=0, prompt_n=256))]
            return io.BytesIO(b'comment\n'+b''.join(b'data: '+json.dumps(x).encode()+b'\n' for x in events))
        calls = []
        with patch.object(audit.urllib.request, 'urlopen', return_value=response(65)):
            r = audit.stream('http://unused', list(range(256)), lambda: calls.append('first'), lambda: calls.append('final'))
        self.assertEqual(calls, ['first', 'final'])
        self.assertEqual(r['token_ids'], list(range(65)))
        with patch.object(audit.urllib.request, 'urlopen', return_value=response(64)):
            with self.assertRaisesRegex(ValueError, '65-token'):
                audit.stream('http://unused', list(range(256)), lambda: None, lambda: None)


if __name__ == '__main__':
    unittest.main()
