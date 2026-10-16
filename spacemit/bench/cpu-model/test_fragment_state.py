"""检查完整调用的有限边界、访存依赖与队列时序。"""
import unittest
import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('fragment_state',Path(__file__).with_name('fragment-state.py'))
state=importlib.util.module_from_spec(spec);spec.loader.exec_module(state)


class FragmentStateTests(unittest.TestCase):
    def parameters(self):
        return state.initial_parameters(dict(width=2,scalar_units=2,lsu_units=1,waw=True,
            latency=dict(add=1,mul=5,load=3),occupancy=dict(add=1,mul=1,load=1),
            bypass={},scalar_queue_depth=3))

    def row(self,name='addi',reads=(),writes=(),address=None,store=False,size=1,**fields):
        operation=dict(name=name,reads=list(reads),writes=list(writes),control='next')
        memory=[]
        if address is not None:
            operation.update(memory_bytes=size,store=store)
            memory=[dict(address=address,bytes=size,store=store)]
        return dict(operation=operation,memory=memory,**fields)

    def test_finite_program_has_no_synthetic_loop(self):
        rows=[self.row(writes=[f'x{i+1}']) for i in range(5)]
        value=state.execute(state.compile_trace(rows),self.parameters())
        self.assertEqual(value['instructions'],5)
        self.assertEqual(value['return_cycles'],3)

    def test_load_result_delays_store_data(self):
        rows=[self.row('lbu',writes=['x1'],address=100),self.row('sb',reads=['x1'],address=200,store=True)]
        p=self.parameters();p['load_store_bypass']=4
        events=[];state.execute(state.compile_trace(rows),p,events)
        self.assertGreaterEqual(events[1]['execute'],events[0]['execute']+4)

    def test_vector_store_overlap_requires_completion(self):
        rows=[self.row('vse8.v',address=100,store=True,size=32,vl=32,vtype=192),
              self.row('sb',address=100,store=True)]
        p=self.parameters();p['vector_start']=5
        events=[];state.execute(state.compile_trace(rows),p,events)
        self.assertGreaterEqual(events[1]['execute'],events[0]['complete'])
        rows[1]['memory'][0]['address']=300
        other=[];state.execute(state.compile_trace(rows),p,other)
        self.assertLess(other[1]['execute'],other[0]['complete'])

    def test_store_to_load_address_dependency(self):
        rows=[self.row('sb',address=100,store=True),self.row('lbu',writes=['x1'],address=100)]
        p=self.parameters();p['store_load_gap']=7
        events=[];state.execute(state.compile_trace(rows),p,events)
        self.assertGreaterEqual(events[1]['execute'],events[0]['execute']+7)

    def test_unknown_division_has_no_cost(self):
        with self.assertRaises(ValueError):state.compile_trace([self.row('div',reads=['x1'],writes=['x2'])])

    def test_invalid_resource_is_failure(self):
        p=self.parameters();p['lsu_units']=0
        with self.assertRaises(ValueError):state.execute(state.compile_trace([self.row()]),p)

    def test_drain_is_reported_separately(self):
        value=state.execute(state.compile_trace([self.row('mul',writes=['x1'])]),self.parameters())
        self.assertEqual(value['return_cycles'],1)
        self.assertEqual(value['drained_cycles'],5)
        self.assertEqual(value['pending_at_return'],4)

    def test_repeated_call_slope_uses_complete_boundary(self):
        p=self.parameters()
        p['write_gap']['add:add']=1
        p['scalar_queue_depth']=0
        short=state.compile_trace([self.row(writes=['x1']) for _ in range(3)])
        long=state.compile_trace([self.row(writes=['x1']) for _ in range(9)])
        self.assertEqual(state.slope(short,long,[3,9],p)['cycles_per_call'],1)
        with self.assertRaises(ValueError):state.slope(short,long,[9,3],p)


if __name__=='__main__':unittest.main()
