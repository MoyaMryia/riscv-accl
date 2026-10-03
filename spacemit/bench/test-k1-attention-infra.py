#!/usr/bin/env python3
"""Check infrastructure experiment gates reject incomplete or misleading evidence."""
import importlib.util
import json
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('infra',HERE/'k1-attention-infra.py')
infra=importlib.util.module_from_spec(spec); spec.loader.exec_module(infra)


class Gates(unittest.TestCase):
    def test_operator_requires_affinity_complete_stage_data_and_disabled_timers(self):
        row={'mode':1,'profile':0,'block':2,'heads':8,'kv_heads':2,'kv_rows':8192,'mask':1,
             'cpus':[0,1,2,3],'slowest_ms':110,'ms_per_call':5,'stage_sum_ns':[0]*8}
        shape={'heads':8,'kv_heads':2}
        self.assertEqual(infra.parse_operator(json.dumps(row),1,0,2,shape,8192,1),row)
        for changes in ({'cpus':[0,0,0,0]},{'slowest_ms':90},{'stage_sum_ns':[0]*7},
                        {'stage_sum_ns':[1]*8},{'ms_per_call':float('nan')},{'profile':1}):
            with self.assertRaises(ValueError):
                infra.parse_operator(json.dumps({**row,**changes}),1,0,2,shape,8192,1)
        with self.assertRaises(ValueError):
            infra.parse_operator(json.dumps({**row,'profile':1}),1,1,2,shape,8192,1)

    def comparisons(self):
        return [{'mode':1,'history':h,'mask':mask,'model':model,'advance':h>=8192,
                 'clear_regression':False,'reduction_pct':5} for model in ('2B','4B')
                for h in (2048,8192,16384) for mask in (0,1)]
    def test_long_history_gain_does_not_require_short_history_gain(self):
        self.assertEqual(infra.choose(self.comparisons(),[1]),1)
    def test_rejects_regression_on_any_shape(self):
        rows=self.comparisons(); rows[0]['clear_regression']=True
        self.assertIsNone(infra.choose(rows,[1]))
    def test_missing_long_shapes_fail_instead_of_qualifying(self):
        with self.assertRaises(ValueError): infra.choose(self.comparisons()[:-1],[1])


if __name__=='__main__': unittest.main()
