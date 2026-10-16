"""检查重复写入间隔与结果依赖分离。"""
import copy
import unittest
import state5


def parameters():
    return dict(width=2,scalar_units=2,lsu_units=1,shared_vector=False,waw=True,
        read_hold_ime=0,branch_boundary_gap=0,latency={k:1 for k in state5.KINDS[:6]},
        occupancy={k:1 for k in state5.KINDS[:6]},bypass={},vector_gap={},
        separate_multiply=True,multiply_units=1,waw_policy='completion',write_gap={})


class WriteGapTests(unittest.TestCase):
    def record(self,reads):
        return dict(instructions=[dict(kind='add',reads=reads,writes=['t0'])]*12)

    def test_same_target_gap_does_not_require_a_read(self):
        p=parameters();r=self.record(['a4','a4']);before=state5.predict(r,p)
        p['write_gap']['add:add']=4
        self.assertGreater(state5.predict(r,p),before)

    def test_raw_latency_remains_separate(self):
        p=parameters();p['latency']['add']=5
        dependent=state5.predict(self.record(['t0','a4']),p)
        independent=state5.predict(self.record(['a4','a4']),p)
        self.assertGreater(dependent,independent)

    def test_period_key_includes_write_gap(self):
        p=parameters();p['write_gap']['add:add']=10
        r=self.record(['a4','a4']);prepared=state5.prepare_parameters(p)
        self.assertEqual(state5.steady(state5.compiled(r),prepared),state5.execute(state5.compiled(r),prepared,384))


if __name__=='__main__':unittest.main()
