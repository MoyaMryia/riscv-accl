"""检查第三轮的实际依赖、数据隔离与乘法资源假设。"""
import copy
import importlib.util
from pathlib import Path
import unittest
import state
import state3
from model import INITIAL
from reorder import dependencies

spec=importlib.util.spec_from_file_location('prepare3',Path(__file__).with_name('prepare-r3.py'))
prepare3=importlib.util.module_from_spec(spec);spec.loader.exec_module(prepare3)


class ThirdRoundTests(unittest.TestCase):
    def test_transfer_consumer_reads_producer(self):
        for row in prepare3.definitions():
            if row['mode']!='transfer':continue
            ops=row['instructions'];consumer=[op for op in ops if op['writes']==['t1']]
            producer=[op for op in ops if op['writes']==['t0']]
            self.assertEqual(len(consumer),8)
            self.assertEqual(len(producer),8)
            self.assertTrue(all(op['reads'][0]=='t0' for op in consumer))
            self.assertEqual(len([op for op in ops if op['writes']==['t0']]),8)

    def test_independent_banks_have_no_cross_dependency(self):
        for row in prepare3.definitions():
            if row['mode']!='independent':continue
            kinds=row['kinds'];banks={kind:set() for kind in kinds}
            for op in row['instructions']:banks[op['kind']].update(op['writes'])
            self.assertFalse(banks[kinds[0]]&banks[kinds[1]])

    def test_holdout_is_disjoint_and_complete(self):
        rows=prepare3.definitions();groups={}
        for row in rows:groups.setdefault(row['group'],[]).append(row)
        counts={'calibration':0,'test':0}
        for records in groups.values():
            splits={r['split'] for r in records};self.assertEqual(len(splits),1)
            split=records[0]['split']
            if split=='training':continue
            counts[split]+=1
            self.assertEqual({(r['unroll'],r['arm']) for r in records},{(2,0),(2,1),(3,0),(3,1)})
        self.assertEqual(counts,{'calibration':19,'test':13})

    def test_separate_multiplier_allows_alu_overlap(self):
        p=copy.deepcopy(INITIAL);p.update(branch_boundary_gap=1,forbidden_pairs=[],arithmetic_queue_depth=0)
        p['latency']['mul']=1;p['occupancy']['mul']=4;p['scalar_units']=1
        row={'instructions':[prepare3.scalar(k,4*j+i%4) for i in range(16) for j,k in enumerate(('mul','add'))]}
        shared=state3.steady(state3.compiled(row),state3.prepare_parameters(p))
        p['separate_multiply']=True
        separate=state3.steady(state3.compiled(row),state3.prepare_parameters(p))
        self.assertLess(separate,shared)
        self.assertEqual(separate,state3.execute(state3.compiled(row),state3.prepare_parameters(p),384))

    def test_completion_rule_does_not_wait_for_equal_latency_write(self):
        p=copy.deepcopy(INITIAL);p.update(branch_boundary_gap=0,forbidden_pairs=[],arithmetic_queue_depth=0)
        p['occupancy']['mul']=1;p['bypass']['load:mul']=1
        row={'instructions':[op for _ in range(8) for op in (prepare3.scalar('load',0),prepare3.scalar('mul',1,0))]}
        pending=state3.steady(state3.compiled(row),state3.prepare_parameters(p))
        p['waw_policy']='completion'
        completion=state3.steady(state3.compiled(row),state3.prepare_parameters(p))
        self.assertLess(completion,pending)
        self.assertEqual(completion,state3.execute(state3.compiled(row),state3.prepare_parameters(p),384))

    def test_original_resource_model_is_preserved(self):
        p=copy.deepcopy(INITIAL);p.update(branch_boundary_gap=1,forbidden_pairs=[],arithmetic_queue_depth=4)
        for row in prepare3.definitions()[::17]:
            a=state.steady(state.compiled(row),state.prepare_parameters(p))
            b=state3.steady(state3.compiled(row),state3.prepare_parameters(p))
            self.assertEqual(a,b)


if __name__=='__main__':unittest.main()
