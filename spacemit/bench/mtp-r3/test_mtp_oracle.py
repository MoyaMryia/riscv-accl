"""检查 MTP 路由 oracle 的配对、家族门槛与聚类区间。"""
import json
from pathlib import Path
import tempfile
import unittest

import mtp_oracle


def rows():
    data = []
    walls = {('a', 'direct'): 10.0, ('a', 'prefix'): 8.0,
             ('b', 'direct'): 10.0, ('b', 'prefix'): 9.0,
             ('c', 'direct'): 10.0, ('c', 'prefix'): 12.0}
    for (case, arm), wall in walls.items():
        data.append({'case_id': case, 'round': 1, 'category': 'code', 'arm': arm,
                     'wall_s': wall, 'response': {'wall_s': wall}})
    return data


class OracleTests(unittest.TestCase):
    def test_per_request_and_family_oracle(self):
        selected = mtp_oracle.pairs(rows())
        for direct, _mtp in selected:
            direct['family'] = 'f1' if direct['case_id'] in ('a', 'b') else 'f2'
        result = mtp_oracle.summarize(selected, 3.0, 200, 1)
        self.assertAlmostEqual(result['per_request_oracle_pct'], 10.0)
        self.assertAlmostEqual(result['families']['f1']['oracle_gain_pct'], 15.0)
        self.assertAlmostEqual(result['families']['f2']['oracle_gain_pct'], 0.0)
        self.assertEqual(result['narrow_families'], ['f1'])
        self.assertAlmostEqual(result['narrow_gain_pct'], 15.0)
        self.assertEqual(result['narrow_pairs'], 2)
        self.assertIsNotNone(result['bootstrap_95'])

    def test_summary_loader_maps_candidate_and_ignores_unpaired(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'summary.json'
            records = [{'case_id': item['case_id'], 'round': 1, 'category': 'code',
                        'variant': item['arm'], 'response': {'wall_s': item['response']['wall_s']}}
                       for item in rows()]
            records.append({'case_id': 'd', 'round': 1, 'category': 'code',
                            'variant': 'direct', 'response': {'wall_s': 5.0}})
            path.write_text(json.dumps({'records': records}))
            loaded = mtp_oracle.summary_rows(path, 'mtp')
        selected = mtp_oracle.pairs(loaded)
        self.assertEqual(len(selected), 3)
        self.assertAlmostEqual(mtp_oracle.gain(selected), 10.0)

    def test_missing_pair_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'no complete'):
            mtp_oracle.summarize(mtp_oracle.pairs([]), 3.0, 10, 1)


if __name__ == '__main__':
    unittest.main()
