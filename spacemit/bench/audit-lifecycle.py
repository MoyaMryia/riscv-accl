#!/usr/bin/env python3
"""Audit lifecycle JSONL completion, stability, and exact-output comparisons."""

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', type=Path, nargs='+')
    parser.add_argument('--label-regex', help='audit only measurements whose labels match this regular expression')
    parser.add_argument('--require-identical', action='store_true',
                        help='fail if grouped completions have different text or token hashes')
    parser.add_argument('--require-token-ids', action='store_true',
                        help='fail if any audited completion lacks returned token IDs')
    parser.add_argument('--min-runs-per-group', type=int, default=1,
                        help='require this many matching-prompt completions in every group')
    args = parser.parse_args()
    if args.min_runs_per_group < 1:
        parser.error('--min-runs-per-group must be positive')
    label_filter = re.compile(args.label_regex) if args.label_regex else None
    groups = defaultdict(list)
    failures = []
    warnings = []
    checked = 0
    for path in args.files:
        config = None
        for number, line in enumerate(path.read_text().splitlines(), 1):
            row = json.loads(line)
            if row.get('kind') == 'config':
                config = row
                continue
            if row.get('kind') != 'measurement':
                continue
            if config is None:
                failures.append(f'{path}:{number}: measurement has no preceding config')
                continue
            label = row['label']
            if label_filter and not label_filter.search(label):
                continue
            results = row['results']
            if len(results) != row['concurrency']:
                failures.append(f'{label}: expected {row["concurrency"]} results, got {len(results)}')
            for result in results:
                slot_contexts = row.get('slot_contexts')
                prompt_length = slot_contexts[result['slot']] if slot_contexts else row['context_tokens']
                key = (Path(config['model']).name, prompt_length, config['n_predict'],
                       config.get('ignore_eos', False), config.get('prompt_sha256', 'synthetic'))
                checked += 1
                name = f'{label} repeat={row["repeat"]} slot={result["slot"]}'
                if result.get('error'):
                    failures.append(f'{name}: server error {result["error"]}')
                if result.get('stop_type') != 'limit':
                    failures.append(f'{name}: stop_type={result.get("stop_type")}')
                if result.get('tokens_predicted') != config['n_predict']:
                    failures.append(f'{name}: predicted {result.get("tokens_predicted")}; require exactly {config["n_predict"]} tokens')
                if config.get('slot_assignment') == 'pinned':
                    if result.get('requested_slot') != result['slot'] or result.get('server_slot') != result['slot']:
                        failures.append(f'{name}: requested/server slot does not match the pinned request')
                elif config.get('rotate_slot_contexts'):
                    failures.append(f'{name}: rotated-slot result lacks verified slot pinning')
                if result.get('tokens_sha256') and result.get('streamed_tokens') != result.get('tokens_predicted'):
                    failures.append(f'{name}: streamed {result.get("streamed_tokens")} tokens but server reports {result.get("tokens_predicted")}')
                trace = result.get('event_trace')
                if config['n_predict'] >= 512 and not trace:
                    failures.append(f'{name}: missing long-generation event trace')
                if trace:
                    if len(trace) != result.get('stream_events'):
                        failures.append(f'{name}: trace length does not match stream events')
                    if sum(item[1] for item in trace) != result.get('streamed_tokens'):
                        failures.append(f'{name}: trace token count does not match streamed tokens')
                    if any(item[1] < 1 for item in trace) or any(b[0] < a[0] for a, b in zip(trace, trace[1:])):
                        failures.append(f'{name}: invalid trace token count or event ordering')
                if result.get('ttft_ms') is None or not result.get('timings', {}).get('predicted_per_second'):
                    failures.append(f'{name}: missing latency or decode timing')
                if result.get('tokens_sha256') is None:
                    message = f'{name}: token IDs unavailable; text hash only'
                    (failures if args.require_token_ids else warnings).append(message)
                groups[key].append((name, result.get('tokens_sha256'), result.get('sha256')))

    print(f'Checked {checked} streamed completions in {len(groups)} model/context/length groups.')
    if checked == 0:
        failures.append('no matching completions found')
    for key, values in groups.items():
        token_variants = defaultdict(list)
        text_variants = defaultdict(list)
        for name, token_hash, text_hash in values:
            if token_hash:
                token_variants[token_hash].append(name)
            text_variants[text_hash].append(name)
        print(f'{key[0]} context={key[1]} n={key[2]} ignore_eos={key[3]}: '
              f'prompt={key[4][:12]} {len(values)} runs, {len(token_variants)} token-hash variants, '
              f'{len(text_variants)} text-hash variants')
        if len(values) < args.min_runs_per_group:
            failures.append(f'{key[0]} context={key[1]} n={key[2]}: only {len(values)} runs; require {args.min_runs_per_group}')
        if args.require_identical and (len(token_variants) > 1 or len(text_variants) > 1):
            failures.append(f'{key[0]} context={key[1]} n={key[2]}: output hash variants differ')
        if len(token_variants) > 1:
            for digest, names in token_variants.items():
                print(f'  {digest[:16]}: {", ".join(names)}')
    if warnings:
        print(f'{len(warnings)} validation limits:')
        for item in warnings:
            print(f'  {item}')
    if failures:
        print(f'{len(failures)} completion issues:')
        for item in failures:
            print(f'  {item}')
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
