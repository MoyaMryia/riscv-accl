#!/usr/bin/env python3
"""用相同共享权重比较完整草稿词表与前缀草稿词表。"""
import argparse
import json
import os
from pathlib import Path
import signal
import sys

import diagnostic as base
import general_suite as suite

VARIANTS = ('direct', 'prefix', 'full')
CASES_PER_CATEGORY = 1


def verification_counts(events):
    original = []
    replay = []
    pending = False
    for event in events:
        (replay if pending else original).append(event)
        pending = event['restore_checkpoint']
    proposed = sum(e['drafted'] for e in original)
    accepted = sum(e['accepted'] for e in original)
    return {'original_steps': len(original), 'original_proposed': proposed,
            'original_first_accepted': accepted,
            'original_first_acceptance': accepted / proposed if proposed else None,
            'original_restores': sum(e['restore_checkpoint'] for e in original),
            'replay_steps': len(replay), 'replay_accepted': sum(e['accepted'] for e in replay),
            'replay_restores': sum(e['restore_checkpoint'] for e in replay)}


def verify_trace(events, metrics):
    expected_replay = None
    for event in events:
        accepted, drafted = event['accepted'], event['drafted']
        if drafted < 1 or accepted > drafted:
            raise ValueError('verification event counts are invalid')
        if expected_replay is not None and drafted != expected_replay:
            raise ValueError('replay length differs from the restored queue')
        if event['restore_checkpoint']:
            if accepted == drafted:
                raise ValueError('restore event has no rejected tokens')
            expected_replay = accepted + 1
        else:
            if accepted != drafted:
                raise ValueError('full acceptance event has rejected tokens')
            expected_replay = None
    counts = verification_counts(events)
    if counts['original_proposed'] != metrics['draft_n']:
        raise ValueError('trace proposal total differs from server metrics')
    completed = sum(e['accepted'] for e in events if not e['restore_checkpoint'])
    if completed != metrics['draft_n_accepted']:
        raise ValueError('trace completion total differs from server metrics')
    return counts


def summarize(records):
    result = {'cases': {},
              'automatic_failures': sum(r['quality']['passed'] is False for r in records),
              'manual_reviews_pending': sum(r['quality']['passed'] is None for r in records)}
    for case_id in dict.fromkeys(r['case_id'] for r in records):
        selected = [r for r in records if r['case_id'] == case_id]
        direct = next(r for r in selected if r['variant'] == 'direct')
        if any(r['metrics']['prompt_tokens'] != direct['metrics']['prompt_tokens'] for r in selected):
            raise ValueError('paired input token counts differ: ' + case_id)
        values = {}
        for record in selected:
            response = record['response']
            values[record['variant']] = {
                'wall_s': response['wall_s'], 'ttft_s': response['ttft_s'],
                'prefill_ms': response['timings']['prompt_ms'],
                'decode_ms': response['timings']['predicted_ms'],
                'completion_tokens': record['metrics']['completion_tokens'],
                'wall_change_vs_direct_pct': 100 * (response['wall_s'] / direct['response']['wall_s'] - 1),
                'verification': record['verification'], 'quality': record['quality']}
        result['cases'][case_id] = {'category': direct['category'], 'variants': values}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('output', 'server', 'models', 'spert', 'tcm', 'manifest', 'request', 'build-receipt',
                 'chat', 'quality', 'effective', 'tool-receipt', 'full-model'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--port', type=int, default=18089)
    args = parser.parse_args(argv)
    if not os.environ.get('TMUX') or not 0 < args.port < 65536:
        parser.error('use tmux and a valid port')
    signal.signal(signal.SIGTERM, base.term_handler)
    args.output.mkdir(parents=True, exist_ok=False)
    here = Path(__file__).parent
    tools = {'ablation': Path(__file__), 'suite': here / 'general_suite.py',
             'model_check': here / 'model_head_check.py', 'probe': here / 'head_probe.py',
             'assessment': here / 'general_cases.py', 'cases': args.request}
    models, identities = base.verify_inputs(args, model_names=('2B',), extra_tools=tools)
    check = base.load_module('ablation_model_check', tools['model_check'])
    comparison = check.compare_models(args.full_model, models['2B'])
    identities['head_comparison'] = comparison
    base.save(args.output / 'identity.json', identities)
    chat = base.load_module('ablation_chat', args.chat)
    quality = base.load_module('ablation_quality', args.quality)
    effective = base.load_module('ablation_effective', args.effective)
    assessment = base.load_module('ablation_assessment', tools['assessment'])
    probe = base.load_module('ablation_probe', tools['probe'])
    cases = suite.read_cases(args.request, quality, cases_per_category=CASES_PER_CATEGORY)
    base.save(args.output / 'cases.json', cases)
    base.save(args.output / 'protocol.json', {'model': '2B', 'variants': list(VARIANTS),
        'cases_per_category': CASES_PER_CATEGORY, 'config': base.CONFIG, 'context': base.CONTEXT,
        'max_tokens': base.MAX_TOKENS, 'draft_max': base.DRAFT_MAX, 'log_verbosity': base.LOG_VERBOSITY,
        'trace': True, 'lowacc': False, 'rs_snapshots': 0,
        'prefix_rows': comparison['prefix_head']['shape'][1], 'full_rows': comparison['vocabulary_rows']})
    libraries = f'{args.server.parent}:{args.tcm}:{args.spert / "lib"}'
    records = []
    for index, case in enumerate(cases):
        offset = index % len(VARIANTS)
        for variant in VARIANTS[offset:] + VARIANTS[:offset]:
            arm = 'direct' if variant == 'direct' else 'mtp'
            model = args.full_model if variant == 'full' else models['2B']
            output = args.output / case['category'] / case['case_id'] / variant
            print('2B', case['case_id'], variant, flush=True)
            record = base.run_one(args, libraries, chat, effective, quality, '2B', arm, 1, case,
                model, output, assess=lambda answer: assessment.assess(case, answer, quality), trace=True)
            folder = output / '2B' / arm / 'round-1'
            events = probe.trace_events((folder / 'server.log').read_text())
            counts = verify_trace(events, record['metrics'])
            base.save(folder / 'trace.json', {'events': events})
            record.update(case_id=case['case_id'], category=case['category'], variant=variant,
                          verification=counts)
            records.append(record)
            base.save(args.output / 'progress.json', {'completed': len(records),
                'planned': len(cases) * len(VARIANTS), 'last': [case['case_id'], variant]})
    summary = summarize(records)
    summary['records'] = records
    base.save(args.output / 'summary.json', summary)
    return 2 if summary['automatic_failures'] else 0


if __name__ == '__main__':
    sys.exit(main())
