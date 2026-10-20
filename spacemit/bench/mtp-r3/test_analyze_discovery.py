"""检查发现批次汇总的配对、分组和排除规则。"""
import json
from pathlib import Path
import tempfile
import unittest

import analyze_discovery as analysis


def record(case_id, arm, wall, category='code', verification=None, quality=True):
    return {'case_id': case_id, 'category': category, 'round': 1, 'arm': arm,
            'response': {'wall_s': wall, 'timings': {'predicted_ms': wall * 1000}},
            'quality': {'passed': quality}, 'verification': verification,
            'coverage': {'prefix_fraction': 0.5}, 'fallback_events': []}


def trace(accepted, proposed, restores, steps):
    return {'original_first_accepted': accepted, 'original_proposed': proposed,
            'original_restores': restores, 'original_steps': steps,
            'original_restore_fraction': restores / steps}


class AnalyzeDiscoveryTests(unittest.TestCase):
    def write(self, root, name, outcome, row=None):
        folder = root / 'batch' / 'attempts' / name
        folder.mkdir(parents=True)
        (folder / 'outcome.json').write_text(json.dumps(outcome))
        if row is not None:
            (folder / 'result.json').write_text(json.dumps(row))

    def test_pairing_keeps_failed_quality_and_excludes_incomplete(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, 'a-direct', {'status': 'passed', 'reason': 'complete'}, record('a', 'direct', 10.0))
            self.write(root, 'a-prefix', {'status': 'failed', 'reason': 'quality'},
                       record('a', 'prefix', 8.0, verification=trace(2, 4, 2, 4), quality=False))
            self.write(root, 'a-lowacc', {'status': 'passed', 'reason': 'complete'},
                       record('a', 'lowacc', 9.0, verification=trace(3, 4, 1, 4)))
            self.write(root, 'b-direct', {'status': 'passed', 'reason': 'complete'}, record('b', 'direct', 10.0))
            (root / 'batch/attempts/b-direct/status.json').write_text(
                json.dumps({'status': 'failed', 'reason': 'backend_busy'}))
            self.write(root, 'b-prefix-real', {'status': 'passed', 'reason': 'complete'}, record('b', 'prefix', 9.0))
            self.write(root, 'b-prefix', {'status': 'incomplete', 'reason': 'output_limit'}, record('b', 'prefix', 7.0))
            self.write(root, 'b-lowacc', {'status': 'incomplete', 'reason': 'request_timeout'})
            paired, counts = analysis.load_attempts(root / 'batch')
            self.assertEqual(analysis.triplets(paired), {('a', 1): paired[('a', 1)]})
            self.assertEqual(counts, {'attempts': 7, 'complete': 4, 'incomplete': 2, 'other': 0,
                                      'controller_rejected': 1})
            self.assertNotIn('b', analysis.triplets(paired))

    def test_grouping_uses_metadata_and_reports_exact_slowdown(self):
        cases = [
            {'case_id': 'a', 'category': 'code',
             'metadata': {'family': 'window_sums', 'prompt_language': 'zh', 'doc_mode': 'en'}},
            {'case_id': 'b', 'category': 'long_document', 'metadata': {'material_chars': 2400}},
        ]
        paired = {}
        for case_id, direct, prefix, lowacc in (('a', 10.0, 8.0, 9.0), ('b', 20.0, 25.0, 21.0)):
            arms = {}
            for arm, wall in (('direct', direct), ('prefix', prefix), ('lowacc', lowacc)):
                arms[arm] = record(case_id, arm, wall,
                                   category='code' if case_id == 'a' else 'long_document',
                                   verification=None if arm == 'direct' else trace(2, 4, 2, 4))
            paired[(case_id, 1)] = arms
        summary = analysis.summarize(paired, cases)
        code = summary['groups']['code|window_sums|zh|en']
        self.assertEqual(code['triplets'], 1)
        self.assertAlmostEqual(code['prefix_slowdown_mean_pct'], -20.0)
        self.assertAlmostEqual(code['lowacc_slowdown_mean_pct'], -10.0)
        self.assertEqual(code['arms']['prefix']['acceptance_mean'], 0.5)
        self.assertEqual(code['arms']['prefix']['restore_mean'], 0.5)
        self.assertEqual(summary['groups']['long_document|long||']['prefix_slowdown_mean_pct'], 25.0)

    def test_legacy_control_is_grouped_without_a_plan_entry(self):
        paired = {}
        for arm, wall in (('direct', 10.0), ('prefix', 8.0), ('lowacc', 9.0)):
            paired.setdefault((analysis.LEGACY, 1), {})[arm] = record(
                analysis.LEGACY, arm, wall, verification=None if arm == 'direct' else trace(2, 4, 2, 4))
        summary = analysis.summarize(paired, [])
        group = summary['groups']['code|unicode_runs_control|legacy|none']
        self.assertEqual(group['triplets'], 1)
        self.assertAlmostEqual(group['prefix_slowdown_mean_pct'], -20.0)

    def test_unknown_case_or_empty_triplet_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, 'x-direct', {'status': 'passed', 'reason': 'complete'}, record('x', 'direct', 1.0))
            paired, _ = analysis.load_attempts(root / 'batch')
            self.assertEqual(analysis.triplets(paired), {})
            with self.assertRaisesRegex(ValueError, 'frozen plan'):
                analysis.summarize({('missing', 1): {arm: record('missing', arm, 1.0) for arm in analysis.ARMS}},
                                   [])


if __name__ == '__main__':
    unittest.main()
