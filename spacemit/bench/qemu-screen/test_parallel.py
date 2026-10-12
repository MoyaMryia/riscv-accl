"""检查混合核心分组边界。"""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('parallel', Path(__file__).with_name('parallel.py'))
parallel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parallel)


def fixture():
    records = []
    for cpu in range(20):
        performance = cpu < 8
        records.append({'cpu': cpu, 'kind': 'P' if performance else 'E',
            'package': 0, 'core': cpu, 'node': 0,
            'siblings': [cpu, cpu+20] if performance else [cpu],
            'l2_shared': [cpu] if performance else list(range(cpu//4*4, cpu//4*4+4))})
    for item in records[:8]:
        other = dict(item)
        other['cpu'] += 20
        records.append(other)
    return records


class CoreGroups(unittest.TestCase):
    def test_hybrid_and_smt(self):
        groups = parallel.groups(fixture(), 4, set())
        self.assertEqual([g['cpus'] for g in groups], [list(range(n, n+4)) for n in (0, 4, 8, 12, 16)])
        self.assertEqual([g['kind'] for g in groups], ['P', 'P', 'E', 'E', 'E'])

    def test_partial_cluster_stays_separate(self):
        groups = parallel.groups(fixture(), 4, {8})
        self.assertEqual([g['cpus'] for g in groups if g['kind'] == 'E'],
                         [list(range(12, 16)), list(range(16, 20))])

    def test_reserved_sibling_reserves_core(self):
        groups = parallel.groups(fixture(), 4, {20})
        self.assertTrue(all(0 not in g['cpus'] and 20 not in g['cpus'] for g in groups))

    def test_numa_boundary(self):
        records = fixture()
        for item in records:
            item['node'] = item['core'] % 2
        for group in parallel.groups(records, 4, set()):
            self.assertEqual(len({cpu % 2 for cpu in group['cpus']}), 1)

    def test_cpu_range(self):
        self.assertEqual(parallel.cpu_list('0-3,7,9-10'), {0, 1, 2, 3, 7, 9, 10})
        with self.assertRaises(ValueError):
            parallel.cpu_list('3-1')


if __name__ == '__main__':
    unittest.main()
