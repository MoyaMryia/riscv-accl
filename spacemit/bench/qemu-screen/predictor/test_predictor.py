"""检查路径合并、错误停止、缓存范围及数据泄漏。"""
import json
import importlib.util
import hashlib
from pathlib import Path
import tempfile
import unittest

from analyze import evaluate, read_trace
from model import Cache, cache_replay, cfg, semantics, vector_context


def module(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent / (name + '.py'))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


class IntegrityTests(unittest.TestCase):
    def test_receipt_detects_tamper_and_missing(self):
        verify = module('verify-evidence')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'data').write_bytes(b'actual')
            sha = hashlib.sha256(b'actual').hexdigest()
            path = root / 'SHA256SUMS'
            path.write_text(sha + '  data\n')
            self.assertFalse(verify.receipt(path, root)['failures'])
            (root / 'data').write_bytes(b'changed')
            self.assertEqual(verify.receipt(path, root)['failures'][0]['status'], 'hash-mismatch')
            (root / 'data').unlink()
            self.assertEqual(verify.receipt(path, root)['failures'][0]['status'], 'missing')

    def test_receipt_rejects_path_outside_base(self):
        verify = module('verify-evidence')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'SHA256SUMS'
            path.write_text('0' * 64 + '  ../outside\n')
            self.assertEqual(verify.receipt(path, root)['failures'][0]['status'], 'outside-base')
            path.write_text('')
            with self.assertRaises(ValueError):
                verify.receipt(path, root)

    def test_native_sample_rejects_wrong_identity_and_duration(self):
        native = module('run-board-existing')
        sample = dict(candidate='conv', shape='C6144-T32', arm=1,
                      iterations=128, wall_ms=128.0, ms_per_call=1.0)
        native.validate_sample(sample, 'conv', 'C6144-T32', 1)
        with self.assertRaises(ValueError):
            native.validate_sample(sample, 'b2', 'C6144-T32', 1)
        sample['ms_per_call'] = 2.0
        with self.assertRaises(ValueError):
            native.validate_sample(sample, 'conv', 'C6144-T32', 1)


def instruction(pc,name,operands,encoding='00000013'):
    return {'address':pc,'bytes':4,'encoding':encoding,'objdump_mnemonic':name,'mnemonic':name,
            'operands':operands,'family':'vector-other' if name.startswith('v') else 'scalar-other'}


class VectorTests(unittest.TestCase):
    def test_full_vector(self):
        context,gap = vector_context(dict(vl=8,vtype=208,vlenb=32,vstart=0))
        self.assertIsNone(gap); self.assertEqual(context['vlmax'],8)

    def test_missing_registers(self):
        self.assertEqual(vector_context({})[1],'vector-register-unavailable')

    def test_illegal_vtype(self):
        self.assertEqual(vector_context(dict(vl=8,vtype=1<<63,vlenb=32,vstart=0))[1],'vector-type-illegal')

    def test_partial_vector_is_preserved(self):
        context,gap = vector_context(dict(vl=3,vtype=208,vlenb=32,vstart=0))
        self.assertEqual(context['vl'],3); self.assertIsNone(gap)

    def test_fractional_group(self):
        context,gap = vector_context(dict(vl=8,vtype=198,vlenb=32,vstart=0))
        self.assertEqual(context['lmul'],'1/4'); self.assertIsNone(gap)

    def test_vector_restart_is_gap(self):
        self.assertEqual(vector_context(dict(vl=8,vtype=208,vlenb=32,vstart=1))[1],'vector-context-unsupported')

    def test_accumulator_dependency(self):
        read,written,gaps = semantics(instruction(0,'vfmacc.vv','v8,v16,v24'),dict(lmul='8',tail_agnostic=True,mask_agnostic=True))
        self.assertIn('v15',read); self.assertIn('v15',written)
        self.assertFalse(gaps)

    def test_unknown_instruction_is_gap(self):
        self.assertTrue(semantics(instruction(0,'new.op','a0,a1'),None)[2])

    def test_scalar_float_transfer(self):
        read,written,_ = semantics(instruction(0,'vfmv.f.s','fa0,v8'),dict(lmul='1',tail_agnostic=True,mask_agnostic=True))
        self.assertIn('v8',read); self.assertIn('f10',written)

    def test_mask_is_dependency(self):
        read,_,gaps = semantics(instruction(0,'vfmacc.vv','v8,v16,v24,v0.t'),dict(lmul='1',tail_agnostic=True,mask_agnostic=True))
        self.assertIn('v0',read); self.assertIn('masked-lane-dependencies-conservative',gaps)

    def test_mask_uses_one_register(self):
        read,_,_ = semantics(instruction(0,'vfmacc.vv','v8,v16,v24,v0.t'),dict(lmul='8',tail_agnostic=True,mask_agnostic=True))
        self.assertNotIn('v1',read)

    def test_segment_store_reads_all_fields(self):
        read,written,gaps = semantics(instruction(0,'vsseg3e32.v','v8,(a0)'),dict(lmul='1',sew=32,tail_agnostic=True,mask_agnostic=True))
        self.assertTrue({'v8','v9','v10','x10'}<=read);self.assertFalse(written);self.assertFalse(gaps)

    def test_widened_accumulator_has_double_group(self):
        read,written,gaps = semantics(instruction(0,'vfwmacc.vv','v8,v16,v24'),dict(lmul='4',sew=16,tail_agnostic=True,mask_agnostic=True))
        self.assertIn('v15',written);self.assertIn('v15',read);self.assertNotIn('v20',read);self.assertFalse(gaps)

    def test_whole_move_ignores_lmul(self):
        read,written,gaps = semantics(instruction(0,'vmv2r.v','v8,v16'),dict(lmul='8',sew=32,tail_agnostic=True,mask_agnostic=True))
        self.assertEqual(written,{'v8','v9'});self.assertEqual(read,{'v16','v17'});self.assertFalse(gaps)


