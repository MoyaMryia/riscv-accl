"""检查完整算子范围、配对数据和独立拟合。"""
import copy
import gzip
import json
from pathlib import Path
import tempfile
import unittest
from test_predictor import module

family=module('family-model')
census=module('domain-census')


class FamilyModelTests(unittest.TestCase):
    def test_ime_mix_encoding_and_group_split(self):
        prepare=module('prepare-ime-mix')
        self.assertEqual(prepare.dot(16,14,0),0xe207382b)
        word=prepare.dot(22,14,3)
        self.assertEqual((word>>7)&31,22)
        self.assertEqual((word>>15)&31,14)
        self.assertEqual((word>>20)&31,3)
        with self.assertRaises(ValueError):prepare.dot(17,14,0)
        groups=prepare.groups()
        self.assertEqual(sum(g['split']=='calibration' for g in groups),19)
        self.assertEqual(sum(g['split']=='test' for g in groups),9)
        self.assertEqual(len({(g['chains'],g['gap']) for g in groups}),28)

    def test_ime_mix_keeps_non_affine_unroll_costs(self):
        audit=module('ime-mix-evaluate')
        definitions=[];rows=[]
        for arm in (0,1):
            for u in (8,32,128):
                identity=f'case-{arm}-{u}'
                definitions.append(dict(id=identity,group='case',arm=arm,operations=u))
                for n in (2,16):
                    rows.append(dict(id=identity,group='case',arm=arm,unroll=u,loops=n,
                        cost=dict(model_sha256='model',coverage=dict(trace_complete=True),
                            scenarios=[dict(name='central-warm',cohort_cycles=123+n*u*u*(1+arm))])))
        plan=dict(binary_sha256='binary',frozen_component_model_sha256='model',
            trace_lengths=[2,16],records=definitions)
        source=dict(status='complete',plan_sha256='plan',binary_sha256='binary',records=rows)
        costs=audit.predictions(plan,source,'plan')
        self.assertEqual(costs['case',0,32],1024)
        self.assertEqual(costs['case',1,128],32768)
        rows[0]['cost']['model_sha256']='other'
        with self.assertRaises(ValueError):audit.predictions(plan,source,'plan')

    def test_ime_mix_bound_rejects_mutation_and_scope_transfer(self):
        audit=module('ime-mix-evaluate')
        plan=dict(groups=[dict(id=str(i),split='calibration') for i in range(19)],
            binary_sha256='binary',frozen_component_model_sha256='model')
        value=dict(implementation_sha256=audit.implementation(),plan_sha256='plan',
            binary_sha256='binary',model_sha256='model',predictions_sha256='predictions',
            records=[dict(group=str(i),maximum_log_error=.1) for i in range(19)],maximum_group_log_error=.1)
        value['calibration_sha256']=audit.measure.digest(value)
        audit.verify_bound(value,plan,'plan','predictions')
        with self.assertRaises(ValueError):audit.verify_bound(value,plan,'other','predictions')
        value['maximum_group_log_error']=.01
        with self.assertRaises(ValueError):audit.verify_bound(value,plan,'plan','predictions')

    def test_loop_neighbor_interpolation_and_joint_group_coverage(self):
        neighbor=module('schedule-neighbor')
        points=[dict(group=str(vl),m=1,vl=vl,stride=0,chains=2,arm=0,unroll=8,cycles_per_loop=cost)
            for vl,cost in [(4,10),(8,40)]]
        value,meta=neighbor.estimate(dict(points=points),dict(m=1,vl=6,stride=0,chains=2),0,8)
        self.assertAlmostEqual(value,20)
        self.assertEqual(meta['kind'],'log-cost-interpolation')
        value,meta=neighbor.estimate(dict(points=points),dict(m=1,vl=1,stride=0,chains=2),0,8)
        self.assertEqual(value,10)
        self.assertEqual(meta['kind'],'clamped-anchor')
        rows=[dict(group='case',variants=[dict(predicted_ratio=1.2,measured_ratio=r) for r in [1.2,1.2,1.5]])]
        neighbor.add_bounds(rows,dict(maximum_group_log_error=.1))
        self.assertEqual(sum(v['covered'] for v in rows[0]['variants']),2)
        self.assertFalse(rows[0]['covered'])

    def test_schedule_basis_and_duplicate_configuration(self):
        schedule=module('schedule-family')
        group=dict(m=4,vl=31,stride=16,chains=4)
        values=schedule.features(group,1)
        self.assertEqual(len(values),48)
        self.assertAlmostEqual(sum(values),1)
        self.assertTrue(all(v>=0 for v in values))
        self.assertEqual(sum(values[:24]),0)
        groups=[dict(id=str(i),m=m,vl=vl,stride=s,chains=c) for i,(m,vl,s,c) in enumerate(
            (m,vl,s,c) for m in (1,2,4) for vl in range(1,8*m+1) for s in (0,16) for c in (2,4))][:52]
        for i,g in enumerate(groups):g['split']='training' if i<24 else 'calibration' if i<43 else 'test'
        schedule.check_plan(dict(groups=groups))
        groups[-1]={**groups[-2],'id':'other','split':'test'}
        with self.assertRaises(ValueError):schedule.check_plan(dict(groups=groups))

    def test_load_use_calibration_rejects_mutation_and_scope_difference(self):
        evaluate=module('load-use-evaluate')
        plan=dict(groups=[dict(id=str(j),split='calibration' if j<19 else 'test') for j in range(24)],
            binary_sha256='binary',frozen_component_model_sha256='model')
        value=dict(implementation_sha256=family.sha(Path(evaluate.__file__)),plan_sha256='plan',
            binary_sha256='binary',model_sha256='model',calibration_groups=[str(j) for j in range(19)],
            maximum_absolute_log_ratio_error=.2)
        value['calibration_sha256']=evaluate.digest(value)
        evaluate.verify_calibration(value,plan,'plan')
        with self.assertRaises(ValueError):evaluate.verify_calibration(value,plan,'other-plan')
        value['maximum_absolute_log_ratio_error']=.1
        with self.assertRaises(ValueError):evaluate.verify_calibration(value,plan,'plan')

    def test_load_use_plan_has_no_group_leakage(self):
        prepare=module('prepare-load-use')
        values=prepare.cases()
        self.assertEqual(len({r['id'] for r in values}),24)
        self.assertEqual(sum(r['split']=='calibration' for r in values),19)
        self.assertEqual(sum(r['split']=='test' for r in values),5)
        self.assertEqual(values,prepare.cases())

    def test_wait_diagnosis_matches_default_and_keeps_hypotheses_separate(self):
        explain=module('explain-cost')
        from k1cost import replay_thread
        operations=[dict(pc=16,name='fadd.s',family='float',context=None,read=['f0','f2'],write=['f1'],gaps=[]),
            dict(pc=20,name='sw',family='scalar-memory',context=None,read=['x1'],write=[],gaps=[]),
            dict(pc=24,name='lw',family='scalar-memory',context=None,read=['x3'],write=['x2'],gaps=[])]
        events=[[0,1,[]],[0,1,[]],[1,1,[[4096,4,True]]],[2,1,[[4100,4,False]]],
                [0,2,[]],[0,2,[]]]
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'events.gz'
            with gzip.open(p,'wt') as f:
                for e in events:f.write(json.dumps(e)+'\n')
            baseline=explain.replay(p,operations,{})
            old=replay_thread(p,operations,{},'central','warm')
            self.assertEqual(baseline['estimated_component_cycles'],old['estimated_component_cycles'])
            self.assertEqual(sum(baseline['charged_cycles'].values()),baseline['estimated_component_cycles'])
            relaxed=explain.replay(p,operations,{},False,False)
            self.assertLess(relaxed['estimated_component_cycles'],baseline['estimated_component_cycles'])

    def test_memory_reference_rejects_unmeasured_and_duplicate_configuration(self):
        reference=module('memory-reference')
        profile=dict(records=[dict(mode=3,threads=4,span_bytes_per_buffer=8192)],
            samples_sha256='samples',plan_sha256='plan',frequency_snapshots_khz=[1600000],limits=[])
        result=reference.select(profile,3,4,8192)
        self.assertIsNone(result['algorithm_time_estimate'])
        with self.assertRaises(ValueError):reference.select(profile,3,4,4096)
        profile['records']*=2
        with self.assertRaises(ValueError):reference.select(profile,3,4,8192)

    def test_matched_cycle_scope_and_slope(self):
        matched=module('matched-evaluate')
        rows=[]
        for rep in range(7):
            for length in range(3):
                for arm in (0,1):
                    calls=2**length
                    rows.append(dict(workload='case',valid=True,phases=False,repeat=rep,length=length,
                        arm=arm,calls=calls,wall_ms=(2-arm)*calls,counter_scope='sync-paused-user-cycles',
                        threads=[dict(cpu=j,cycles=7+(20-10*arm)*calls,instructions=10,enabled=20,running=20,
                            frequency_before_khz=1600000,frequency_after_khz=1600000) for j in range(4)]))
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'samples.jsonl'
            p.write_text(''.join(json.dumps(v)+'\n' for v in rows))
            result=matched.evaluate(p,'case','bench-roi')
            self.assertAlmostEqual(result['arms'][0]['cohort_cycles'],20,delta=1e-12)
            self.assertAlmostEqual(result['wall_gain_percent'],50,delta=1e-12)
            with self.assertRaises(ValueError):matched.evaluate(p,'case','bench')

    def test_shared_cache_preserves_repeated_call_state(self):
        from analyze import write,sha
        shared=module('shared-cache')
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);threads=[]
            for cpu in range(4):
                p=root/f't{cpu}.gz'
                with gzip.open(p,'wt') as f:f.write(json.dumps([0,1,[[4096,4,False]]])+'\n')
                threads.append(dict(file=p.name,sha256=sha(p),instructions=1))
            write(root/'program.json',dict(complete=True,threads=threads))
            result=shared.replay(root,1,2,True)
            self.assertEqual(result['passes'][0]['counts']['lower_line_fills'],1)
            self.assertEqual(result['passes'][1]['counts']['lower_line_fills'],0)
            self.assertEqual(result['cross_thread_lines'],1)

    def test_shared_cache_rejects_truncated_or_changed_input(self):
        from analyze import write
        shared=module('shared-cache')
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);write(root/'program.json',dict(complete=False,threads=[]))
            with self.assertRaises(ValueError):shared.replay(root,64,2,False)
            write(root/'program.json',dict(complete=True,threads=[dict(file='missing',sha256='invalid')]*4))
            with self.assertRaises(FileNotFoundError):shared.replay(root,64,2,False)

    def test_nnls_recovers_costs_and_rejects_negative_target(self):
        x=[[1,0],[1,1],[1,2],[1,4]];y=[2,5,8,14]
        coefficients,meta=family.nnls(x,y)
        self.assertAlmostEqual(coefficients[0],2,places=5)
        self.assertAlmostEqual(coefficients[1],3,places=5)
        self.assertLess(meta['optimality_residual'],1e-7)
        with self.assertRaises(ValueError):family.nnls(x,[2,5,-8,14])

    def test_census_requires_actual_bytes_and_four_threads(self):
        item=dict(address=16,encoding='00000013',bytes=4,mnemonic='addi')
        site=dict(pc=16,encoding='00000013',size=4,count=10,load_bytes=0,store_bytes=0)
        data=dict(failure=False,threads=[dict(cpu=j,instructions=10,sites=[dict(site)]) for j in range(4)])
        inv=dict(functions=[dict(instructions=[item])])
        self.assertEqual(census.features(data,inv,0),[1,10/1e6,0,0,2])
        broken=copy.deepcopy(data);broken['threads'][0]['sites'][0]['encoding']='00000093'
        with self.assertRaises(ValueError):census.features(broken,inv,0)
        broken=copy.deepcopy(data);broken['threads'].pop()
        with self.assertRaises(ValueError):census.features(broken,inv,0)

    def test_paired_samples_reject_missing_block_and_counter_multiplex(self):
        rows=[]
        for rep in range(2):
            for length in range(3):
                for arm in (0,1):
                    rows.append(dict(workload='case',valid=True,phases=False,repeat=rep,length=length,
                        arm=arm,calls=2**length,wall_ms=(2-arm)*2**length,
                        threads=[dict(cpu=j,cycles=10,instructions=10,enabled=20,running=20,
                            frequency_before_khz=1600000,frequency_after_khz=1600000) for j in range(4)]))
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'samples.jsonl'
            def save(values):p.write_text(''.join(json.dumps(v)+'\n' for v in values))
            save(rows);self.assertEqual(family.paired_samples(p,'case',2)['measured_ratio'],.5)
            save(rows[:-1])
            with self.assertRaises(ValueError):family.paired_samples(p,'case',2)
            broken=copy.deepcopy(rows);broken[0]['threads'][0]['running']=19;save(broken)
            with self.assertRaises(ValueError):family.paired_samples(p,'case',2)

    def test_model_receipt_rejects_coefficient_change(self):
        value=dict(coefficients_ms=[1,2],implementation_sha256=family.sha(Path(family.__file__)))
        value['model_sha256']=family.digest(value);family.verify_model(value)
        value['coefficients_ms'][0]=3
        with self.assertRaises(ValueError):family.verify_model(value)


if __name__=='__main__':unittest.main()
