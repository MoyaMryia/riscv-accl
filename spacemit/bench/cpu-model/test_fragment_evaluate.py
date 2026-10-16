"""检查冻结预测的漏报、退步与观测不确定方向均被保留。"""
import importlib.util
import copy
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('fragment_evaluate',Path(__file__).with_name('fragment-evaluate.py'))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class EvaluationTests(unittest.TestCase):
    def fixture(self):
        plan=dict(baseline='base',cases=[dict(id='held',split='validation')],kernels=[dict(id=k) for k in ('base','candidate')])
        prediction=dict(records=[dict(case='held',kernel=k,cycles_per_call=v) for k,v in [('base',100),('candidate',120)]])
        observations=dict(status='paired-observations-verified',nonpositive_slopes=[],cases=[dict(configuration=plan['cases'][0],
            median_cost_per_call=dict(base=dict(cycles=100),candidate=dict(cycles=80)),
            comparisons=[dict(candidate='candidate',metrics=dict(cycles=dict(candidate_over_baseline=.8,observed_paired_ratio_range=[.79,.81])))])])
        observations['slopes']=[dict(case='held',session=s,repeat=r,kernel=k,
            fields=dict(cycles=dict(slope=100 if k=='base' else [79,80,80,80,81][r])))
            for s in (0,1) for r in range(5) for k in ('base','candidate')]
        return plan,prediction,observations

    def test_missed_gain_is_retained(self):
        result=module.evaluate(*self.fixture())
        self.assertEqual(result['summary']['validation']['direction_agreement'],0)
        self.assertTrue(result['comparisons'][0]['retained'])
        self.assertFalse(result['automatic_performance_rejection'])
        self.assertIsNone(result['prediction_confidence'])

    def test_repeat_range_crosses_one_is_not_confidence(self):
        plan,prediction,observations=self.fixture()
        observations['slopes'][9]['fields']['cycles']['slope']=110
        observations['cases'][0]['comparisons'][0]['metrics']['cycles']['observed_paired_ratio_range']=[.79,1.1]
        result=module.evaluate(plan,prediction,observations)
        self.assertFalse(result['comparisons'][0]['observed_direction_resolved'])
        self.assertEqual(result['summary']['validation']['unresolved_observed_directions'],1)

    def test_missing_prediction_is_failure(self):
        plan,prediction,observations=self.fixture();prediction['records'].pop()
        with self.assertRaises(ValueError):module.evaluate(plan,prediction,observations)

    def test_bad_native_status_is_failure(self):
        plan,prediction,observations=self.fixture();observations['status']='nonpositive-slopes'
        with self.assertRaises(ValueError):module.evaluate(plan,prediction,observations)

    def test_missing_comparison_is_failure(self):
        plan,prediction,observations=self.fixture();observations['cases'][0]['comparisons']=[]
        with self.assertRaises(ValueError):module.evaluate(plan,prediction,observations)

    def test_duplicate_comparison_is_failure(self):
        plan,prediction,observations=self.fixture()
        observations['cases'][0]['comparisons']*=2
        with self.assertRaises(ValueError):module.evaluate(plan,prediction,observations)

    def test_duplicate_case_is_failure(self):
        plan,prediction,observations=self.fixture()
        observations['cases'].append(copy.deepcopy(observations['cases'][0]))
        with self.assertRaises(ValueError):module.evaluate(plan,prediction,observations)

    def test_ratio_and_range_must_match_slopes(self):
        for field,value in [('candidate_over_baseline',1.2),('observed_paired_ratio_range',[.79,1.1])]:
            with self.subTest(field=field):
                plan,prediction,observations=self.fixture()
                observations['cases'][0]['comparisons'][0]['metrics']['cycles'][field]=value
                with self.assertRaises(ValueError):module.evaluate(plan,prediction,observations)

    def test_nonfinite_or_nonpositive_cost_is_failure(self):
        for value in (float('nan'),float('inf'),0,-1,True):
            with self.subTest(value=value):
                plan,prediction,observations=self.fixture()
                observations['cases'][0]['median_cost_per_call']['base']['cycles']=value
                with self.assertRaises(ValueError):module.evaluate(plan,prediction,observations)

    def test_missing_or_duplicate_slope_is_failure(self):
        for duplicate in (False,True):
            with self.subTest(duplicate=duplicate):
                plan,prediction,observations=self.fixture()
                if duplicate:observations['slopes'].append(copy.deepcopy(observations['slopes'][0]))
                else:observations['slopes'].pop()
                with self.assertRaises(ValueError):module.evaluate(plan,prediction,observations)

    def test_cost_must_match_slopes(self):
        plan,prediction,observations=self.fixture()
        observations['cases'][0]['median_cost_per_call']['candidate']['cycles']=81
        with self.assertRaises(ValueError):module.evaluate(plan,prediction,observations)


if __name__=='__main__':unittest.main()
