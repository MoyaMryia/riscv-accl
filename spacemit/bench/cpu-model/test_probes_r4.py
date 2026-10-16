"""检查主动选测保留范围、真实依赖与冻结重排角色。"""
import importlib.util
from pathlib import Path
import unittest
from model import INITIAL
from reorder import dependencies

spec=importlib.util.spec_from_file_location('probes4',Path(__file__).with_name('prepare-probes-r4.py'))
probes=importlib.util.module_from_spec(spec);spec.loader.exec_module(probes)


class ProbeTests(unittest.TestCase):
    def test_pool_and_budget_keep_all_candidates(self):
        rows=probes.candidates();self.assertEqual(len(rows),230)
        selected=probes.select(rows,[INITIAL])
        self.assertEqual(len(rows),230);self.assertEqual(len(selected),48)
        for family in ('WAW','WAR','RAW','vector-gap'):
            subset=[r for r in selected if r['family']==family]
            self.assertEqual(len(subset),12)
            self.assertEqual({tuple(r['type_order']) for r in subset},{tuple(r['type_order']) for r in rows if r['family']==family})
        self.assertEqual(sum(not r['selected'] for r in rows),182)

    def test_war_result_accumulates_old_source(self):
        for row in probes.candidates():
            if row['family']!='WAR':continue
            first=row['instructions'][0]
            self.assertIn(first['writes'][0],first['reads'])
            self.assertEqual(len(set(first['reads'])),2)
            self.assertEqual(row['instructions'][row['gap']+1]['writes'][0],first['reads'][1])

    def test_validation_reorder_keeps_dependencies(self):
        rows=probes.validation();self.assertEqual(len(rows),36)
        for row in rows:
            positions={index:i for i,index in enumerate(row['original_order'])}
            for index,previous in enumerate(row['original_dependencies']):
                self.assertTrue(all(positions[parent]<positions[index] for parent in previous))
            self.assertEqual(row['role'],'frozen-validation')


if __name__=='__main__':unittest.main()