class CFGTests(unittest.TestCase):
    def test_diamond_retains_both_configs(self):
        function = {'instructions':[
            instruction(0,'beq','a0,zero,10 <right>'),instruction(4,'vsetvli','t0,zero,e32,m1,ta,ma'),
            instruction(8,'c.j','14 <join>'),instruction(12,'addi','a0,a0,0'),
            instruction(16,'vsetvli','t0,zero,e16,m2,ta,ma'),instruction(20,'vfmul.vv','v8,v16,v24'),
            instruction(24,'c.jr','ra')]}
        record = cfg(function)
        self.assertEqual(record['ambiguous_vector_uses'],1)
        self.assertEqual(len(record['vector_uses'][0]['contexts']),2)

    def test_call_invalidates_vector_type(self):
        function = {'instructions':[instruction(0,'vsetvli','t0,zero,e32,m1,ta,ma'),
            instruction(4,'jal','ra,100 <callee>'),instruction(8,'vfmul.vv','v8,v16,v24')]}
        self.assertEqual(cfg(function)['vector_uses'][0]['contexts'],['unknown-after-call'])

    def test_loop_reaches_fixed_point(self):
        function = {'instructions':[instruction(0,'vsetivli','t0,8,e32,m1,ta,ma'),
            instruction(4,'vfmul.vv','v8,v16,v24'),instruction(8,'bne','a0,zero,4 <loop>')]}
        self.assertEqual(cfg(function)['backedges'],[(8,4)])


