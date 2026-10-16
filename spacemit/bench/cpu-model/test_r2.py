"""检查第二轮分组、语义约束与稳态周期计算。"""
from importlib.util import module_from_spec,spec_from_file_location
from pathlib import Path
import copy
import random
import unittest
import model
import prepare
import state
from test_reorder import values

HERE=Path(__file__).resolve().parent
spec=spec_from_file_location('prepare_r2',HERE/'prepare-r2.py')
prepare_r2=module_from_spec(spec);spec.loader.exec_module(prepare_r2)
spec=spec_from_file_location('fit_r2',HERE/'fit-r2.py')
fit_r2=module_from_spec(spec);spec.loader.exec_module(fit_r2)


class SecondRoundTests(unittest.TestCase):
    def test_complete_group_split(self):
        rows=prepare_r2.definitions()
        self.assertEqual(sum(r['split']=='training' for r in rows),174)
        self.assertEqual(sum(r['split']=='calibration' for r in rows),76)
        self.assertEqual(sum(r['split']=='test' for r in rows),36)
        groups={}
        for row in rows:
            groups.setdefault(row['group'],set()).add(row['split'])
        self.assertTrue(all(len(splits)==1 for splits in groups.values()))

    def test_all_reorders_preserve_register_results(self):
        index={}
        for row in prepare_r2.definitions():
            key=row['group'],row['unroll']
            if row['arm']==0:
                index[key]=row
            else:
                self.assertEqual(values(index[key]['instructions']),values(row['instructions']))
                position={original:i for i,original in enumerate(row['original_order'])}
                for node,parents in enumerate(row['original_dependencies']):
                    self.assertTrue(all(position[parent]<position[node] for parent in parents))

    def test_period_matches_long_direct_simulation(self):
        rng=random.Random(2026101220)
        rows=prepare.definitions()
        for _ in range(12):
            p=copy.deepcopy(model.INITIAL)
            p['branch_boundary_gap']=rng.randrange(2)
            p['read_hold_ime']=rng.randrange(9)
            p['occupancy']['mul']=rng.choice([1,3,5,6])
            program=state.compiled(rng.choice(rows))
            parameters=state.prepare_parameters(p)
            self.assertAlmostEqual(state.steady(program,parameters),state.execute(program,parameters,4096),delta=.01)

    def test_arithmetic_queue_allows_scalar_overlap(self):
        row=dict(instructions=[prepare.instruction('vadd',0),prepare.instruction('vadd',0)]+[prepare.instruction('add',7) for _ in range(10)])
        p=copy.deepcopy(model.INITIAL)
        p['latency']['vadd']=8
        program=state.compiled(row)
        blocked=state.steady(program,state.prepare_parameters(p))
        p['arithmetic_queue_depth']=4
        queued=state.steady(program,state.prepare_parameters(p))
        self.assertLess(queued,blocked)
        self.assertAlmostEqual(queued,state.execute(program,state.prepare_parameters(p),4096),delta=.01)

    def test_group_score_includes_both_unroll_versions(self):
        rows=[];predictions={};cycles={};slopes={}
        for unroll in (1,4):
            for arm in (0,1):
                name=f'{unroll}-{arm}'
                rows.append(dict(id=name,group='g',split='test',unroll=unroll,arm=arm,kinds=['add'],chains=2))
                predictions[name]=100
                cycles[name]=200 if unroll==4 and arm else 100
                slopes[name]={'0':cycles[name]}
        result=fit_r2.groups(dict(records=rows),dict(predictions=predictions),dict(cycles=cycles,slopes=slopes),'test')
        self.assertEqual(len(result[0]['variants']),2)
        self.assertAlmostEqual(result[0]['maximum_absolute_log_error'],model.math.log(2))


if __name__=='__main__':
    unittest.main()
