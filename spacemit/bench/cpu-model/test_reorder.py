"""检查重排保留依赖，且状态引擎与冻结首轮语义一致。"""
import copy
import hashlib
import unittest
import model
import prepare
import reorder
import state


def values(ops):
    registers={name:name.encode() for op in ops for name in op['reads']+op['writes']}
    for _ in range(3):
        for op in ops:
            data=op['kind'].encode()+b'|'+b'|'.join(registers[r] for r in op['reads'])
            results=[hashlib.sha256(data+str(i).encode()).digest() for i in range(len(op['writes']))]
            for register,value in zip(op['writes'],results):
                registers[register]=value
    return registers


class ReorderTests(unittest.TestCase):
    def test_reorder_preserves_register_results(self):
        ops=[prepare.instruction(k,i%4) for i in range(16) for k in prepare.TYPES]
        result,order=reorder.by_kind(ops,prepare.TYPES)
        self.assertEqual(values(ops),values(result))
        self.assertEqual(sorted(order),list(range(len(ops))))

    def test_read_before_write_constraint_is_preserved(self):
        ops=[prepare.instruction('ime',0),prepare.instruction('vload',0)]
        self.assertIn(0,reorder.dependencies(ops)[1])
        result,order=reorder.by_kind(ops,['vload','ime'])
        self.assertEqual(order,[0,1])

    def test_integer_engine_matches_original(self):
        for row in prepare.definitions():
            self.assertEqual(model.predict(row,model.INITIAL,32),state.predict(row,model.INITIAL,32))

    def test_branch_boundary_is_a_separate_hypothesis(self):
        row=dict(instructions=[prepare.instruction('add',0) for _ in range(16)])
        p=copy.deepcopy(model.INITIAL)
        with_boundary=state.predict(row,p)
        p['branch_boundary_gap']=0
        self.assertLess(state.predict(row,p),with_boundary)

    def test_forbidden_pair_changes_issue(self):
        row=dict(instructions=[prepare.instruction(k,i%4) for i in range(16) for k in ('add','load')])
        p=copy.deepcopy(model.INITIAL)
        p['latency']['load']=1
        ordinary=state.predict(row,p)
        p['forbidden_pairs']=['add:load','load:add']
        self.assertGreater(state.predict(row,p),ordinary)


if __name__=='__main__':
    unittest.main()
