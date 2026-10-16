"""检查实际二进制接入对缺失事件与未知状态的拒绝行为。"""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('binary_input',Path(__file__).with_name('binary-input.py'))
binary=importlib.util.module_from_spec(spec);spec.loader.exec_module(binary)


class BinaryInputTests(unittest.TestCase):
    def fixture(self):
        body=dict(encodings={4096:0x0005b283,4100:0xfff50513,4104:0xfe051ce3},
            instructions=[dict(pc=4096,kind='load',memory_bytes=8)])
        rows=[dict(kind='instruction',seq=1,segment=1,pc=4096,size=4,encoding='0005b283'),
            dict(kind='memory',seq=1,address=8192,bytes=8,store=False),
            dict(kind='instruction',seq=2,segment=1,pc=4100,size=4,encoding='fff50513'),
            dict(kind='instruction',seq=3,segment=1,pc=4104,size=4,encoding='fe051ce3'),
            dict(kind='end',instructions=3,recorded=3,memory_callbacks=1,truncated=False,failure=False)]
        return body,rows

    def audit(self,body,rows):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'trace.jsonl';p.write_text(''.join(json.dumps(row)+'\n' for row in rows))
            return binary.trace(p,body,[1])

    def test_complete_dynamic_memory_path(self):
        body,rows=self.fixture();value=self.audit(body,rows)
        self.assertEqual(value['distinct_virtual_bytes'],8)
        self.assertEqual(value['iterations'],[1])

    def test_missing_memory_is_failure(self):
        body,rows=self.fixture();del rows[1]
        with self.assertRaises(binary.CoverageError):self.audit(body,rows)

    def test_truncated_trace_is_failure(self):
        body,rows=self.fixture();rows[-1]['truncated']=True
        with self.assertRaises(binary.CoverageError):self.audit(body,rows)

    def test_changed_encoding_is_failure(self):
        body,rows=self.fixture();rows[0]['encoding']='00000013'
        with self.assertRaises(binary.CoverageError):self.audit(body,rows)

    def test_incomplete_loop_is_failure(self):
        body,rows=self.fixture();del rows[3];rows[-1].update(instructions=2,recorded=2)
        with self.assertRaises(binary.CoverageError):self.audit(body,rows)

    def test_store_is_failure(self):
        body,rows=self.fixture();rows[1]['store']=True
        with self.assertRaises(binary.CoverageError):self.audit(body,rows)

    def test_vector_state_is_required(self):
        body,rows=self.fixture();body['instructions'][0]['kind']='vload';body['instructions'][0]['memory_bytes']=32
        rows[1]['bytes']=32
        with self.assertRaises(binary.CoverageError):self.audit(body,rows)
        rows[0].update(vl=32,vtype=192,vlenb=32,vstart=0)
        self.assertEqual(self.audit(body,rows)['distinct_virtual_bytes'],32)

    def test_unknown_encoding_has_no_semantics(self):
        with self.assertRaises(binary.CoverageError):binary.decode(0xffffffff)

    def test_register_dependency_comes_from_bytes(self):
        op=binary.decode(0x02e28333)
        self.assertEqual(op['kind'],'mul')
        self.assertEqual(op['reads'],['x5','x14'])
        self.assertEqual(op['writes'],['x6'])

    def test_non_elf_is_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'bad.elf';p.write_bytes(b'not an ELF')
            with self.assertRaises(binary.CoverageError):binary.function(p,'kernel')


if __name__=='__main__':unittest.main()
