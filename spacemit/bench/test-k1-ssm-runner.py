#!/usr/bin/env python3
"""Check isolated-link and activation gates without a board or cloud request."""
import importlib.util
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
def module(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'))
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
runner=module('k1-ssm-conv'); patcher=module('make-k1-ssm-conv')

class Gates(unittest.TestCase):
    def test_replace_only_requested_objects(self):
        line=': && g++ -shared -o bin/lib.so a/ops.cpp.o b/ime.cpp.o a/unchanged.cpp.o bin/libggml-base.so && :'
        argv=runner.rewrite_link(line,Path('/tmp/candidate.so'),{'/ops.cpp.o':Path('/tmp/ops.o'),'/ime.cpp.o':Path('/tmp/ime.o')})
        self.assertIn('/tmp/candidate.so',argv); self.assertIn('/tmp/ops.o',argv); self.assertIn('/tmp/ime.o',argv)
        self.assertIn('a/unchanged.cpp.o',argv); self.assertIn('bin/libggml-base.so',argv)
    def test_missing_or_duplicate_object_rejected(self):
        for objects in ('a/unchanged.o','a/ops.cpp.o b/ops.cpp.o'):
            with self.assertRaises(ValueError):
                runner.rewrite_link(': && g++ -shared -o lib.so '+objects+' && :',Path('/tmp/lib.so'),{'/ops.cpp.o':Path('/tmp/ops.o')})
    def test_foreign_link_recipe_rejected(self):
        with self.assertRaises(ValueError): runner.rewrite_link('g++ -shared -o lib.so a/ops.cpp.o',Path('/tmp/lib.so'),{'/ops.cpp.o':Path('/tmp/ops.o')})
    def test_wrong_mode_backend_or_rs_rejected(self):
        runner.check_marker('K1_SSM_CONV mode=2 layout=channels rs=0 cpu_only=1',2)
        for marker in ('mode=0 layout=time rs=0 cpu_only=1','mode=2 layout=channels rs=3 cpu_only=1','mode=2 layout=channels rs=0 cpu_only=0'):
            with self.assertRaises(ValueError): runner.check_marker('K1_SSM_CONV '+marker,2)
    def test_patch_cannot_be_applied_twice(self):
        with self.assertRaises(ValueError): patcher.generate(patcher.PATHS[0],'spine_k1_ssm existing candidate')
    def test_drifted_baseline_rejected(self):
        with self.assertRaises(ValueError): patcher.generate(patcher.PATHS[0],'// missing original convolution')

if __name__=='__main__': unittest.main()
