#!/usr/bin/env python3
"""测量 2B 在四类任务中的完整回答。"""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
import signal
import statistics
import sys

import diagnostic as base

CATEGORIES = ('code', 'chinese', 'qa', 'long_document')
ARMS = ('direct', 'mtp', 'mtp_lowacc')
CASES_PER_CATEGORY = 3


def read_cases(path, quality):
    cases = json.loads(path.read_text())
    expected = {name: CASES_PER_CATEGORY for name in CATEGORIES}
    if not isinstance(cases, list) or any(not isinstance(c, dict) for c in cases):
        raise ValueError('cases must be a list of objects')
    if Counter(c.get('category') for c in cases) != expected:
        raise ValueError('case categories or counts differ')
    names = [c.get('case_id') for c in cases]
    if any(not isinstance(n, str) or re.fullmatch(r'[a-z]+(?:_[a-z]+)+', n) is None for n in names):
        raise ValueError('case identifiers are invalid')
    if len(set(names)) != len(names):
        raise ValueError('case identifiers are not unique')
    for case in cases:
        messages = case.get('messages')
        if not isinstance(messages, list) or len(messages) != 2:
            raise ValueError('each case must have two messages')
        if any(not isinstance(m, dict) for m in messages):
            raise ValueError('messages must be objects')
        if [m.get('role') for m in messages] != ['system', 'user'] or any(
                not isinstance(m.get('content'), str) or not m['content'].strip() for m in messages):
            raise ValueError('message roles or content are invalid')
        metadata = case.get('metadata')
        if not isinstance(metadata, dict) or not isinstance(metadata.get('evidence'), str) or not metadata['evidence']:
            raise ValueError('source evidence is absent')
        for key in ('required_facts', 'required_citations'):
            values = case.get(key)
            if not isinstance(values, list) or any(not isinstance(v, str) or not v for v in values):
                raise ValueError('invalid assessment data: ' + key)
        if not case['required_facts']:
            raise ValueError('required facts are absent')
        if case['category'] == 'code' and case.get('code_task') not in (
                quality.CODE_SPECS.keys() | quality.ADAPTIVE_CODE_SPECS.keys()):
            raise ValueError('unknown code task')
    return cases


def summarize(records):
    result = {'categories': {},
              'automatic_failures': sum(r['quality']['passed'] is False for r in records),
              'manual_reviews_pending': sum(r['quality']['passed'] is None for r in records)}
    for category in CATEGORIES:
        selected = [r for r in records if r['category'] == category]
        direct = {r['case_id']: r for r in selected if r['arm'] == 'direct'}
        if any(r['metrics']['prompt_tokens'] != direct[r['case_id']]['metrics']['prompt_tokens'] for r in selected):
            raise ValueError('paired input token counts differ: ' + category)
        arms = {}
        for arm in ARMS:
            rows = [r for r in selected if r['arm'] == arm]
            responses = [r['response'] for r in rows]
            drafted = sum(r['metrics']['draft_n'] for r in rows)
            accepted = sum(r['metrics']['draft_n_accepted'] for r in rows)
            arms[arm] = {
                'pairs': len(rows),
                'wall_mean_s': statistics.mean(r['wall_s'] for r in responses),
                'ttft_mean_s': statistics.mean(r['ttft_s'] for r in responses),
                'prefill_ms_mean': statistics.mean(r['timings']['prompt_ms'] for r in responses),
                'decode_ms_mean': statistics.mean(r['timings']['predicted_ms'] for r in responses),
                'completion_tokens': [r['metrics']['completion_tokens'] for r in rows],
                'draft_n': drafted, 'draft_accepted': accepted,
                'draft_acceptance': accepted / drafted if drafted else None,
                'fallback_events': sum(len(r['fallback_events']) for r in rows),
                'wall_change_vs_direct_pct': statistics.mean(
                    100 * (r['response']['wall_s'] / direct[r['case_id']]['response']['wall_s'] - 1)
                    for r in rows),
            }
        result['categories'][category] = arms
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('output', 'server', 'models', 'spert', 'tcm', 'manifest', 'request', 'build-receipt',
                 'chat', 'quality', 'effective', 'tool-receipt'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--port', type=int, default=18087)
    args = parser.parse_args(argv)
    if not os.environ.get('TMUX') or not 0 < args.port < 65536:
        parser.error('use tmux and a valid port')
    signal.signal(signal.SIGTERM, base.term_handler)
    args.output.mkdir(parents=True, exist_ok=False)
    assessment_path = Path(__file__).with_name('general_cases.py')
    models, identities = base.verify_inputs(args, model_names=('2B',), extra_tools={
        'suite': Path(__file__), 'assessment': assessment_path, 'cases': args.request})
    base.save(args.output / 'identity.json', identities)
    chat = base.load_module('general_chat', args.chat)
    quality = base.load_module('general_quality', args.quality)
    effective = base.load_module('general_effective', args.effective)
    assessments = base.load_module('general_assessment', assessment_path)
    cases = read_cases(args.request, quality)
    base.save(args.output / 'cases.json', cases)
    base.save(args.output / 'protocol.json', {
        'model': '2B', 'categories': list(CATEGORIES), 'arms': list(ARMS),
        'cases_per_category': CASES_PER_CATEGORY, 'config': base.CONFIG, 'context': base.CONTEXT,
        'max_tokens': base.MAX_TOKENS, 'request_deadline_s': base.DEADLINE_S,
        'log_verbosity': base.LOG_VERBOSITY, 'rs_snapshots': 0})
    libraries = f'{args.server.parent}:{args.tcm}:{args.spert / "lib"}'
    records = []
    for index, case in enumerate(cases):
        offset = index % len(ARMS)
        for arm in ARMS[offset:] + ARMS[:offset]:
            print('2B', case['category'], case['case_id'], arm, flush=True)
            record = base.run_one(args, libraries, chat, effective, quality, '2B', arm, 1, case,
                models['2B'], args.output / case['category'] / case['case_id'],
                assess=lambda answer: assessments.assess(case, answer, quality))
            record.update(case_id=case['case_id'], category=case['category'])
            records.append(record)
            base.save(args.output / 'progress.json', {'completed': len(records),
                'planned': len(cases) * len(ARMS), 'last': [case['case_id'], arm]})
    summary = summarize(records)
    summary['records'] = records
    base.save(args.output / 'summary.json', summary)
    return 2 if summary['automatic_failures'] else 0


if __name__ == '__main__':
    sys.exit(main())
