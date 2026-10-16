#!/usr/bin/env python3
"""检查源码身份、配置隔离、模型拒绝与源码重建。"""
import importlib.util
import itertools
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import package
spec=importlib.util.spec_from_file_location('launcher',HERE/'run.py')
launcher=importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)

class PackageTests(unittest.TestCase):
    def test_profile_isolation(self):
        polluted={'SPINE_K1_FA_GQA':'1','SPINE_GDN_PREFILL':'1','SPINE_UNKNOWN':'1',
                  'SPACEMIT_CORE_ARCH':'wrong','LLAMA_ARG_MODEL':'wrong','GGML_BACKEND_PATH':'wrong','OMP_NUM_THREADS':'8',
                  'LD_PRELOAD':'wrong','LD_AUDIT':'wrong','LD_LIBRARY_PATH':'wrong'}
        with patch.dict(os.environ,polluted):
            for profile in ('baseline','optimized','c1','c2-r2','b1-r2','prefill','all'):
                env=launcher.environment(profile,Path('/new/bin'),Path('/spert'),Path('/tcm'))
                self.assertEqual(env['LD_LIBRARY_PATH'],'/new/bin:/tcm:/spert/lib')
                self.assertNotIn('LD_PRELOAD',env)
                self.assertNotIn('LD_AUDIT',env)
                for key in ('SPINE_UNKNOWN','SPACEMIT_CORE_ARCH','LLAMA_ARG_MODEL','GGML_BACKEND_PATH','OMP_NUM_THREADS'):
                    self.assertNotIn(key,env)
                self.assertEqual(env['SPINE_K1_GEMM_ROUTE'],'0' if profile=='baseline' else '3')
                self.assertEqual(env['SPINE_K1_TRACE'],'0')
                self.assertEqual(env['SPINE_IME_SCALAR_SCHEDULE'],'0')
                self.assertEqual(env['SPINE_GDN_PREFILL'],env['SPINE_K1_GDN_REVISION'])

    def test_independent_switches(self):
        for bits in itertools.product((False,True),repeat=3):
            enabled=[n for n,b in zip(launcher.CANDIDATES,bits) if b]
            disabled=[n for n,b in zip(launcher.CANDIDATES,bits) if not b]
            env=launcher.environment('experimental',Path('/bin'),Path('/spert'),Path('/tcm'),enabled,disabled)
            self.assertEqual(env['SPINE_K1_SSM_CONV'],'3' if bits[0] else '0')
            self.assertEqual(env['SPINE_GDN_PREFILL'],'1' if bits[1] else '0')
            self.assertEqual(env['SPINE_K1_FA_GQA'],'1' if bits[2] else '0')
        with self.assertRaises(ValueError):
            launcher.environment('optimized',Path('/bin'),Path('/spert'),Path('/tcm'),['c1'])
        with self.assertRaises(ValueError):
            launcher.environment('experimental',Path('/bin'),Path('/spert'),Path('/tcm'),['c1'],['c1'])

    def test_reject_model(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/package.manifest()['models']['2B']['filename']
            f.write_bytes(b'wrong model')
            with self.assertRaises(ValueError): launcher.verify_model(f)

    def test_reject_binary(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'bin').mkdir(); f=root/'bin/llama-server'; f.write_bytes(b'first')
            (root/'build-receipt.json').write_text(json.dumps({'package':package.manifest()['version'],'binaries':{'llama-server':package.sha(f)}}))
            launcher.verify_binaries(root)
            extra=root/'bin/libspine_tcm.so';extra.write_bytes(b'undeclared library')
            with self.assertRaises(ValueError): launcher.verify_binaries(root)
            extra.unlink()
            f.write_bytes(b'changed')
            with self.assertRaises(ValueError): launcher.verify_binaries(root)

    def test_source_rebuild(self):
        vendor=Path(os.environ['K1_TEST_VENDOR_SOURCE'])
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'source'
            receipt=package.prepare(vendor,root)
            self.assertEqual(receipt['files'],3270)
            with self.assertRaises(ValueError): package.prepare(vendor,root)
            changed=root/'ggml/src/ggml-cpu/ops.cpp'
            changed.write_text(changed.read_text()+'\n')
            with self.assertRaises(ValueError): package.verify(root)

if __name__=='__main__':
    if not os.environ.get('TMUX'): raise SystemExit('Run tests in tmux.')
    unittest.main(verbosity=2)
