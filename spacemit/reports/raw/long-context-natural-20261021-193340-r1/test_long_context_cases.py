"""检查完整原文、独立事实和构造数值。"""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import long_context_cases as cases


def character_count(messages):
    """用可复算的字符计数替身测试二分计算。"""
    return 11 + sum(len(message['content']) for message in messages)


class CasesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generated = cases.generate_cases(character_count)

    def test_matrix_counts_and_positions(self):
        self.assertEqual(len(self.generated), 6)
        for case in self.generated:
            with self.subTest(case=case['case_id']):
                text = case['messages'][1]['content']
                self.assertEqual(case['local_token_count'], 11 + len(case['messages'][0]['content']) + len(text))
                if case['level'] == 'short':
                    self.assertNotIn('Z000000', text)
                else:
                    target = 16384 if case['level'] == '16k' else 32768
                    self.assertLessEqual(abs(case['local_token_count'] - target), 64)
                    markers = ('资料甲', '资料乙', '资料丙') if case['task'] == 'lookup' else ('版本记录一', '版本记录二', '版本记录三')
                    positions = [text.index(marker) / len(text) for marker in markers]
                    self.assertEqual(positions[0], 0)
                    self.assertTrue(.45 < positions[1] < .55)
                    self.assertGreater(positions[2], .97)
                    filler = [line for line in text.splitlines() if line.startswith('巡检资料')]
                    self.assertEqual(len(filler), case['filler_lines'])
                    self.assertEqual(len(set(filler)), len(filler))
                    for line in filler:
                        for target_id in ('A17', 'B29', 'C43', 'P17'):
                            self.assertNotIn(target_id, line)

    def test_independent_facts_and_identical_questions(self):
        for task in ('lookup', 'revision'):
            selected = [case for case in self.generated if case['task'] == task]
            self.assertEqual(len({case['messages'][1]['content'].split('\n\n')[-1] for case in selected}), 1)
            for case in selected:
                text, reference = case['messages'][1]['content'], case['reference']
                if task == 'lookup':
                    for fact in ('A17 的设备数为 137 台', 'B29 的负责人为顾青禾', 'C43 的巡检周期为 19 天'):
                        self.assertIn(fact, text)
                    self.assertEqual(reference['设备数'], '137 台')
                    self.assertEqual(reference['负责人'], '顾青禾')
                    self.assertEqual(reference['巡检周期'], '19 天')
                else:
                    for fact in ('V3', '梁知远', '2027-03-11', 'V8', '沈若宁', '2027-05-23',
                                 'V12', '陶云舟', '2027-09-17'):
                        self.assertIn(fact, text)
                    self.assertEqual(reference['版本'], 'V12')
                    self.assertEqual(reference['负责人'], '陶云舟')
                    self.assertEqual(reference['确认期限'], '2027-09-17')
                self.assertEqual(reference, selected[0]['reference'])

    def test_schema_roundtrip(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'cases.json'
            path.write_text(json.dumps(self.generated, ensure_ascii=False))
            self.assertEqual(cases.read_cases(path), self.generated)

    def test_schema_errors(self):
        mutations = [lambda value: value.pop(),
                     lambda value: value.__setitem__(1, value[0]),
                     lambda value: value.__setitem__(0, None),
                     lambda value: value[0].update(task=[]),
                     lambda value: value[0].update(level='64k'),
                     lambda value: value[0].update(local_token_count=True),
                     lambda value: value[0].update(filler_lines=-1),
                     lambda value: value[0].update(filler_lines=1),
                     lambda value: value[1].update(local_token_count=16000),
                     lambda value: value[0].update(messages=[]),
                     lambda value: value[0]['reference'].update(负责人='错误'),
                     lambda value: value[0]['payload_settings'].update(max_tokens=512)]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'cases.json'
            for mutation in mutations:
                with self.subTest(mutation=mutations.index(mutation)):
                    value = copy.deepcopy(self.generated)
                    mutation(value)
                    path.write_text(json.dumps(value, ensure_ascii=False))
                    with self.assertRaises(ValueError):
                        cases.read_cases(path)
            for value in ({}, None, [0] * 6):
                path.write_text(json.dumps(value))
                with self.assertRaises(ValueError):
                    cases.read_cases(path)

    def test_count_boundaries(self):
        for count in (16320, 16448):
            cases.check_count(count, '16k')
        for count in (32704, 32832):
            cases.check_count(count, '32k')
        cases.check_count(12032, 'short')
        for count, level in ((16319, '16k'), (16449, '16k'), (32703, '32k'),
                             (32833, '32k'), (12033, 'short'), (0, 'short'), (True, 'short')):
            with self.subTest(count=count), self.assertRaises(ValueError):
                cases.check_count(count, level)

    def test_cli_uses_local_chat_template(self):
        tokenizer = mock.Mock()
        tokenizer.apply_chat_template.side_effect = lambda messages, **kwargs: list(range(character_count(messages)))
        auto = mock.Mock()
        auto.from_pretrained.return_value = tokenizer
        with tempfile.TemporaryDirectory() as folder, mock.patch.dict('sys.modules', {'transformers': mock.Mock(AutoTokenizer=auto)}):
            path = Path(folder) / 'cases.json'
            self.assertEqual(cases.main(['--tokenizer', '/本地/官方2B', '--output', str(path)]), 0)
            self.assertEqual(len(cases.read_cases(path)), 6)
            auto.from_pretrained.assert_called_once_with('/本地/官方2B', local_files_only=True)
            for call in tokenizer.apply_chat_template.call_args_list:
                self.assertEqual(call.kwargs, {'enable_thinking': False, 'add_generation_prompt': True, 'tokenize': True})
            with self.assertRaises(FileExistsError):
                cases.main(['--tokenizer', '/本地/官方2B', '--output', str(path)])


if __name__ == '__main__':
    unittest.main()
