"""检查片段比较在证据错误时保留候选并停止有效收益声明。"""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import tempfile
import unittest
from common import digest
from model import INITIAL

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('fragment_compare_test', HERE / 'fragment-compare.py')
fragment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fragment)


def elf_fixture(path):
    code = struct.pack('<IIII', 0x00e282b3, 0xfff50513, 0xfe051ce3, 0x00008067)
    names = b'\0kernel\0'
    symbols = bytes(24) + struct.pack('<IBBHQQ', 1, 0x12, 0, 1, 4096, len(code))
    symbol_offset = 64 + len(code) + len(names)
    section_offset = symbol_offset + len(symbols)
    header = struct.pack('<16sHHIQQQIHHHHHH', b'\x7fELF\x02\x01\x01' + bytes(9),
                         2, 243, 1, 4096, 0, section_offset, 0, 64, 0, 0, 64, 4, 0)
    sections = [(0,) * 10, (0, 1, 6, 4096, 64, len(code), 0, 0, 4, 0),
                (0, 3, 0, 0, 64 + len(code), len(names), 0, 0, 1, 0),
                (0, 2, 0, 0, symbol_offset, len(symbols), 2, 1, 8, 24)]
    path.write_bytes(header + code + names + symbols + b''.join(struct.pack('<IIQQQQIIQQ', *row) for row in sections))


class FragmentCompareTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        elf_fixture(self.root / 'fixture.elf')
        rows = []
        for iteration in range(3):
            for offset, encoding in enumerate(('00e282b3', 'fff50513', 'fe051ce3')):
                rows.append(dict(kind='instruction', seq=len(rows) + 1, segment=1,
                                 pc=4096 + 4 * offset, size=4, encoding=encoding))
        rows.append(dict(kind='end', instructions=9, recorded=9, memory_callbacks=0, truncated=False, failure=False))
        (self.root / 'trace.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in rows))
        for name in ('before.bin', 'after.bin', 'reference.bin'):
            (self.root / name).write_bytes(bytes(range(16)))
        shutil.copy2(HERE / 'state8.py', self.root / 'state8.py')
        self.save('model.json', dict(schema=8, parameters=copy.deepcopy(INITIAL),
                                     engine_files={'state8.py': digest(self.root / 'state8.py')}))
        arm = dict(elf=self.file('fixture.elf'), trace=self.file('trace.jsonl'), symbol='kernel', iterations=[3])
        self.manifest = dict(schema=1, id='unit-pair', primary_model='r8', baseline=arm, candidate=copy.deepcopy(arm),
            contract=dict(work_id='same-add', input_description='固定整数输入', boundary='循环体与计数回边',
                          compile_context='手工机器码测试夹具', live_inputs=['x5', 'x14'], live_outputs=['x5'],
                          memory_effects=['无访存'], equivalent_work_per_iteration=True, cpu=0, threads=1,
                          boundary_kind='steady-loop', memory_scenario='no-memory', entry_state='repeated-steady-loop'),
            models=[dict(id='r8', model=self.file('model.json'), engine=self.file('state8.py'))],
            numerical_checks=[dict(id='input0', baseline=self.file('before.bin'), candidate=self.file('after.bin'),
                                   reference=self.file('reference.bin'), elf_sha256=[arm['elf']['sha256']] * 2)])

    def save(self, name, value):
        (self.root / name).write_text(json.dumps(value))

    def file(self, name):
        return dict(path=name, sha256=digest(self.root / name))

    def run_pair(self):
        self.save('pair.json', self.manifest)
        return fragment.evaluate(self.root / 'pair.json')

    def assert_no_prediction(self, result):
        self.assertEqual(result['predictions'], [])
        self.assertTrue(result['retained'])
        self.assertFalse(result['automatic_performance_rejection'])
        self.assertFalse(result['automatic_full_test'])
        self.assertIsNone(result['prediction_interval'])

    def test_actual_elf_trace_and_tie_are_retained(self):
        result = self.run_pair()
        self.assertEqual(result['status'], 'exploratory-pair-estimate')
        self.assertEqual(result['primary_prediction']['candidate_over_baseline'], 1)
        self.assertEqual(result['recommendation']['action'], 'paired-native-test-before-expanded-tests')
        self.assertTrue(result['retained'])
        self.assertIsNone(result['prediction_confidence'])

    def test_numerical_failure_blocks_gain(self):
        (self.root / 'after.bin').write_bytes(b'wrong output')
        self.manifest['numerical_checks'][0]['candidate'] = self.file('after.bin')
        result = self.run_pair()
        self.assertEqual(result['status'], 'numerical-failed')
        self.assertEqual(result['recommendation']['action'], 'repair-numerical-contract')
        self.assert_no_prediction(result)

    def test_missing_numerical_evidence_blocks_gain(self):
        self.manifest['numerical_checks'] = []
        result = self.run_pair()
        self.assertEqual(result['recommendation']['action'], 'collect-numerical-evidence')
        self.assert_no_prediction(result)

    def test_stale_numerical_binary_identity_blocks_gain(self):
        self.manifest['numerical_checks'][0]['elf_sha256'][1] = '0' * 64
        self.assert_no_prediction(self.run_pair())

    def test_changed_elf_blocks_gain(self):
        (self.root / 'fixture.elf').write_bytes(b'changed')
        self.assert_no_prediction(self.run_pair())

    def test_trace_truncation_blocks_gain(self):
        path = self.root / 'trace.jsonl'
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        rows[-1]['truncated'] = True
        path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
        for key in ('baseline', 'candidate'):
            self.manifest[key]['trace'] = self.file('trace.jsonl')
        self.assert_no_prediction(self.run_pair())

    def test_wrong_engine_identity_blocks_gain(self):
        frozen = json.loads((self.root / 'model.json').read_text())
        frozen['engine_files']['state8.py'] = '0' * 64
        self.save('model.json', frozen)
        self.manifest['models'][0]['model'] = self.file('model.json')
        self.assert_no_prediction(self.run_pair())

    def test_unsupported_entry_state_blocks_gain(self):
        self.manifest['contract']['entry_state'] = 'arbitrary-caller'
        self.assert_no_prediction(self.run_pair())

    def test_reference_is_required(self):
        del self.manifest['numerical_checks'][0]['reference']
        self.assert_no_prediction(self.run_pair())

    def test_unknown_cost_is_not_zero(self):
        result = self.run_pair()
        self.assertEqual(len(result['cost']['unknown_stages']), 3)
        self.assertIsNone(result['cost']['total_seconds'])

    def test_runtime_does_not_change_comparison_identity(self):
        first = self.run_pair()
        self.manifest['cost_seconds'] = {'build': 0, 'trace_acquisition': 1.25, 'native_measurement': 0}
        second = self.run_pair()
        self.assertEqual(first['primary_prediction'], second['primary_prediction'])
        self.assertEqual(second['cost']['unknown_stages'], [])
        self.assertGreaterEqual(second['cost']['known_subtotal_seconds'], 1.25)
        self.assertIsNone(second['cost']['total_seconds'])
        third = self.run_pair()
        self.assertEqual(second['comparison_sha256'], third['comparison_sha256'])


if __name__ == '__main__':
    unittest.main()
