"""检查完整调用中的被调用函数、返回边界与向量访存缺失。"""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('fragment_invocation', HERE/'fragment-invocation.py')
invocation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(invocation)


class InvocationTests(unittest.TestCase):
    def fixture(self, directory):
        elf = Path(directory)/'fixture.elf'
        data = bytearray(0x400)
        ident = b'\x7fELF\x02\x01\x01'+b'\0'*9
        struct.pack_into('<16sHHIQQQIHHHHHH', data, 0, ident, 2, 243, 1, 0x1000, 0, 0x300, 0, 64, 0, 0, 64, 4, 0)
        text = bytearray(40)
        struct.pack_into('<III', text, 0, 0x020000ef, 0x00013083, 0x00008067)
        struct.pack_into('<IH', text, 32, 0x00a58023, 0x8082)
        data[0x100:0x128] = text
        data[0x180:0x186] = b'\0root\0'
        struct.pack_into('<IBBHQQ', data, 0x200, 1, 2, 0, 1, 0x1000, 12)
        struct.pack_into('<IIQQQQIIQQ', data, 0x340, 0, 1, 6, 0x1000, 0x100, len(text), 0, 0, 2, 0)
        struct.pack_into('<IIQQQQIIQQ', data, 0x380, 0, 3, 0, 0, 0x180, 6, 0, 0, 1, 0)
        struct.pack_into('<IIQQQQIIQQ', data, 0x3c0, 0, 2, 0, 0, 0x200, 24, 2, 0, 8, 24)
        elf.write_bytes(data)
        rows = [dict(kind='begin', cpu=0, entry=0x1000, return_pc=0x8000)]
        for seq, pc, size, encoding in [(1,0x1000,4,'020000ef'), (2,0x1020,4,'00a58023'),
                                        (3,0x1024,2,'8082'), (4,0x1004,4,'00013083'), (5,0x1008,4,'00008067')]:
            rows.append(dict(kind='instruction', cpu=0, seq=seq, pc=pc, size=size, encoding=encoding))
            if seq in (2,4):
                rows.append(dict(kind='memory', seq=seq, address=0x9000, bytes=1 if seq==2 else 8, store=seq==2))
        rows.append(dict(kind='end', instructions=5, recorded=5, memory_callbacks=2,
                         closed=True, truncated=False, failure=False))
        return elf, rows

    def run_audit(self, directory, elf, rows):
        path = Path(directory)/'trace.jsonl'
        path.write_text(''.join(json.dumps(row)+'\n' for row in rows))
        return invocation.audit(path, elf, 'root')

    def mutate(self, change):
        with tempfile.TemporaryDirectory() as directory:
            elf, rows = self.fixture(directory)
            change(rows)
            with self.assertRaises(invocation.CoverageError):
                self.run_audit(directory, elf, rows)

    def test_callee_and_compressed_return_are_included(self):
        with tempfile.TemporaryDirectory() as directory:
            elf, rows = self.fixture(directory)
            result, instructions = self.run_audit(directory, elf, rows)
            self.assertEqual(result['instructions'],5)
            self.assertEqual(result['instructions_outside_symbol'],2)
            self.assertEqual(result['memory_bytes'],dict(load=8,store=1))
            self.assertEqual(result['compressed_instructions'],1)
            self.assertIsNone(result['K1_cycles'])
            self.assertEqual(instructions[1]['operation']['reads'],['x11','x10'])

    def test_truncation_is_failure(self):
        self.mutate(lambda rows:rows[-1].update(truncated=True))

    def test_open_call_is_failure(self):
        self.mutate(lambda rows:rows[-1].update(closed=False))

    def test_missing_memory_is_failure(self):
        def change(rows):
            del rows[3]
            rows[-1]['memory_callbacks']=1
        self.mutate(change)

    def test_changed_encoding_is_failure(self):
        self.mutate(lambda rows:rows[1].update(encoding='00000013'))

    def test_wrong_return_target_is_failure(self):
        self.mutate(lambda rows:rows[0].update(return_pc=0x1020))

    def test_missing_callee_is_failure(self):
        def change(rows):
            del rows[2:5]
            for i,row in enumerate(r for r in rows if r['kind']=='instruction'):
                row['seq']=i+1
            for row in rows:
                if row['kind']=='memory':row['seq']=2
            rows[-1].update(instructions=3,recorded=3,memory_callbacks=1)
        self.mutate(change)

    def test_event_after_end_is_failure(self):
        self.mutate(lambda rows:rows.append(copy.deepcopy(rows[1])))

    def test_unknown_encoding_is_not_default_arithmetic(self):
        for word,size in [(0xffffffff,4),(0x0000100f,4),(0,2),(0x6101,2)]:
            with self.assertRaises(invocation.CoverageError):invocation.decode(word,size)

    def test_zero_register_has_no_dependency(self):
        op=invocation.decode(0x00000013,4)
        self.assertEqual(op['reads'],[])
        self.assertEqual(op['writes'],[])

    def test_m8_move_has_all_destination_registers(self):
        op=invocation.decode(0x5e05c057,4)
        result=invocation.validate_vector(dict(vl=256,vtype=195,vlenb=32,vstart=0),op)
        self.assertEqual(result['writes'],[f'v{i}' for i in range(8)])
        self.assertIn('x11',result['reads'])

    def test_vector_store_uses_dynamic_vl(self):
        op=invocation.decode(0x02078027,4)
        result=invocation.validate_vector(dict(vl=256,vtype=195,vlenb=32,vstart=0),op)
        self.assertEqual(result['memory_bytes'],256)
        self.assertTrue(result['store'])
        self.assertTrue(all(f'v{i}' in result['reads'] for i in range(8)))
        for state in ({},dict(vl=257,vtype=195,vlenb=32,vstart=0),dict(vl=256,vtype=195,vlenb=32,vstart=1)):
            with self.assertRaises(invocation.CoverageError):invocation.validate_vector(state,op)

    def test_compressed_backward_branch_target(self):
        op=invocation.decode(0xfa75,2)
        self.assertEqual(op['offset'],-12)
        self.assertEqual(op['reads'],['x12'])


if __name__=='__main__':unittest.main()
