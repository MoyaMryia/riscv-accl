import importlib.util
from collections import Counter
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cases_module = load_module('general_cases_under_test', HERE / 'general_cases.py')
quality = load_module('quality_for_general_cases_tests', HERE.parents[1] / 'release-candidate/tests/quality.py')


class GeneralCasesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = cases_module.build_cases(quality)
        cls.by_id = {case['case_id']: case for case in cls.cases}

    def test_case_count_categories_ids_and_message_shape(self):
        self.assertEqual(len(self.cases), 12)
        self.assertEqual(Counter(case['category'] for case in self.cases), {
            'code': 3, 'chinese': 3, 'qa': 3, 'long_document': 3,
        })
        ids = [case['case_id'] for case in self.cases]
        self.assertEqual(len(ids), len(set(ids)))
        for case_id in ids:
            self.assertRegex(case_id, r'^[a-z]+(?:_[a-z]+)+$')
        for case in self.cases:
            self.assertEqual([message['role'] for message in case['messages']], ['system', 'user'])
            self.assertIn('evidence', case['metadata'])
            self.assertIn('required_facts', case['metadata'])
            self.assertIn('required_citations', case['metadata'])
            self.assertEqual(case['metadata']['required_facts'], case['required_facts'])

    def test_code_tasks_use_existing_specs_and_checks(self):
        self.assertTrue(self.by_id['code_unicode_runs']['messages'][1]['content'].startswith(quality.CODE_SPECS['unicode_runs']))
        self.assertTrue(self.by_id['code_free_windows']['messages'][1]['content'].startswith(quality.CODE_SPECS['free_windows']))
        self.assertTrue(self.by_id['code_unicode_offsets']['messages'][1]['content'].startswith(quality.ADAPTIVE_CODE_SPECS['unicode_offsets']))
        for case_id, spec in (
            ('code_unicode_runs', quality.CODE_SPECS['unicode_runs']),
            ('code_free_windows', quality.CODE_SPECS['free_windows']),
            ('code_unicode_offsets', quality.ADAPTIVE_CODE_SPECS['unicode_offsets']),
        ):
            self.assertEqual(self.by_id[case_id]['metadata']['evidence'], spec)
            self.assertIn('Python 源码', self.by_id[case_id]['messages'][0]['content'])
            self.assertIn('不得使用 imports', self.by_id[case_id]['messages'][0]['content'])
        self.assertIn('自然中文', self.by_id['qa_service_cost']['messages'][0]['content'])
        self.assertEqual({case['code_task'] for case in self.cases if case['category'] == 'code'},
                         {'unicode_runs', 'free_windows', 'unicode_offsets'})

    def test_long_document_has_length_and_distributed_evidence(self):
        document = cases_module.LONG_DOCUMENT
        self.assertGreaterEqual(len(document), 6000)
        self.assertLessEqual(len(document), 9000)
        self.assertGreater(document.index('【L04'), len(document) * 2 // 3)
        self.assertGreater(document.index('【L15'), len(document) * 2 // 3)
        self.assertGreater(document.index('【L17'), document.index('【L32'))
        self.assertGreater(document.index('【L11'), document.index('【L43'))
        self.assertGreater(document.index('【L21'), document.index('【L51'))
        key_positions = [document.index('【' + item) for item in ('L02', 'L32', 'L59')]
        self.assertLess(key_positions[0], len(document) // 3)
        self.assertGreater(key_positions[1], len(document) // 3)
        self.assertLess(key_positions[1], len(document) * 2 // 3)
        self.assertGreater(key_positions[2], len(document) * 2 // 3)
        for case in self.cases:
            if case['category'] in ('chinese', 'qa'):
                prompt = case['messages'][1]['content']
                evidence = case['metadata']['evidence']
                self.assertIn('【L', prompt)
                self.assertIn(evidence, prompt)
                self.assertNotRegex(evidence, r'^L[0-9]{2}(?:、L[0-9]{2})*$')
        fact_sources = {
            'chinese_customer_note': ('640 次', '608 次', '20 次'),
            'qa_inventory_arithmetic': ('80 件', '24 件', '31 件', '70 件', '111 台'),
            'qa_service_cost': ('16 张', '180 元', '5 张', '60 元'),
            'qa_rule_decision': ('10 分钟', '15 分钟', '4 小时'),
        }
        for case_id, facts in fact_sources.items():
            prompt = self.by_id[case_id]['messages'][1]['content']
            for fact in facts:
                with self.subTest(case=case_id, fact=fact):
                    self.assertIn(fact, prompt)
        for case in self.cases:
            if case['category'] == 'long_document':
                prompt = case['messages'][1]['content']
                self.assertIn(document, prompt)
                for citation in case['required_citations']:
                    self.assertIn('【' + citation, document)
                    self.assertIn(cases_module.SOURCE_SECTIONS[citation], case['metadata']['evidence'])

    def test_inventory_batches_and_report_time_rules_are_consistent(self):
        l05 = cases_module.SOURCE_SECTIONS['L05']
        l09 = cases_module.SOURCE_SECTIONS['L09']
        l10 = cases_module.SOURCE_SECTIONS['L10']
        l39 = cases_module.SOURCE_SECTIONS['L39']
        self.assertIn('以设备端签收时间为准', l05)
        self.assertIn('报表采用设备端签收时间', l39)
        self.assertIn('40 件', l10)
        self.assertIn('30 件', l10)
        self.assertIn('合计 70 件', l10)
        self.assertEqual(80 + 24 - 31 - 3, 70)
        self.assertIn('70 件', ' '.join(self.by_id['qa_inventory_arithmetic']['required_facts']))
        self.assertIn('111 台', ' '.join(self.by_id['qa_inventory_arithmetic']['required_facts']))
        self.assertIn('70 件', l09)
        self.assertIn('1 个事件', ' '.join(self.by_id['qa_rule_decision']['required_facts']))
        self.assertIn('95%', ' '.join(self.by_id['chinese_customer_note']['required_facts']))
        self.assertIn('3180 元', ' '.join(self.by_id['qa_service_cost']['required_facts']))

    def test_required_numeric_answers_are_explicit(self):
        numeric_facts = {
            'chinese_customer_note': ['608/640', '95%'],
            'chinese_handover_note': ['21 张'],
            'qa_inventory_arithmetic': ['111 台', '94 台', '12 台', '5 台', '80+24-31-3=70 件'],
            'qa_service_cost': ['16×180+5×60=3180 元', '21 张'],
            'qa_rule_decision': ['1 个事件', '15 分钟', '4 小时'],
            'long_device_reconciliation': ['92+3-2+1=94', '12 台', '5 台', '111 台'],
            'long_weekly_metrics': ['608/640=95%', '30/42', '3180 元'],
        }
        for case_id, values in numeric_facts.items():
            joined = ' '.join(self.by_id[case_id]['required_facts'])
            for value in values:
                with self.subTest(case=case_id, value=value):
                    self.assertIn(value, joined)

    def test_non_code_assessment_waits_for_blind_review(self):
        case = self.by_id['qa_service_cost']
        result = cases_module.assess(case, '服务费为 3180 元 [L11]，工单 21 张 [L08]。', quality)
        self.assertIsNone(result['passed'])
        self.assertEqual(result['result']['required_facts'], case['required_facts'])
        self.assertEqual(result['result']['required_citations'], case['required_citations'])
        self.assertEqual(result['result']['observed_citations'], ['L08', 'L11'])

    def test_code_assessment_runs_independent_correct_and_wrong_source(self):
        correct = {
            'unicode_runs': '''def encode_runs(text):
    runs = []
    for char in text:
        if runs and runs[-1][0] == char:
            runs[-1] = (char, runs[-1][1] + 1)
        else:
            runs.append((char, 1))
    return runs

def decode_runs(runs):
    result = ''
    for item in runs:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise ValueError()
        char, count = item
        if not isinstance(char, str) or len(char) != 1 or type(count) is not int or count <= 0:
            raise ValueError()
        result += char * count
    return result''',
            'free_windows': '''def merge_intervals(busy):
    values = []
    for start, end in busy:
        if end < start:
            raise ValueError()
        if end > start:
            values.append((start, end))
    values.sort()
    merged = []
    for start, end in values:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged

def free_windows(busy, start, end):
    if end < start:
        raise ValueError()
    if end == start:
        return []
    clipped = [(max(a, start), min(b, end)) for a, b in merge_intervals(busy) if b > start and a < end]
    result = []
    cursor = start
    for a, b in clipped:
        if cursor < a:
            result.append((cursor, a))
        cursor = max(cursor, b)
    if cursor < end:
        result.append((cursor, end))
    return result''',
            'unicode_offsets': '''def run_spans(text):
    spans = []
    for index, char in enumerate(text):
        if spans and spans[-1][0] == char:
            spans[-1] = (char, spans[-1][1], index + 1)
        else:
            spans.append((char, index, index + 1))
    return spans

def expand_spans(spans):
    if not spans:
        return ''
    output = ''
    expected = 0
    for item in spans:
        if not isinstance(item, (list, tuple)) or len(item) != 3:
            raise ValueError()
        char, start, end = item
        if not isinstance(char, str) or len(char) != 1 or type(start) is not int or type(end) is not int:
            raise ValueError()
        if start != expected or end <= start:
            raise ValueError()
        output += char * (end - start)
        expected = end
    return output''',
        }
        wrong = {
            'unicode_runs': 'def encode_runs(text):\n    return [(char, 1) for char in text]\ndef decode_runs(runs):\n    return "".join(char for char, count in runs)',
            'free_windows': 'def merge_intervals(busy):\n    return list(busy)\ndef free_windows(busy, start, end):\n    return []',
            'unicode_offsets': 'def run_spans(text):\n    return []\ndef expand_spans(spans):\n    return ""',
        }
        for task in correct:
            with self.subTest(task=task):
                case = self.by_id['code_' + task]
                good = cases_module.assess(case, correct[task], quality)
                bad = cases_module.assess(case, wrong[task], quality)
                self.assertIs(good['passed'], True)
                self.assertIs(bad['passed'], False)
                self.assertTrue(good['result']['checks'] > 0)


if __name__ == '__main__':
    unittest.main()
