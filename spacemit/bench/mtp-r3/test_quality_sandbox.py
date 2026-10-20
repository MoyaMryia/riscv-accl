"""检查代码沙箱只有一份定义，并拒绝运行时逃逸名字。"""
import importlib.util
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
QUALITY = ROOT / 'release-candidate/tests/quality.py'
BENCH = ROOT / 'bench/mtp-quality-checks.py'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SandboxTests(unittest.TestCase):
    def test_bench_entry_exports_the_release_candidate_definition(self):
        bench = load('sandbox_bench', BENCH)
        quality = load('sandbox_quality', QUALITY)
        self.assertEqual(bench.SAFE_BUILTINS, quality.SAFE_BUILTINS)
        self.assertEqual(bench.SAFE_ATTRIBUTES, quality.SAFE_ATTRIBUTES)
        self.assertEqual(bench.FORBIDDEN_NAMES, quality.FORBIDDEN_NAMES)
        self.assertTrue(callable(bench.checked_tree))
        self.assertIn('hash', bench.SAFE_BUILTINS)

    def test_runtime_escape_names_are_rejected(self):
        quality = load('sandbox_quality_rules', QUALITY)
        for name in ('getattr', 'eval', 'open', 'vars', 'globals'):
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, 'prohibited runtime name'):
                    quality.checked_tree('def f(x):\n    return ' + name + '(x)\n')
        with self.assertRaisesRegex(ValueError, 'unsupported attribute'):
            quality.checked_tree("def f(x):\n    return x.__class__\n")
        self.assertTrue(quality.checked_tree('def f(items):\n    return [hash(item) for item in items]\n'))

    def test_missing_builtin_name_is_a_loud_error_at_import(self):
        quality = load('sandbox_quality_names', QUALITY)
        import builtins
        missing = [name for name in quality.SAFE_BUILTINS if not hasattr(builtins, name)]
        self.assertEqual(missing, [])
        self.assertEqual([name for name in quality.FORBIDDEN_NAMES if name in quality.SAFE_BUILTINS], [])


if __name__ == '__main__':
    unittest.main()
