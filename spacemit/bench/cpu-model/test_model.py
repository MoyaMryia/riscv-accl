"""检查依赖、资源冲突、数据隔离与证据损坏处理。"""
import copy
import unittest
import model
import prepare


class ModelTests(unittest.TestCase):
    def test_dependency_chain_limits_parallel_issue(self):
        parameters=copy.deepcopy(model.INITIAL)
        parameters['latency']['add']=4
        dependent=dict(instructions=[prepare.instruction('add',0) for _ in range(16)])
        independent=dict(instructions=[prepare.instruction('add',i%4) for i in range(16)])
        self.assertGreater(model.predict(dependent,parameters),model.predict(independent,parameters)*2)

    def test_resource_occupancy_limits_independent_chains(self):
        parameters=copy.deepcopy(model.INITIAL)
        parameters['latency']['ime']=1
        record=dict(instructions=[prepare.instruction('ime',i%4) for i in range(16)])
        fast=model.predict(record,parameters)
        parameters['occupancy']['ime']=4
        self.assertGreater(model.predict(record,parameters),fast*2)

    def test_shared_resource_changes_overlap(self):
        parameters=copy.deepcopy(model.INITIAL)
        parameters['latency']['ime']=parameters['latency']['vadd']=1
        parameters['occupancy']['ime']=parameters['occupancy']['vadd']=3
        record=dict(instructions=[prepare.instruction(k,i%4) for i in range(16) for k in ('ime','vadd')])
        separate=model.predict(record,parameters)
        parameters['shared_vector']=True
        self.assertGreater(model.predict(record,parameters),separate)

    def test_head_block_prevents_later_issue(self):
        parameters=copy.deepcopy(model.INITIAL)
        parameters['latency']['mul']=12
        blocked=dict(instructions=[prepare.instruction('mul',0),prepare.instruction('add',0),prepare.instruction('add',1)])
        reordered=dict(instructions=[prepare.instruction('mul',0),prepare.instruction('add',1),prepare.instruction('add',0)])
        self.assertGreaterEqual(model.predict(blocked,parameters),model.predict(reordered,parameters))

    def test_late_operand_read_blocks_overwrite(self):
        parameters=copy.deepcopy(model.INITIAL)
        record=dict(instructions=[prepare.instruction(k,i%4) for i in range(16) for k in ('ime','vload')])
        immediate=model.predict(record,parameters)
        parameters['read_hold_ime']=8
        self.assertGreater(model.predict(record,parameters),immediate)

    def test_typed_bypass_changes_consumer_ready_time(self):
        parameters=copy.deepcopy(model.INITIAL)
        record=dict(instructions=[prepare.instruction(k,i%2) for i in range(16) for k in ('mul','add')])
        ordinary=model.predict(record,parameters)
        parameters['bypass']['mul:add']=16
        self.assertGreater(model.predict(record,parameters),ordinary)

    def test_vector_type_gap_changes_interleave(self):
        parameters=copy.deepcopy(model.INITIAL)
        record=dict(instructions=[prepare.instruction(k,i%4) for i in range(16) for k in ('ime','vadd')])
        ordinary=model.predict(record,parameters)
        parameters['vector_gap']['ime:vadd']=8
        self.assertGreater(model.predict(record,parameters),ordinary)

    def test_split_uses_whole_groups(self):
        records=prepare.definitions()
        for split,count in [('training',48),('calibration',38),('test',18)]:
            self.assertEqual(sum(r['split']==split for r in records),count)
        groups={}
        for row in records:
            groups.setdefault(row['group'],set()).add(row['split'])
        self.assertTrue(all(len(splits)==1 for splits in groups.values()))
        self.assertTrue(all(len(row['kinds'])<3 for row in records if row['split']=='training'))

    def test_calibration_score_covers_both_arms_and_ratio(self):
        plan=dict(records=[dict(id='a',group='g',split='test',arm=0,kinds=['add'],chains=1),dict(id='b',group='g',split='test',arm=1,kinds=['add'],chains=1)])
        predicted=dict(predictions=dict(a=100,b=100))
        data=dict(cycles=dict(a=50,b=200),slopes=dict(a={'0':50},b={'0':200}))
        row=model.group_scores(plan,predicted,data,'test')[0]
        self.assertAlmostEqual(row['ratio_error_factor'],4)
        self.assertAlmostEqual(row['maximum_absolute_log_error'],model.math.log(4))

    def test_steady_state_preserves_loop_carried_dependency(self):
        parameters=copy.deepcopy(model.INITIAL)
        record=dict(instructions=[prepare.instruction('mul',0)])
        self.assertEqual(model.predict(record,parameters,32),model.predict(record,parameters,128))
        self.assertGreaterEqual(model.predict(record,parameters),parameters['latency']['mul'])


if __name__=='__main__':
    unittest.main()
