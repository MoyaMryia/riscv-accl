"""检查代码答案重评的读取、跳过和差异记录。"""
import json
from pathlib import Path
import tempfile
import unittest

import rescore_discovery


class RescoreTests(unittest.TestCase):
    def write(self, root, name, outcome, row, answer='def f():\n    return 1\n'):
        folder = root / 'batch' / 'attempts' / name
        folder.mkdir(parents=True)
        (folder / 'outcome.json').write_text(json.dumps(outcome))
        (folder / 'result.json').write_text(json.dumps(row))
        (folder / 'answer.txt').write_text(answer)

    def test_only_completed_code_attempts_are_rescored(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, 'a-code', {'status': 'failed', 'reason': 'quality'},
                       {'case_id': 'c1', 'category': 'code', 'arm': 'direct', 'quality': {'passed': False}})
            self.write(root, 'b-truncated', {'status': 'incomplete', 'reason': 'output_limit'},
                       {'case_id': 'c1', 'category': 'code', 'arm': 'prefix', 'quality': {'passed': False}})
            self.write(root, 'c-text', {'status': 'passed', 'reason': 'complete'},
                       {'case_id': 't1', 'category': 'chinese', 'arm': 'direct', 'quality': {'passed': None}})
            self.write(root, 'd-legacy', {'status': 'passed', 'reason': 'complete'},
                       {'case_id': 'legacy_unicode_runs', 'category': 'code', 'arm': 'direct',
                        'quality': {'passed': True}})
            (root / 'cases.json').write_text(json.dumps([
                {'case_id': 'c1', 'category': 'code', 'code_task': 'f', 'messages': []}]))
            assessment = root / 'assess.py'
            assessment.write_text(
                'def assess(case, answer, quality):\n'
                '    passed = "return 1" in answer\n'
                '    return {"passed": passed, "result": {"checks": 6, "detail": "fixed"}}\n'
                'def check_code(task, answer):\n'
                '    return {"pass": "return 1" in answer, "checks": 106}\n')
            output = root / 'out'
            rescore_discovery.main(['--batch', str(root / 'batch'), '--cases', str(root / 'cases.json'),
                                    '--assessment', str(assessment), '--quality', str(assessment),
                                    '--output', str(output)])
            summary = json.loads((output / 'rescore.json').read_text())
            self.assertEqual(summary['records'], 2)
            self.assertEqual(summary['skipped_attempts'], 2)
            self.assertEqual(summary['original_failures'], 1)
            self.assertEqual(summary['rescored_failures'], 0)
            self.assertEqual(summary['changes'][0]['attempt'], 'a-code')
            self.assertEqual(summary['changes'][0]['checks'], 6)
            legacy = [row for row in summary['rows'] if row['kind'] == 'legacy_control']
            self.assertEqual(len(legacy), 1)
            self.assertEqual(legacy[0]['checks'], 106)

    def test_unknown_case_stops_the_rerun(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, 'a-code', {'status': 'passed', 'reason': 'complete'},
                       {'case_id': 'missing', 'category': 'code', 'arm': 'direct', 'quality': {'passed': True}})
            (root / 'cases.json').write_text('[]')
            assessment = root / 'assess.py'
            assessment.write_text('def assess(*args):\n    return {"passed": True, "result": {}}\n')
            with self.assertRaisesRegex(ValueError, 'frozen plan'):
                rescore_discovery.main(['--batch', str(root / 'batch'), '--cases', str(root / 'cases.json'),
                                        '--assessment', str(assessment), '--quality', str(assessment),
                                        '--output', str(root / 'out')])


if __name__ == '__main__':
    unittest.main()
