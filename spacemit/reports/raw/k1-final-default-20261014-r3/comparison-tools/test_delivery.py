"""核验交付补丁的重放结果和默认启动的环境隔离。"""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import build_default

ROOT = Path(__file__).resolve().parents[3]
REFERENCE = ROOT / 'spacemit/release-candidate'


class DeliveryTests(unittest.TestCase):
    def test_patch_replay_and_environment(self):
        for mask, threads, batch in ((0, 4, 32), (7, 2, 128)):
            with self.subTest(mask=mask), tempfile.TemporaryDirectory(prefix='k1-default-preflight-') as temp:
                folder = Path(temp)
                policy = folder / 'simulated-policy.json'
                data = dict(version='preflight-only', config=dict(mask=mask, threads=threads, ubatch=batch),
                    search_converged=True, quality={n: dict(checks=106, control='0' * 64, selected='0' * 64)
                        for n in ('2B', '4B')})
                policy.write_text(json.dumps(data))
                result = build_default.generate(REFERENCE, ROOT / 'lab/integrated-20261013/source',
                    ROOT / 'lab/local-reference/source-a990751-clean', policy, folder / 'generated')
                self.assertEqual(result['files'], 3271)
                package = folder / 'generated/package'
                pkg = build_default.load(package)
                replay = pkg.prepare(ROOT / 'lab/local-reference/source-a990751-clean', folder / 'replay')
                self.assertEqual(result, replay)
                sys.modules['package'] = pkg
                spec = importlib.util.spec_from_file_location('delivery_start', package / 'start.py')
                start = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(start)
                with patch.dict(os.environ, dict(SPINE_K1_SSM_CONV='3', LLAMA_ARG_THREADS='8',
                    OMP_NUM_THREADS='8', LD_PRELOAD='/tmp/untrusted.so', LD_LIBRARY_PATH='/tmp/untrusted')):
                    env = start.environment(folder / 'bin', folder / 'spert', folder / 'tcm')
                self.assertFalse(any(n.startswith(('SPINE_', 'LLAMA_', 'OMP_')) for n in env))
                self.assertNotIn('LD_PRELOAD', env)
                self.assertEqual(env['LD_LIBRARY_PATH'], ':'.join(map(str,
                    (folder / 'bin', folder / 'tcm', folder / 'spert/lib'))))
                fixture = (package / 'tests/test-state.cpp').read_bytes()
                self.assertEqual(fixture, (ROOT / 'lab/final-default-20261013/test-state-all-masks.cpp').read_bytes())
                subprocess.run(['g++', '-std=c++17', '-fsyntax-only',
                    '-I' + str(folder / 'generated/source/include'),
                    '-I' + str(folder / 'generated/source/ggml/include'),
                    str(package / 'tests/test-default-state.cpp')], check=True)


if __name__ == '__main__':
    if not os.environ.get('TMUX'):
        raise SystemExit('Run the tests in tmux.')
    unittest.main()
