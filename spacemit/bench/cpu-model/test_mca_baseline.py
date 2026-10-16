"""核对完整指令约束、转写失败和证据损坏。"""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from common import seal

spec = importlib.util.spec_from_file_location('mca_baseline', Path(__file__).with_name('mca-baseline.py'))
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)


class BaselineTest(unittest.TestCase):
    def document(self):
        return dict(TargetInfo=dict(CPUName='spacemit-x60'), CodeRegions=[dict(
            Instructions=['add', 'addi', 'bne'], InstructionInfoView=dict(InstructionList=[{}, {}, {}]),
            SummaryView=dict(Iterations=128, Instructions=384, TotalCycles=257))])

    def test_complete_instruction_count(self):
        document = self.document()
        self.assertEqual(baseline.summary(document, 128, 3)['TotalCycles'], 257)
        document['CodeRegions'][0]['SummaryView']['Instructions'] -= 128
        with self.assertRaises(ValueError):
            baseline.summary(document, 128, 3)

    def test_wrong_target(self):
        document = self.document()
        document['TargetInfo']['CPUName'] = 'generic-rv64'
        with self.assertRaises(ValueError):
            baseline.summary(document, 128, 3)

    def test_missing_static_instruction(self):
        document = self.document()
        document['CodeRegions'][0]['Instructions'].pop()
        with self.assertRaises(ValueError):
            baseline.summary(document, 128, 3)

    def test_negative_load_offset_and_zero_register(self):
        word = 0x3003 | (5 << 7) | (11 << 15) | (4088 << 20)
        body = dict(counter=10, instructions=[dict(kind='load', encoding=f'{word:08x}', address_offset=-8),
            dict(kind='add', encoding='000002b3')])
        text = baseline.assembly(body)
        self.assertIn('ld x5,-8(x11)', text)
        self.assertIn('add x5,x0,x0', text)
        self.assertTrue(text.endswith('addi x10,x10,-1\nbnez x10,.Lloop\n'))

    def test_wrong_opcode_and_unsupported_instruction(self):
        body = dict(counter=10, instructions=[dict(kind='add', encoding='02000033')])
        with self.assertRaises(ValueError):
            baseline.assembly(body)
        body['instructions'][0]['kind'] = 'ime'
        with self.assertRaises(ValueError):
            baseline.assembly(body)

    def test_receipt_corruption_and_extra_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'input.s'
            path.write_text('add x5,x5,x5\n')
            seal(root)
            baseline.verify(root)
            (root / 'extra.s').write_text('mul x5,x5,x5\n')
            with self.assertRaises(ValueError):
                baseline.verify(root)
            (root / 'extra.s').unlink()
            path.write_text('mul x5,x5,x5\n')
            with self.assertRaises(ValueError):
                baseline.verify(root)


if __name__ == '__main__':
    unittest.main()
