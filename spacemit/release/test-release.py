#!/usr/bin/env python3
"""Check release integrity and prevent silently enabling rejected experiments."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('serve',HERE/'run-server.py')
serve=importlib.util.module_from_spec(spec); spec.loader.exec_module(serve)


class Release(unittest.TestCase):
    def test_patch_checksum_and_measured_source_pins(self):
        manifest=json.loads((HERE/'manifest.json').read_text())
        self.assertEqual(hashlib.sha256((HERE/manifest['patch']).read_bytes()).hexdigest(),manifest['patch_sha256'])
        routing=json.loads((HERE.parent/'reports/raw/k1-gemm-routing-20261003-005740/provenance.json').read_text())
        self.assertEqual(manifest['patched_source_sha256']['ggml/src/ggml-cpu/spacemit/ime.cpp'],routing['candidate_source_sha256'])
        self.assertEqual(manifest['source_commit'],'a990751d55a4c54acf2bb77d44282c2093652359')
    def test_reject_changed_model_and_unknown_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            model=Path(directory)/'model.gguf'; model.write_bytes(b'pinned model fixture')
            manifest={'models':{'2B':{'filename':model.name,'sha256':hashlib.sha256(model.read_bytes()).hexdigest()}}}
            serve.verify_model(model,manifest)
            model.write_bytes(b'changed model fixture')
            with self.assertRaises(ValueError): serve.verify_model(model,manifest)
            with self.assertRaises(ValueError): serve.verify_model(Path(directory)/'unknown.gguf',manifest)
    def test_matched_profiles_clear_experimental_environment(self):
        with patch.dict(os.environ,{'SPINE_IME_M1_K32':'1','SPINE_K1_SSM_CONV':'3','SPINE_SPEC_RS':'3'}):
            for profile,route in [('baseline','0'),('optimized','3')]:
                env=serve.environment(profile,'tcm:spert:release')
                self.assertEqual({k:v for k,v in env.items() if k.startswith('SPINE_')},
                    {'SPINE_FA_WIDE_TILE':'1','SPINE_FA_K1_LAYOUT':'0','SPINE_K1_GEMM_ROUTE':route})
                self.assertEqual(env['LD_LIBRARY_PATH'],'tcm:spert:release')
            self.assertEqual(os.environ['SPINE_IME_M1_K32'],'1')


if __name__=='__main__': unittest.main()
