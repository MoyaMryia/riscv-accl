#!/usr/bin/env python3
"""Regression checks for completion integrity, cache validity and judge blinding."""

import importlib.util
import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import document_quality_suite as suite


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


CHAT = suite.load_chat()
JUDGE = module('judge', Path(__file__).with_name('judge-shared-document-cache.py'))
RUNNER = module('runner', Path(__file__).with_name('run-all-document-quality.py'))


class QualityChecks(unittest.TestCase):
    def test_grouped_and_alternating_runs_keep_valid_pairs_and_new_cached_targets(self):
        cases = [{'case_id': f'case{i}', 'question': f'question{i}', 'source_id': f'S{i}',
                  'evidence': f'evidence{i}', 'required_facts': ['answer'],
                  'fact_patterns': ['answer'], 'position': 'middle'} for i in range(6)]
        for schedule, full_passes in [('grouped', 7), ('alternating', 12)]:
            with self.subTest(schedule=schedule), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                calls, seen, cached_document = [], set(), False
                previous_question = None

                def complete(url, payload, timeout, display):
                    nonlocal cached_document, previous_question
                    question = payload['messages'][1]['content'].split('Question: ')[1]
                    reuse = payload['cache_prompt'] and cached_document
                    if payload['cache_prompt'] and question != 'Reply with the word Ready.':
                        # The cached arm must never be an identical target repeat.
                        self.assertNotEqual(question, previous_question)
                        if schedule == 'grouped':
                            self.assertNotIn(question, seen)
                    seen.add(question)
                    previous_question = question
                    calls.append((question, payload['cache_prompt'], reuse))
                    cached_document = payload['cache_prompt']
                    answer = 'answer [S0]'
                    return {'server_slot': 0, 'ttft_s': 1 if reuse else 100,
                            'wall_s': 2 if reuse else 101, 'finish_reason': 'stop',
                            'reasoning_text': '', 'answer': answer,
                            'answer_sha256': hashlib.sha256(answer.encode()).hexdigest(),
                            'usage': {'prompt_tokens_details': {'cached_tokens': 1000 if reuse else 0}}}

                chat = SimpleNamespace(SYSTEM_INSTRUCTION=CHAT.SYSTEM_INSTRUCTION,
                                       messages=CHAT.messages, request_body=CHAT.request_body,
                                       count_prompt_tokens=lambda *args: 1050, complete=complete)
                args = SimpleNamespace(context=1000, n_predict=128, timeout=300,
                                       ctx_size=2048, port=18085, model_size='2B', case_id=None,
                                       quality_schedule=schedule, output=root/'results.jsonl',
                                       log=root/'server.log')
                for name in ('server', 'model', 'document', 'source_readme'):
                    path = root/name
                    path.write_text('public')
                    setattr(args, name, path)
                proc = SimpleNamespace(terminate=lambda: None, wait=lambda **kwargs: None)
                def popen(command, stdout, **kwargs):
                    stdout.write(b'SPINE_FA_WIDE_TILE: RVV tiled attention enabled for 256-dim heads\n')
                    stdout.flush()
                    return proc
                with patch.object(suite, 'load_chat', return_value=chat), \
                        patch.object(suite, 'evidence_cases', return_value=cases), \
                        patch.object(suite, 'make_document', return_value=('document', 1000)), \
                        patch.object(suite.subprocess, 'Popen', side_effect=popen), \
                        contextlib.redirect_stdout(io.StringIO()):
                    suite.run_chat_suite(args, SimpleNamespace(wait_healthy=lambda *args: None))
                records = list(map(json.loads, args.output.read_text().splitlines()))
                pairs = [r for r in records if r['kind'] == 'pair']
                self.assertEqual(len(pairs), 6)
                self.assertTrue(all(p['audit']['eligible_for_judging'] for p in pairs))
                self.assertEqual(sum(arm in ('primer', 'cold') for arm, _ in suite.request_plan(cases, schedule)),
                                 full_passes)
                self.assertLessEqual(sum(not reuse for _, _, reuse in calls), full_passes)
                if schedule == 'grouped':
                    self.assertEqual([cache for _, cache, _ in calls], [True] * 7 + [False] * 6)
                else:
                    self.assertEqual([p['order'] for p in pairs], [['warm', 'cold'], ['cold', 'warm']] * 3)



    def test_markdown_does_not_hide_required_facts(self):
        case = {'source_id': 'S3', 'fact_patterns': [r'not guaranteed', r'batch']}
        result = suite.fact_check(case, 'Identical logits are **not** guaranteed because batches differ. [S3]')
        self.assertEqual(result['required_fact_hits'], [True, True])
        self.assertTrue(result['expected_citation_present'])

    def response(self, events):
        return io.BytesIO(b''.join(b'data: ' + json.dumps(e).encode() + b'\n\n' for e in events)
                          + b'data: [DONE]\n\n')

    def test_usage_only_final_chunk_preserves_cache_and_physical_slot(self):
        events = [
            {'choices': [{'delta': {'content': 'Answer [S1]'}, 'finish_reason': None}]},
            {'choices': [{'delta': {}, 'finish_reason': 'stop'}], '__verbose': {'id_slot': 0}},
            {'choices': [], 'usage': {'prompt_tokens_details': {'cached_tokens': 8000}},
             'timings': {'prompt_n': 35}},
        ]
        with patch.object(CHAT.urllib.request, 'urlopen', return_value=self.response(events)):
            result = CHAT.complete('http://local', {}, 10, display=False)
        self.assertEqual(result['usage']['prompt_tokens_details']['cached_tokens'], 8000)
        self.assertEqual(result['server_slot'], 0)
        self.assertEqual(result['timings']['prompt_n'], 35)

    def test_broken_stream_is_rejected(self):
        with patch.object(CHAT.urllib.request, 'urlopen', return_value=self.response([
                {'choices': [{'delta': {'content': 'partial'}, 'finish_reason': None}]}])):
            with self.assertRaisesRegex(RuntimeError, 'finish reason'):
                CHAT.complete('http://local', {}, 10, display=False)

    def test_document_budget_retains_all_evidence_at_spread_positions(self):
        class FakeTokenizer:
            @staticmethod
            def post_json(url, payload, timeout):
                if url.endswith('/tokenize'):
                    return {'tokens': list(map(ord, payload['content']))}
                return {'content': ''.join(map(chr, payload['tokens']))}
        cases = [{'evidence': f'[S{i}] exact source passage {i}'} for i in range(6)]
        document, count = suite.make_document('http://local', FakeTokenizer, cases,
                                               'Public filler line.\n' * 200, 1200, 10)
        self.assertLessEqual(count, 1200)
        self.assertGreater(count, 1150)
        self.assertTrue(all(c['evidence'] in document for c in cases))
        self.assertLess(cases[0]['evidence_char_fraction'], .2)
        self.assertGreater(cases[2]['evidence_char_fraction'], .3)
        self.assertGreater(cases[4]['evidence_char_fraction'], .7)

    def test_length_and_reasoning_and_wrong_slot_are_not_judge_eligible(self):
        case = {'source_id': 'S1', 'fact_patterns': ['answer']}
        def result(cache):
            return {'answer': 'answer [S1]', 'finish_reason': 'stop', 'ttft_s': 1,
                    'server_slot': 0, 'answer_sha256': 'same', 'reasoning_text': '',
                    'usage': {'prompt_tokens_details': {'cached_tokens': cache}}}
        warm, cold = result(1000), result(0)
        self.assertTrue(suite.pair_audit(case, {'warm': warm, 'cold': cold}, 1050, 1000)['eligible_for_judging'])
        for field, bad in [('finish_reason', 'length'), ('reasoning_text', 'hidden reasoning'), ('server_slot', 1)]:
            with self.subTest(field=field):
                changed = dict(warm, **{field: bad})
                self.assertFalse(suite.pair_audit(case, {'warm': changed, 'cold': cold}, 1050, 1000)['eligible_for_judging'])
        cold['usage']['prompt_tokens_details']['cached_tokens'] = 10
        self.assertFalse(suite.pair_audit(case, {'warm': warm, 'cold': cold}, 1050, 1000)['cache_verified'])

    def test_both_answer_orders_are_mapped_back_to_the_correct_arm(self):
        case = {'case_id': 'test', 'question': 'q', 'evidence': 'e', 'cold_answer': 'cold', 'warm_answer': 'warm'}
        calls = []
        def fake(url, model, key, messages, *args):
            payload = json.loads(messages[1]['content']); calls.append(payload)
            mark = lambda text: {'score': 4 if text == 'warm' else 3,
                                 'reason': '', 'factual_errors': [], 'missing_points': []}
            return {'answer_a': mark(payload['answer_a']), 'answer_b': mark(payload['answer_b'])}, {}
        with patch.object(JUDGE, 'chat_completion', side_effect=fake):
            result = JUDGE.grade_case(case, 'https://example.invalid', 'judge', 'mock', 10, 0, 512, True)
        self.assertEqual([p['answer_a'] for p in calls], ['cold', 'warm'])
        self.assertEqual(result['cold_mean_score'], 3)
        self.assertEqual(result['warm_mean_score'], 4)

    def test_truncated_pair_cannot_pass_with_high_cloud_scores(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pair = {'kind': 'pair', 'case_id': 'test', 'cold_ttft_s': 100, 'warm_ttft_s': 1,
                    'audit': {'eligible_for_judging': False, 'complete_pair': False, 'cache_verified': True}}
            (root / '2B-2048.jsonl').write_text(json.dumps(pair) + '\n')
            result = RUNNER.summarize(root, ['2B-2048'], {})
            self.assertEqual(result['configurations'][0]['status'], 'REVIEW REQUIRED')
            self.assertEqual(result['configurations'][0]['judged'], 0)

    def test_missing_requested_pair_cannot_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'manifest.json').write_text(json.dumps({'case_ids': ['first', 'missing']}))
            pair = {'kind': 'pair', 'case_id': 'first', 'cold_ttft_s': 100, 'warm_ttft_s': 1,
                    'audit': {'eligible_for_judging': True, 'complete_pair': True, 'cache_verified': True,
                              'warm_facts': {'required_fact_hits': [True], 'expected_citation_present': True},
                              'cold_facts': {'required_fact_hits': [True], 'expected_citation_present': True}}}
            mark = {'case_id': 'first', 'cold_mean_score': 5, 'warm_mean_score': 5,
                    'passes': [{'cold': {'score': 5}, 'warm': {'score': 5}}] * 2}
            (root / '2B-2048.jsonl').write_text(json.dumps(pair) + '\n')
            (root / '2B-2048.judge.jsonl').write_text(json.dumps(mark) + '\n')
            result = RUNNER.summarize(root, ['2B-2048'], {})
            self.assertEqual(result['configurations'][0]['status'], 'REVIEW REQUIRED')


if __name__ == '__main__':
    unittest.main()
