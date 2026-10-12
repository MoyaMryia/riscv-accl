"""检查成本覆盖、实际编码和独立误差接口。"""
import json
from pathlib import Path
import tempfile
import unittest

from analyze import write
from k1cost import compile_program, component, model_identity, replay_thread
from priority import conformal, rank
from test_predictor import instruction, module


class ProfileTests(unittest.TestCase):
    def test_archive_receipt_base_is_explicit_and_cannot_escape(self):
        import hashlib
        import tarfile
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);run=root/'payload/run';run.mkdir(parents=True)
            (run/'data').write_bytes(b'evidence')
            digest=hashlib.sha256(b'evidence').hexdigest()
            (run/'SHA256SUMS').write_text(digest+'  run/data\n')
            archive=root/'evidence.tar.gz'
            with tarfile.open(archive,'w:gz') as stream:stream.add(root/'payload',arcname='payload')
            digest=hashlib.sha256(archive.read_bytes()).hexdigest();verify=module('verify-evidence')
            self.assertTrue(verify.archive(archive,digest)['failures'])
            self.assertFalse(verify.archive(archive,digest,{'payload/run/SHA256SUMS':'payload'})['failures'])
            with self.assertRaises(ValueError):verify.archive(archive,digest,{'payload/run/SHA256SUMS':'../outside'})

    def test_count_slope_separates_loop_overhead(self):
        linear=module('fit-k1-profile').linear
        per_count=[]
        for count in (8,32,128):
            value=linear([(n,170+n*(count*6.0+3.0)) for n in (128,512,2048)])
            per_count.append((count,value['slope']))
        value=linear(per_count)
        self.assertAlmostEqual(value['slope'],6.0)
        self.assertAlmostEqual(value['intercept'],3.0)

    def test_missing_cost_is_nonzero_and_has_gap(self):
        op=dict(name='unknown.op',family='unknown',context=None,gaps=[],read=[],write=[])
        latency,occupancy,_,source,gaps,_=component({},op,[],'central')
        self.assertGreater(latency,0);self.assertGreater(occupancy,0)
        self.assertEqual(source,'assumed');self.assertTrue(gaps)

    def test_compressed_memory_uses_memory_cost(self):
        op=dict(name='c.ldsp',family='scalar-load',context=None,gaps=[],read=[],write=[])
        latency,occupancy,port,_,_,_=component({},op,[[4096,8,False]],'central')
        self.assertEqual((latency,occupancy,port),(4.0,1.0,'memory'))

    def test_measured_adapter_keeps_separate_baseline_blocks(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);rows=[]
            for group,arm in [('04',8),('08',16)]:
                for block in range(2):
                    for selected in (0,arm):
                        rows.append(dict(candidate='b2',shape='K2048-H8',arm=selected,block=block,
                            label=group+'-b2-test',ms_per_call=1.0))
            write(root/'samples.json',rows)
            module('prepare-measured-priority').prepare(root/'samples.json',root/'plan.json')
            self.assertEqual(len(json.loads((root/'plan.json').read_text())['records']),2)

    def test_model_identity_ignores_profile_location(self):
        self.assertEqual(model_identity([dict(path='a',sha256='f')])[0],
                         model_identity([dict(path='b',sha256='f')])[0])
        self.assertNotEqual(model_identity([dict(sha256='f')])[0],model_identity([dict(sha256='e')])[0])


