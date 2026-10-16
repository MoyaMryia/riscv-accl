"""检查新后测划分、候选保留与重排依赖。"""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('queue6',Path(__file__).with_name('prepare-queue-r6.py'))
r6=importlib.util.module_from_spec(spec);spec.loader.exec_module(r6)


class QueuePlanTests(unittest.TestCase):
    def test_fixed_split_and_retained_candidates(self):
        groups,rows=r6.definitions();self.assertEqual(len(groups),126);self.assertEqual(len(rows),118)
        self.assertEqual({stage:sum(g['split']==stage for g in groups) for stage in ('calibration','test','unmeasured')},dict(calibration=19,test=9,unmeasured=98))
        self.assertEqual({stage:sum(r['split']==stage for r in rows) for stage in ('training','calibration','test')},dict(training=6,calibration=76,test=36))

    def test_new_gaps_and_packet_counts(self):
        groups,rows=r6.definitions()
        self.assertEqual({g['gap'] for g in groups},{1,3,5})
        self.assertEqual({r['packets'] for r in rows if r['split']!='training'},{8,16})

    def test_holdout_reorder_keeps_dependencies(self):
        groups,rows=r6.definitions()
        for row in rows:
            if row['split']=='training':continue
            positions={index:i for i,index in enumerate(row['original_order'])}
            for index,parents in enumerate(row['original_dependencies']):self.assertTrue(all(positions[p]<positions[index] for p in parents))


if __name__=='__main__':unittest.main()
