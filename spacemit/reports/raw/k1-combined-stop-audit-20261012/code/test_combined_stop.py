#!/usr/bin/env python3
"""核验真实停止记录和独立分派修订的拒绝条件。"""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE/file)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


AUDIT = module('stop_audit', 'audit-combined-stop.py')
REVISION = module('dispatch_revision', 'prepare-combined-dispatch-r2.py')


class StopReview(unittest.TestCase):
    def setUp(self):
        self.source = REPO/'lab/k1-combined-stop-audit-20261012/input/cold-round-1'
        if not self.source.is_dir():
            self.skipTest('fixed request evidence is absent')
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for file in self.source.iterdir():
            (self.root/file.name).symlink_to(file)

    def alter(self, name, change):
        path = self.root/name
        data = [json.loads(line) for line in path.read_text().splitlines()]
        change(data)
        path.unlink()
        path.write_text('\n'.join(json.dumps(row) for row in data)+'\n')

    def test_real_stop(self):
        result = AUDIT.audit(self.root)
        self.assertEqual(result['verified_requests'], 96)
        self.assertEqual(result['verified_comparisons'], 48)
        self.assertEqual(len(result['failures']), 1)
        self.assertEqual(result['failures'][0]['reference'], 'B')

    def test_cached_request_is_rejected(self):
        def change(rows):
            next(row for row in rows if row.get('kind') == 'measurement')['results'][0]['timings']['cache_n'] = 1
        self.alter('2B-p512-n1-C0-0.jsonl', change)
        with self.assertRaisesRegex(ValueError, 'cache or prompt'):
            AUDIT.audit(self.root)

    def test_changed_output_is_rejected(self):
        def change(rows):
            value = next(row for row in rows if row.get('kind') == 'measurement')['results'][0]
            value['token_ids'][0] += 1
            value['tokens_sha256'] = AUDIT.digest(value['token_ids'])
        self.alter('2B-p512-n1-C0-0.jsonl', change)
        with self.assertRaisesRegex(ValueError, 'paired tokens'):
            AUDIT.audit(self.root)


class DispatchReview(unittest.TestCase):
    def test_actual_expressions_match(self):
        text = '''#include <cstdio>
static int calls = 0, enabled = 0, vl = 0;
static bool spine_k1_flag(const char *) { ++calls; return enabled; }
static int __riscv_vsetvlmax_e32m8() { return vl; }
int main() {
    int cases = 0, saved = 0;
    for (int n_tokens : {0, 1, 2, 8, 32})
    for (int S_v : {64, 128, 256})
    for (int width : {32, 64, 128})
    for (int flag : {0, 1}) {
        enabled = flag; vl = width; calls = 0;
        bool before = OLD;
        int old_calls = calls; calls = 0;
        bool after = NEW;
        if (before != after) return 1;
        if (n_tokens <= 1 && calls != 0) return 2;
        saved += old_calls - calls; ++cases;
    }
    std::printf("PASS: %d dispatch cases; %d flag reads removed\\n", cases, saved);
}
'''.replace('OLD', REVISION.OLD).replace('NEW', REVISION.NEW)
        text = '#include <initializer_list>\n'+text
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            (root/'test.cpp').write_text(text)
            subprocess.run(['g++', '-std=c++17', '-O2', str(root/'test.cpp'), '-o', str(root/'test')], check=True)
            result = subprocess.run([str(root/'test')], check=True, capture_output=True, text=True)
            self.assertIn('PASS: 90 dispatch cases', result.stdout)


if __name__ == '__main__':
    unittest.main()