class PriorityTests(unittest.TestCase):
    def validation(self,count=9):
        return dict(model_sha256='m',domain='cpu0-hot',training_groups=['train'],
                    records=[dict(group=str(i),predicted_ratio=.9,measured_ratio=.95,scope_matched=True) for i in range(count)])

    def test_sparse_groups_have_no_finite_confidence_bound(self):
        bound,meta=conformal(self.validation(5),'m',.9,'new','cpu0-hot')
        self.assertIsNone(bound);self.assertEqual(meta['status'],'too-few-independent-groups')
        bound,_=conformal(self.validation(),'m',.9,'new','cpu0-hot')
        self.assertGreater(bound,0)

    def test_query_training_and_calibration_leaks_are_rejected(self):
        for group in ('train','0'):
            with self.assertRaises(ValueError):conformal(self.validation(),'m',.9,group,'cpu0-hot')
        with self.assertRaises(ValueError):conformal(self.validation(),'other',.9,'new','cpu0-hot')
        with self.assertRaises(ValueError):conformal(self.validation(),'m',.9,'new','cpu1-cold')

    def test_all_candidates_remain_and_baselines_do_not_mix(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);out=root/'out';out.mkdir()
            records=[dict(id=str(i),workload='same',baseline_id=base,kind='measured',
                          control=[1]*6,candidate=[cost]*6,coverage={})
                     for i,(base,cost) in enumerate([('a',.99),('a',1.5),('b',.5)])]
            write(root/'plan.json',dict(records=records))
            result=rank(root/'plan.json',out)
            self.assertEqual(len(result['records']),3);self.assertEqual(len(result['comparisons']),1)
            for row in result['records']:
                self.assertEqual(row['automatic_action'],'none')
                self.assertNotIn('advance',row);self.assertNotIn('reject',row)

    def test_finite_residual_bound_requires_matching_coverage(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);write(root/'validation.json',self.validation())
            base=dict(id='new',workload='shape',baseline_id='original',kind='predicted',group='new',
                      domain='cpu0-hot',model_sha256='m',
                      scenarios=[dict(name='central',control_cycles=100,candidate_cycles=90)])
            for complete in (False,True):
                row=dict(base,coverage=dict(trace_complete=True,scope_matched=complete,
                         calibrated_instruction_fraction=1,gaps=[]))
                plan=root/('plan'+str(complete)+'.json');out=root/str(complete);out.mkdir()
                write(plan,dict(records=[row],validation=str(root/'validation.json')))
                record=rank(plan,out)['records'][0]
                self.assertEqual(record['evidence_level'],'calibrated-in-domain' if complete else 'exploratory')
                if complete:self.assertLess(record['gain_interval'][0],.1)

    def test_nonfinite_coverage_cannot_get_a_confidence_label(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);out=root/'out';out.mkdir()
            (root/'plan.json').write_text(json.dumps(dict(records=[dict(id='x',workload='x',baseline_id='x',kind='measured',
                  control=[1,1],candidate=[1,1],coverage=dict(calibrated_instruction_fraction=float('nan')))])))
            with self.assertRaises(ValueError):rank(root/'plan.json',out)


class ProgramTests(unittest.TestCase):
    def test_memory_order_crosses_vector_callback_line_boundaries(self):
        import gzip
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'program.gz'
            operations=[dict(name='sw',family='scalar-store',context=None,gaps=[],read=[],write=[]),
                        dict(name='lw',family='scalar-load',context=None,gaps=[],read=[],write=[])]
            with gzip.open(path,'wt') as stream:
                for event in [[0,0,[[63,4,True]]],[1,0,[[64,4,False]]]]:
                    stream.write(json.dumps(event)+'\n')
            cost=replay_thread(path,operations,{},'central','warm')
            self.assertEqual(cost['estimated_component_cycles'],8)
            self.assertEqual(cost['gaps']['cache-line-memory-order-is-conservative'],2)

    def test_actual_ime_encoding_has_pair_accumulator_dependency(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);out=root/'out';out.mkdir()
            insn=instruction(4096,'.4byte','',encoding='e207382b');insn['family']='ime-known-encoding'
            write(root/'inventory.json',dict(elf_sha256='x',functions=[dict(instructions=[insn])]))
            events=[dict(kind='instruction',seq=1,pc=4096,encoding='e207382b',size=4,
                         segment=0,vl=32,vtype=192,vlenb=32,vstart=0),
                    dict(kind='end',failure=False,recorded=1,instructions=1,truncated=False)]
            (root/'trace-cpu0.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
            compile_program(root,root/'inventory.json',out)
            op=json.loads((out/'operations.json').read_text())[0]
            self.assertEqual(set(op['write']),{'v16','v17'})
            self.assertTrue({'v16','v17','v14','v0'}.issubset(op['read']));self.assertFalse(op['gaps'])

    def test_footer_cannot_claim_fewer_executed_instructions(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);out=root/'out';out.mkdir()
            write(root/'inventory.json',dict(elf_sha256='x',functions=[dict(instructions=[instruction(0,'addi','t0,t0,1')])]))
            events=[dict(kind='instruction',seq=1,pc=0,encoding='00000013',size=4,segment=0),
                    dict(kind='end',failure=False,recorded=1,instructions=0,truncated=True)]
            (root/'trace-cpu0.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
            with self.assertRaises(ValueError):compile_program(root,root/'inventory.json',out)


if __name__=='__main__':unittest.main()
