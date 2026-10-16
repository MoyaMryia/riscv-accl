"""检查源操作数交换保持完整依赖与算术语义。"""
import importlib.util
from pathlib import Path
import unittest
from collections import defaultdict
from reorder import dependencies

spec=importlib.util.spec_from_file_location('write5',Path(__file__).with_name('prepare-write-r5.py'))
r5=importlib.util.module_from_spec(spec);spec.loader.exec_module(r5)


class WriteProbeTests(unittest.TestCase):
    def test_complete_fixed_matrix(self):
        rows=r5.definitions()
        self.assertEqual(len(rows),168)
        self.assertEqual({f:sum(r['family']==f for r in rows) for f in ('RAW','WAR','WAW','reorder')},dict(RAW=72,WAR=24,WAW=36,reorder=36))

    def test_swap_preserves_reads_writes_and_dependencies(self):
        groups=defaultdict(list)
        for row in r5.definitions():
            if row['family'] in ('RAW','WAR'):groups[row['group']].append(row)
        for rows in groups.values():
            self.assertEqual(len(rows),2)
            self.assertEqual(dependencies(rows[0]['instructions']),dependencies(rows[1]['instructions']))
            for left,right in zip(rows[0]['instructions'],rows[1]['instructions']):
                self.assertEqual(left['kind'],right['kind']);self.assertEqual(left['writes'],right['writes'])
                self.assertEqual(sorted(left['reads']),sorted(right['reads']))

    def test_reorder_preserves_dependencies(self):
        for row in r5.definitions():
            if row['family']!='reorder':continue
            positions={index:i for i,index in enumerate(row['original_order'])}
            for index,parents in enumerate(row['original_dependencies']):
                self.assertTrue(all(positions[p]<positions[index] for p in parents))


if __name__=='__main__':unittest.main()
