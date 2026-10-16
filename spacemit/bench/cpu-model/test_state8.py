"""检查完成顺序假设与新探针的数据隔离。"""
import importlib.util
from pathlib import Path
import unittest
import state6
import state8
from test_state5 import parameters


class CompletionTests(unittest.TestCase):
    def parameters(self):
        p = parameters()
        p.update(scalar_queue_depth=4, scalar_queue_kinds=['add', 'mul', 'load'], scalar_capture='execute')
        p['latency']['mul'] = 5
        p['occupancy']['mul'] = 3
        return p

    def record(self):
        return dict(instructions=[dict(kind='mul', reads=['a4'], writes=['t0']),
            dict(kind='add', reads=['a4'], writes=['t1'])] * 9)

    def test_default_matches_frozen_engine(self):
        p = self.parameters()
        row = self.record()
        self.assertEqual(state8.predict(row, p), state6.predict(row, p))

    def test_global_order_delays_independent_short_operation(self):
        p = self.parameters()
        p['scalar_queue_depth'] = 0
        independent = state8.predict(self.record(), p)
        p['completion_order'] = 'global'
        self.assertGreater(state8.predict(self.record(), p), independent)

    def test_resource_order_does_not_create_cross_resource_delay(self):
        p = self.parameters()
        p.update(scalar_queue_depth=0, separate_multiply=True)
        independent = state8.predict(self.record(), p)
        p['completion_order'] = 'resource'
        self.assertEqual(state8.predict(self.record(), p), independent)

    def test_period_contains_completion_limits(self):
        p = self.parameters()
        p['completion_order'] = 'global'
        program = state8.compiled(self.record())
        parameters = state8.prepare_parameters(p)
        self.assertEqual(state8.steady(program, parameters), state8.execute(program, parameters, 384))
        events = []
        state8.execute(program, parameters, 8, events=events)
        self.assertTrue(all(e['complete'] >= e['previous_completion_limit'] for e in events))
        self.assertTrue(all(e['execute'] >= e['operand_ready'] for e in events))

    def test_probe_groups_do_not_cross_stages(self):
        spec = importlib.util.spec_from_file_location('prepare8_test', Path(__file__).with_name('prepare-completion-r8.py'))
        prepare = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(prepare)
        configs, rows = prepare.definitions()
        self.assertEqual(len(configs), 72)
        self.assertEqual(len(rows), 312)
        for config in configs:
            group = [r for r in rows if r['group'] == config['group']]
            self.assertEqual(len(group), 4)
            self.assertEqual({r['split'] for r in group}, {config['split']})
            self.assertTrue(all(not r['semantic_pair'] for r in group))
        self.assertEqual(sum(r['semantic_pair'] for r in rows), 24)


if __name__ == '__main__':
    unittest.main()
