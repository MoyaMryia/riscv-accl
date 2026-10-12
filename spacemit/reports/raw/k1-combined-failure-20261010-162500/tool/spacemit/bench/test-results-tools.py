#!/usr/bin/env python3
"""Exercise archived matrix verification and confidence-interval regressions."""

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / 'reports/raw/2026-09-25-lifecycle'
REPORT = HERE.parent / 'reports/2026-09-27-resumed-measures.md'


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VERIFY = load('matrix_verifier', 'verify-results-matrix.py')
STATS = load('launch_statistics', 'paired-stats.py')


class MatrixChecks(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='results-tools-')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.raw = self.root / 'raw'; self.raw.mkdir()
        for filename in VERIFY.FILES:
            shutil.copyfile(RAW / filename, self.raw / filename)
        self.report = self.root / 'report.md'
        shutil.copyfile(REPORT, self.report)

    def verify(self):
        return subprocess.run([sys.executable, str(HERE / 'verify-results-matrix.py'),
                               str(self.report), str(self.raw)], capture_output=True, text=True,
                              env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))

    def mutate(self, field, value, filename='lifecycle-rvv32.jsonl', label_filter=None):
        path = self.raw / filename
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        for row in rows:
            if row.get('kind') == 'measurement' and (label_filter is None or label_filter in row['label']):
                for result in row['results']:
                    result[field] = value
        path.write_text('\n'.join(json.dumps(row) for row in rows) + '\n')

    def test_original_archive_including_complete_single_arm_passes(self):
        result = self.verify()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('rows checked: 21', result.stdout)

    def test_different_rvv_arm_hashes_fail(self):
        self.mutate('tokens_sha256', 'f' * 64, label_filter='-rvv32-1-')
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('differ across comparison arms', result.stdout)

    def test_missing_token_hashes_fail(self):
        self.mutate('tokens_sha256', None)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('missing/invalid=True', result.stdout)

    def test_missing_text_hashes_fail(self):
        self.mutate('sha256', None)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('missing/invalid=True', result.stdout)

    def test_different_rvv_text_hashes_fail(self):
        self.mutate('sha256', 'f' * 64, label_filter='-rvv32-1-')
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('differ across comparison arms', result.stdout)

    def test_different_weight_format_hashes_fail(self):
        self.mutate('tokens_sha256', 'f' * 64, 'lifecycle-weight-compare-2k.jsonl', '2B-Q8_0-')
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('differ across comparison arms', result.stdout)

    def test_missing_comparison_partner_fails(self):
        lines = self.report.read_text().splitlines()
        self.report.write_text('\n'.join(line for line in lines
                                        if not line.startswith('| 2B | R | 2,048 | 1 |')) + '\n')
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Exact requires both distinct comparison arms', result.stdout)

    def test_single_complete_arm_cannot_be_relabelled_exact(self):
        self.report.write_text(self.report.read_text().replace('Complete; one arm', 'Exact; one arm'))
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Exact requires both distinct comparison arms', result.stdout)


class StatisticsChecks(unittest.TestCase):
    def test_critical_values_keep_fractional_and_boundary_degrees_of_freedom(self):
        # Reference quantiles, including the fractional df from the archived M4 pair.
        for df, expected in [(1, 12.7062047364), (11, 2.2009851601),
                             (30, 2.0422724563), (1.31198415453, 7.3858641274)]:
            with self.subTest(df=df):
                self.assertAlmostEqual(STATS.t_critical(df), expected, places=7)

    def test_invalid_degrees_of_freedom_are_rejected(self):
        for df in [0, -1, float('nan'), float('inf')]:
            with self.subTest(df=df), self.assertRaises(ValueError):
                STATS.t_critical(df)

    def test_archived_m4_interval_uses_fractional_welch_quantile(self):
        raw = HERE.parent / 'reports/raw/2026-09-24-integrated'
        result = subprocess.run([
            sys.executable, str(HERE / 'paired-stats.py'),
            str(raw / 'codex-q4-scale-base-1.jsonl'), str(raw / 'codex-q4-scale-base-4.jsonl'),
            '--candidate', str(raw / 'codex-q4-scale-scale-2.jsonl'),
            str(raw / 'codex-q4-scale-scale-3.jsonl'), '--select', 'n_prompt=128'],
            capture_output=True, text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('[0.0947, 0.5109]', result.stdout)


if __name__ == '__main__':
    unittest.main()
