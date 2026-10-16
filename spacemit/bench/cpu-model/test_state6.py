"""检查标量等待队列保留结果依赖与稳态状态。"""
import copy
import unittest
import state6
from test_state5 import parameters


class ScalarQueueTests(unittest.TestCase):
    def parameters(self):
        p=parameters();p.update(scalar_queue_depth=4,scalar_queue_kinds=['add','mul','load'],scalar_capture='execute')
        p['latency']['mul']=5;p['occupancy']['mul']=3
        return p

    def test_queue_cannot_remove_true_self_dependency(self):
        p=self.parameters();p['latency']['add']=5
        row=dict(instructions=[dict(kind='add',reads=['t0','a4'],writes=['t0'])]*12)
        queued=state6.predict(row,p);p['scalar_queue_depth']=0
        self.assertEqual(queued,state6.predict(row,p))

    def test_independent_multiply_can_advance(self):
        p=self.parameters();ops=[]
        for i in range(12):
            source=f's{i%3}';destination=f'd{i%3}'
            ops += [dict(kind='mul',reads=[source,'a4'],writes=[source]),dict(kind='add',reads=[destination,source],writes=[destination])]
        row=dict(instructions=ops);queued=state6.predict(row,p);p['scalar_queue_depth']=0
        self.assertLess(queued,state6.predict(row,p))

    def test_period_includes_waiting_scalar_instructions(self):
        p=self.parameters();p['write_gap']={'add:mul':5,'mul:add':5}
        row=dict(instructions=[dict(kind='add',reads=['a4','a4'],writes=['t0']),dict(kind='mul',reads=['a4','a4'],writes=['t0'])]*12)
        prepared=state6.prepare_parameters(p)
        self.assertEqual(state6.steady(state6.compiled(row),prepared),state6.execute(state6.compiled(row),prepared,384))


if __name__=='__main__':unittest.main()
