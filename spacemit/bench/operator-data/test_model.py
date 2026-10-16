#!/usr/bin/env python3
"""检查形状隔离、冻结身份、组界限和全部候选保留。"""
import copy
import json
from pathlib import Path
import unittest

import model


PLAN = json.loads(Path(__file__).with_name('plan.json').read_text())


def summary(split):
    rows = []
    for g in PLAN['groups']:
        if g['split'] != split:
            continue
        for threads in g['threads']:
            a, b = g['shape']
            base = 0.00001*a*b+0.02*threads
            ratio = 1.12 if g['family'] == 'ime' else 0.8+2/b
            arm = '1' if g['family'] == 'ime' else '2'
            rows.append(dict(case=dict(g, id=f'{g["id"]}-t{threads}', thread_count=threads),
                fits={'0': dict(median_slope_ms_per_call=base), arm: dict(median_slope_ms_per_call=base*ratio)}))
    return dict(status='verified', split=split, results=rows)


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = model.build_model(PLAN, [summary('train')], [{'binary': 'fixed'}])
        cls.calibration = model.calibrate(cls.model, PLAN, summary('calibration'))

    def test_group_shape_cannot_cross_splits(self):
        plan = copy.deepcopy(PLAN)
        train = next(g for g in plan['groups'] if g['split'] == 'train' and g['family'] == 'ime')
        test = next(g for g in plan['groups'] if g['split'] == 'test' and g['family'] == 'ime')
        test['shape'] = train['shape']
        with self.assertRaises(ValueError):
            model.check_plan(plan)

    def test_fit_rejects_calibration_rows(self):
        with self.assertRaises(ValueError):
            model.build_model(PLAN, [summary('calibration')], [{'binary': 'fixed'}])

    def test_fit_rejects_changed_training_plan(self):
        data = summary('train')
        data['results'][0]['case']['padding'] = 999
        with self.assertRaises(ValueError):
            model.build_model(PLAN, [data], [{'binary': 'fixed'}])

    def test_fit_rejects_binary_change(self):
        with self.assertRaises(ValueError):
            model.build_model(PLAN, [summary('train')]*2, [{'binary': 'a'}, {'binary': 'b'}])

    def test_model_mutation_is_rejected(self):
        changed = copy.deepcopy(self.model)
        changed['components']['ime']['ridge'] = 999
        with self.assertRaises(ValueError):
            model.prediction(changed, summary('test')['results'][0]['case'])

    def test_group_bound_is_joint_across_threads_and_targets(self):
        data = summary('calibration')
        victim = next(r for r in data['results'] if r['case']['family'] == 'ime' and r['case']['thread_count'] == 4)
        victim['fits']['1']['median_slope_ms_per_call'] *= 100
        calibration = model.calibrate(self.model, PLAN, data)
        self.assertEqual(calibration['bounds']['ime']['quantile_rank'], 19)
        self.assertGreater(calibration['bounds']['ime']['factor'], 90)
        self.assertEqual(len(calibration['bounds']['ime']['groups']), 19)

    def test_resealed_bound_cannot_hide_failure(self):
        value = copy.deepcopy(self.calibration)
        del value['sha256']
        value['bounds']['ime']['maximum_log_error'] = 0
        value = model.seal(value)
        with self.assertRaises(ValueError):
            model.verify_calibration(value, self.model, PLAN)

    def test_stage_missing_or_duplicate_configuration_is_rejected(self):
        data = summary('test')
        for rows in (data['results'][:-1], data['results'][:-1]+data['results'][:1]):
            with self.assertRaises(ValueError):
                model.evaluate(self.model, PLAN, dict(data, results=rows), self.calibration)

    def test_evaluation_retains_every_candidate(self):
        value = model.evaluate(self.model, PLAN, summary('test'), self.calibration)
        self.assertEqual(len(value['rows']), 36)
        self.assertFalse(value['candidate_elimination'])
        self.assertTrue(any(r['predicted']['ratio'] > 1 for r in value['rows']))
        self.assertTrue(any(r['predicted']['ratio'] < 1 for r in value['rows']))

    def test_no_bound_for_training_or_outside_grid(self):
        train = summary('train')['results'][0]['case']
        test = summary('test')['results'][0]['case']
        outside = dict(test, shape=[999999, 77])
        result = model.query(self.model, PLAN, self.calibration, [train, test, outside])
        by_shape = {tuple(r['case']['shape']): r for r in result}
        self.assertIsNone(by_shape[tuple(train['shape'])]['ratio_interval'])
        self.assertIsNone(by_shape[tuple(outside['shape'])]['ratio_interval'])
        self.assertIsNotNone(by_shape[tuple(test['shape'])]['ratio_interval'])

    def test_nonpositive_slopes_stop_evaluation(self):
        data = summary('test')
        data['results'][0]['fits']['0']['median_slope_ms_per_call'] = -1
        with self.assertRaises(ValueError):
            model.evaluate(self.model, PLAN, data, self.calibration)


class BundleTests(unittest.TestCase):
    def test_portable_replay_and_file_mutation(self):
        import importlib.util
        import tarfile
        import tempfile
        spec = importlib.util.spec_from_file_location('bundle', Path(__file__).with_name('model-bundle.py'))
        bundle = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bundle)
        frozen = model.build_model(PLAN, [summary('train')], [{'binary': 'fixed'}])
        calibration = model.calibrate(frozen, PLAN, summary('calibration'))
        evaluation = model.evaluate(frozen, PLAN, summary('test'), calibration)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, value in [('model', frozen), ('calibration', calibration), ('evaluation', evaluation)]:
                model.write_new(root/(name+'.json'), value)
            bundle.build(Path(__file__).parent, root/'bundle.tar.gz', root/'model.json',
                         root/'calibration.json', root/'evaluation.json')
            unpacked = root/'unpacked'
            unpacked.mkdir()
            with tarfile.open(root/'bundle.tar.gz') as archive:
                archive.extractall(unpacked, filter='data')
            result = bundle.replay(unpacked)
            self.assertEqual(result['cases'], 36)
            (unpacked/'predictions.json').write_text('[]')
            with self.assertRaises(ValueError):
                bundle.replay(unpacked)


if __name__ == '__main__':
    unittest.main()
