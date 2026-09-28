#!/usr/bin/env python3
"""Validate the complete 2B/4B four-arm rotated-slot KV scheduling campaign."""
import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

EXPECTED = {1: 'partition', 2: 'unified', 3: 'unified', 4: 'partition'}
BASE_CONTEXTS = [128, 512, 1024, 2048]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results', type=Path)
    parser.add_argument('--size', choices=('2B', '4B'), action='append',
                        help='audit only selected model size; default both')
    args = parser.parse_args()
    sizes = tuple(args.size or ('2B', '4B'))
    records = {}
    errors = []
    config = None
    for number, line in enumerate(args.results.read_text().splitlines(), 1):
        row = json.loads(line)
        if row.get('kind') == 'config':
            config = row
            continue
        if row.get('kind') != 'measurement':
            continue
        label = row.get('label', '')
        matches = [(size, variant, arm) for size in sizes
                   for arm, variant in EXPECTED.items()
                   if label == f'{size}-{variant}-rotate-{arm}']
        if not matches:
            continue
        size, variant, arm = matches[0]
        if config is None:
            errors.append(f'line {number}: measurement without config')
            continue
        repeat = row.get('repeat')
        key = (size, arm, repeat)
        if key in records:
            errors.append(f'duplicate {key}')
            continue
        expected_contexts = BASE_CONTEXTS[repeat:] + BASE_CONTEXTS[:repeat] if repeat in (0, 1) else []
        if (config.get('label') != label or size not in Path(config.get('model', '')).name
                or config.get('mode') != 'plain' or config.get('kv_unified') != (variant == 'unified')
                or config.get('slot_assignment') != 'pinned' or not config.get('rotate_slot_contexts')
                or config.get('slot_contexts') != BASE_CONTEXTS or config.get('repeats') != 2
                or config.get('parallel') != 4 or config.get('concurrency') != 4
                or config.get('n_predict') != 128 or config.get('ctx_size') != 16384
                or row.get('slot_contexts') != expected_contexts or row.get('concurrency') != 4):
            errors.append(f'{label} repeat={repeat}: configuration or rotation mismatch')
        results = row.get('results', [])
        if len(results) != 4:
            errors.append(f'{label} repeat={repeat}: expected four completions')
        by_length = {}
        for result in results:
            slot = result.get('slot')
            if slot not in range(4):
                errors.append(f'{label} repeat={repeat}: invalid slot {slot}')
                continue
            length = expected_contexts[slot] if expected_contexts else None
            if length in by_length:
                errors.append(f'{label} repeat={repeat}: duplicate prompt length {length}')
            by_length[length] = result.get('tokens_sha256')
            if (result.get('requested_slot') != slot or result.get('server_slot') != slot
                    or result.get('stop_type') != 'limit' or result.get('error')
                    or result.get('tokens_predicted') != 128 or result.get('streamed_tokens') != 128
                    or not result.get('tokens_sha256') or not result.get('ttft_ms')):
                errors.append(f'{label} repeat={repeat} slot={slot}: completion/slot mismatch')
        rate = row.get('aggregate_tps')
        if not isinstance(rate, (int, float)) or rate <= 0:
            errors.append(f'{label} repeat={repeat}: missing aggregate throughput')
        records[key] = (variant, rate, by_length)
    for size in sizes:
        expected = {(size, arm, repeat) for arm in EXPECTED for repeat in (0, 1)}
        for key in sorted(expected - records.keys()):
            errors.append(f'missing {key}')
        if not expected.issubset(records):
            continue
        hashes = defaultdict(set)
        rates = defaultdict(list)
        for key in sorted(expected):
            variant, rate, by_length = records[key]
            rates[variant].append(rate)
            for length in BASE_CONTEXTS:
                hashes[length].add(by_length.get(length))
        for length, variants in hashes.items():
            if len(variants) != 1 or None in variants:
                errors.append(f'{size} context={length}: output token hashes differ')
        partition = mean(rates['partition'])
        unified = mean(rates['unified'])
        print(f'{size}: partition={partition:.4f} unified={unified:.4f} tok/s; '
              f'unified_delta={100 * (unified / partition - 1):+.2f}%')
        print(f'{size}: {8 * 4} completions, {len(hashes)} prompt lengths, '
              f'one token hash per length={all(len(v) == 1 and None not in v for v in hashes.values())}')
    if errors:
        for error in errors:
            print('FAIL', error)
        return 1
    print('PASS: complete pinned ABBA campaign with exact outputs')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
