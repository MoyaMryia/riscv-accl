#!/usr/bin/env python3
"""测量前缀词表覆盖，并记录检查点恢复路径。"""
import argparse
import json
import os
from pathlib import Path
import re
import signal
import sys
import urllib.request

import diagnostic as base


def prefix_coverage(tokens, rows):
    if not isinstance(tokens, list) or not tokens or any(type(t) is not int or t < 0 for t in tokens):
        raise ValueError('tokenizer returned invalid token identifiers')
    included = sum(t < rows for t in tokens)
    return {'retokenized_tokens': len(tokens), 'prefix_tokens': included,
            'prefix_fraction': included / len(tokens), 'token_ids': tokens}


def coverage_sources(records):
    return [r for r in records if r['model'] == '2B' and r['arm'] == 'direct']


def trace_events(text):
    events = []
    for line in text.splitlines():
        found = re.search(r'accepted\s+(\d+)/\s*(\d+) draft tokens( \(restore checkpoint\))?', line)
        if found:
            events.append({'accepted': int(found[1]), 'drafted': int(found[2]),
                           'restore_checkpoint': bool(found[3]), 'log_line': line})
    return events


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('output', 'server', 'models', 'spert', 'tcm', 'manifest', 'request', 'build-receipt',
                 'chat', 'quality', 'effective', 'tool-receipt', 'records'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--prefix-rows', type=int, required=True)
    parser.add_argument('--case-id', required=True)
    parser.add_argument('--port', type=int, default=18088)
    args = parser.parse_args(argv)
    if not os.environ.get('TMUX') or not 0 < args.port < 65536 or args.prefix_rows <= 0:
        parser.error('use tmux, a valid port and a positive prefix row count')
    signal.signal(signal.SIGTERM, base.term_handler)
    args.output.mkdir(parents=True, exist_ok=False)
    models, identity = base.verify_inputs(args, model_names=('2B',), extra_tools={
        'probe': Path(__file__), 'records': args.records, 'cases': args.request})
    base.save(args.output / 'identity.json', identity)
    chat = base.load_module('probe_chat', args.chat)
    effective = base.load_module('probe_effective', args.effective)
    cases = json.loads(args.request.read_text())
    selected = [c for c in cases if c['case_id'] == args.case_id]
    if len(selected) != 1:
        raise ValueError('probe case is absent or duplicated')
    records = json.loads(args.records.read_text())['records']
    sources = coverage_sources(records)
    url = f'http://127.0.0.1:{args.port}'

    def assess(_answer):
        coverage = []
        for record in sources:
            data = json.dumps({'content': record['response']['answer'],
                               'add_special': False, 'parse_special': False}).encode()
            request = urllib.request.Request(url + '/tokenize', data=data,
                                              headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(request, timeout=30) as response:
                tokens = json.load(response)['tokens']
            coverage.append({'case_id': record['case_id'], 'category': record['category'],
                'generated_tokens': record['metrics']['completion_tokens'],
                **prefix_coverage(tokens, args.prefix_rows)})
        base.save(args.output / 'coverage.json', {'prefix_rows': args.prefix_rows, 'records': coverage})
        return {'passed': None, 'result': {'coverage_records': len(coverage)}}

    libraries = f'{args.server.parent}:{args.tcm}:{args.spert / "lib"}'
    record = base.run_one(args, libraries, chat, effective, None, '2B', 'mtp_lowacc', 1,
                         selected[0], models['2B'], args.output, assess=assess, trace=True)
    log = (args.output / '2B/mtp_lowacc/round-1/server.log').read_text()
    events = trace_events(log)
    if not events:
        raise ValueError('verification trace is absent')
    base.save(args.output / 'trace.json', {'case_id': args.case_id, 'events': events,
        'timing_draft_n': record['metrics']['draft_n'],
        'timing_draft_accepted': record['metrics']['draft_n_accepted'],
        'fallback_events': record['fallback_events']})
    print('PROBE_COMPLETE', args.case_id, 'trace_events', len(events), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