class CacheTests(unittest.TestCase):
    def test_lru_dirty_eviction(self):
        cache = Cache(128,64,2)
        cache.access(0,True);cache.access(1,False);cache.access(1,False)
        self.assertEqual(cache.access(2,False),(False,0))
        self.assertEqual(cache.writebacks,1)

    def test_cache_bad_dimensions(self):
        with self.assertRaises(ValueError): Cache(100,64,2)

    def test_private_l1_shared_l2_and_line_cross(self):
        threads = {1:[dict(kind='memory',address=63,bytes=2,store=False)],
                   2:[dict(kind='memory',address=63,bytes=2,store=False)]}
        params = dict(thread_to_core={'1':0,'2':1},core_to_cluster={'0':0,'1':0},
                      line_bytes=64,l1_bytes=128,l2_bytes=256,l1_ways=2,l2_ways=2)
        result = cache_replay(threads,params,'round-robin')
        self.assertEqual(result['l1']['0']['misses'],2)
        self.assertEqual(result['l1']['1']['misses'],2)
        self.assertEqual(result['l2']['0']['misses'],2)
        self.assertEqual(result['l2']['0']['hits'],2)
        self.assertIsNone(result['DDR_bytes']);self.assertIsNone(result['cycles'])


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def trace(self,encoding='00000013',end=True):
        row = dict(kind='instruction',cpu=0,seq=1,segment=1,pc=0,size=4,encoding=encoding,
                   vl=8,vtype=208,vlenb=32,vstart=0,v0='00'*32)
        rows = [row]
        if end: rows.append(dict(kind='end',recorded=1,instructions=1,truncated=False,failure=False))
        path = self.root/'trace.jsonl';path.write_text(''.join(json.dumps(r)+'\n' for r in rows));return path

    def test_actual_bytes_are_required(self):
        with self.assertRaises(ValueError): read_trace(self.trace('00000017'),{'instructions':[instruction(0,'addi','zero,zero,0')]})

    def test_trace_footer_is_required(self):
        with self.assertRaises(ValueError): read_trace(self.trace(end=False),{'instructions':[instruction(0,'addi','zero,zero,0')]})

    def test_complete_trace(self):
        _,summary = read_trace(self.trace(),{'instructions':[instruction(0,'addi','zero,zero,0')]})
        self.assertEqual(summary['instructions'],1)

    def test_memory_byte_overlap_dependency(self):
        path=self.trace(); rows=[json.loads(s) for s in path.read_text().splitlines()]
        second=rows[0] | {'seq':2,'pc':4}
        values=[rows[0],dict(kind='memory',seq=1,address=65,bytes=4,store=True),second,
                dict(kind='memory',seq=2,address=66,bytes=2,store=False),rows[1] | {'recorded':2,'instructions':2}]
        path.write_text(''.join(json.dumps(r)+'\n' for r in values))
        _,summary=read_trace(path,{'instructions':[instruction(0,'addi','a0,a0,1'),instruction(4,'addi','a0,a0,1')]})
        self.assertEqual(summary['address_dependency_edges']['RAW'],1)
        self.assertEqual(summary['address_dependency_edges']['overlap_bytes'],2)

    def evaluate(self,rows,pairs=None):
        protocol = Path(__file__).with_name('validation-protocol.json')
        data = self.root/'data.json';data.write_text(json.dumps({'records':rows,'pairs':pairs or []}))
        return evaluate(protocol,data)

    def test_empty_measurements_are_not_zero_error(self):
        result = self.evaluate([])
        self.assertEqual(result['status'],'insufficient-independent-data')
        self.assertNotIn('cycle_error_median',result)

    def test_group_leakage_is_rejected(self):
        rows = [dict(id='a',group='scalar-dependent',split='train',predicted_cycles=1,measured_cycles=1),
                dict(id='b',group='scalar-dependent',split='test',predicted_cycles=1,measured_cycles=1)]
        with self.assertRaises(ValueError): self.evaluate(rows)

    def test_small_test_set_is_not_accepted(self):
        rows = [dict(id='a',group='scalar-dependent',split='train',predicted_cycles=1,measured_cycles=1),
                dict(id='b',group='mixed-gdn',split='test',predicted_cycles=1,measured_cycles=1)]
        self.assertEqual(self.evaluate(rows)['status'],'insufficient-independent-data')

    def test_order_error_and_false_rejection(self):
        rows = [dict(id='a',group='scalar-dependent',split='train',predicted_cycles=100,measured_cycles=100),
                dict(id='b',group='mixed-gdn',split='test',predicted_cycles=100,measured_cycles=100),
                dict(id='c',group='mixed-gdn',split='test',predicted_cycles=110,measured_cycles=90)]
        result = self.evaluate(rows,[dict(control='b',candidate='c')])
        self.assertEqual(result['ranking_errors'],1)
        self.assertEqual(result['false_rejection_risks'],1)
        self.assertEqual(result['pairs'][0]['decision'],'needs-board')

    def test_nan_cycle_is_rejected(self):
        rows = [dict(id='a',group='scalar-dependent',split='train',predicted_cycles=float('nan'),measured_cycles=1)]
        with self.assertRaises(ValueError): self.evaluate(rows)


if __name__ == '__main__': unittest.main()
