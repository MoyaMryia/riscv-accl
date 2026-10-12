#!/usr/bin/env python3
"""Test source guards, isolated patches and the prefill protocol."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import prepare
import prefill


class Candidates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = prepare.REPO/'lab/local-reference/source-a990751-clean'
        if not cls.source.is_dir():
            raise unittest.SkipTest('fixed local source is absent')
        cls.temporary = tempfile.TemporaryDirectory(prefix='k1-prepare-test-')
        cls.root = Path(cls.temporary.name)
        cls.manifests = {kind:prepare.generate(cls.source,cls.root/kind,kind)
                         for kind in ('control','A1','B1','C','D')}

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def text(self,kind,relative=prepare.OPS):
        return (self.root/kind/'overlay'/relative).read_text()

    def test_patch_round_trip(self):
        for kind, manifest in self.manifests.items():
            with self.subTest(kind=kind):
                target = self.root/('apply-'+kind)
                target.mkdir()
                for relative in manifest['files_sha256']:
                    if (self.source/relative).exists():
                        output = target/relative
                        output.parent.mkdir(parents=True,exist_ok=True)
                        shutil.copyfile(self.source/relative,output)
                subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(self.root/kind/'candidate.patch')],
                               cwd=target,check=True,capture_output=True)
                for relative, expected in manifest['files_sha256'].items():
                    self.assertEqual(prepare.digest((target/relative).read_bytes()),expected)

    def test_changed_source_rejected_before_write(self):
        real_digest = prepare.digest
        victim = (self.source/'src/models/qwen35.cpp').read_bytes()
        with patch.object(prepare,'digest',side_effect=lambda data: '0'*64 if data == victim else real_digest(data)):
            with self.assertRaisesRegex(ValueError,'snapshot source hash mismatch'):
                prepare.generate(self.source,self.root/'bad','C')
        self.assertFalse((self.root/'bad').exists())

    def test_existing_destination_preserved(self):
        old = (self.root/'A1/manifest.json').read_bytes()
        with self.assertRaisesRegex(ValueError,'destination exists'):
            prepare.generate(self.source,self.root/'A1','A1')
        self.assertEqual((self.root/'A1/manifest.json').read_bytes(),old)

    def test_a_uses_original_chunk_and_reducer(self):
        text = self.text('A1')
        self.assertIn('spine_k1_dot256((const ggml_fp16_t *) k_data, Q_q, &s)',text)
        baseline = (self.source/prepare.OPS).read_text()
        start = baseline.index('static void ggml_flash_attn_ext_reduce_partials(')
        end = baseline.index('\nstatic void ggml_compute_forward_flash_attn_ext_f16(',start)
        self.assertIn(baseline[start:end],text)
        self.assertIn('!spine_k1_flag("SPINE_K1_FA_GQA")',text)

    def test_b_keeps_both_workspace_planners(self):
        for path in (prepare.CPU,'ggml/src/ggml-cpu/spacemit/ime.cpp'):
            self.assertEqual(self.manifests['B1']['files_sha256'][path],self.manifests['control']['files_sha256'][path])
        self.assertEqual(self.manifests['B1']['gqa_stack_bytes_per_worker'],5184)
        self.assertIn('ggml_flash_attn_ext_reduce_partials(params, dst, nth, chunk_size)',self.text('B1'))

    def test_c_keeps_both_changes(self):
        text = self.text('C')
        self.assertIn('spine_k1_ssm_conv_cpu(params, dst)',text)
        self.assertIn('SPINE_GDN_PREFILL',text)
        self.assertIn('cparams.n_rs_seq == 0',self.text('C','src/models/qwen35.cpp'))
        probe = (self.root/'C/test-c-state.cpp').read_text()
        self.assertIn('const std::vector<int> chunks = {32,1,31,32}',probe)
        self.assertIn('select_arm(0)',probe)
        self.assertIn('mode == 2 || mode == 3 ? "1" : "0"',probe)

    def test_d_keeps_graph_guards(self):
        text = self.text('D',prepare.CPU)
        self.assertIn('ggml_can_fuse(cgraph, node_n, pair, 2)',text)
        self.assertIn('node->ne[0] % 64 == 0',text)
        self.assertIn('if (ggml_cpu_disable_fusion || cplan->use_ref)',text)
        self.assertIn('ggml_compute_forward_rms_norm_mul_fused',text)

    def test_changed_anchor_rejected(self):
        text = (self.source/prepare.OPS).read_text()
        text = text.replace('            kq_vec_dot(DK, &s, 0, k_data, 0, Q_q, 0, 1);','')
        with self.assertRaisesRegex(ValueError,'unexpected source anchor'):
            prepare.attention(text,True,False)


class Protocol(unittest.TestCase):
    def test_abba_and_fixed_shapes(self):
        for arm in ('C1','C2','C3'):
            result = prefill.protocol(arm)
            self.assertEqual(result['order'],['C0',arm,arm,'C0'])
            self.assertEqual(result['prompt_tokens'],[512,2048])
            self.assertEqual(result['output_tokens'],[1,65])
        self.assertEqual(prefill.protocol('C3','C1')['order'],['C1','C3','C3','C1'])

    def test_invalid_comparisons_rejected(self):
        for candidate,reference in (('C0','C1'),('C1','C2'),('C3','C3'),('bad','C0')):
            with self.assertRaises(ValueError): prefill.protocol(candidate,reference)

    def test_environment_has_one_arm(self):
        with patch.dict(os.environ,{'SPINE_K1_FA_DECODE':'1','SPINE_GDN_PREFILL':'1','SPACEMIT_BAD':'1'},clear=True):
            env = prefill.arm_env('C1',Path('/candidate'))
        self.assertNotIn('SPINE_GDN_PREFILL',env)
        self.assertNotIn('SPINE_K1_FA_DECODE',env)
        self.assertNotIn('SPACEMIT_BAD',env)
        self.assertEqual(env['SPINE_K1_SSM_CONV'],'3')
        self.assertEqual(env['SPINE_K1_GEMM_ROUTE'],'3')

    def test_prepare_does_not_launch_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = type('Args',(),{'candidate':'C3','reference':'C0','destination':Path(tmp)/'plan','execute':False})()
            with patch.object(subprocess,'run',side_effect=AssertionError('process started')):
                result = prefill.compare(args)
            self.assertEqual(result['status'],'prepared')
            self.assertEqual(json.loads((args.destination/'protocol.json').read_text())['candidate'],'C3')


if __name__ == '__main__':
    unittest.main()
