"""检查成果总账复算脚本会拒绝错误数字。"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / 'tools/verify_results_ledger.py'
LEDGER = ROOT / 'spacemit/reports/results-ledger.json'


def run(*args):
    return subprocess.run([sys.executable, str(TOOL), *args], capture_output=True, text=True)


class ResultsLedgerTests(unittest.TestCase):
    def test_current_ledger_matches_raw_records(self):
        result = run()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith('LEDGER_OK '))

    def test_changed_number_fails_the_recompute(self):
        with tempfile.TemporaryDirectory() as directory:
            damaged = Path(directory) / 'ledger.json'
            data = json.loads(LEDGER.read_text(encoding='utf-8'))
            data['recomputed']['router_e2e']['claims']['wall_change_pct'] = 1.5
            damaged.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
            result = run('--ledger', str(damaged))
        self.assertEqual(result.returncode, 1)
        self.assertIn('LEDGER_MISMATCH', result.stderr)

    def test_missing_raw_record_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            damaged = Path(directory) / 'ledger.json'
            data = json.loads(LEDGER.read_text(encoding='utf-8'))
            data['recomputed']['bert_classifier']['raw'] = 'spacemit/reports/raw/absent/training.json'
            damaged.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
            result = run('--ledger', str(damaged))
        self.assertEqual(result.returncode, 1)
        self.assertIn('missing record', result.stderr)


if __name__ == '__main__':
    unittest.main()
