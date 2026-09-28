#!/usr/bin/env python3
"""Select model sizes whose 128/2048-token RVV32 wide-RVV FA arms are complete and exact."""

import argparse
import json
import re
import sys
from pathlib import Path

LABEL = re.compile(r'^(2B|4B)-rvv32-([01])-pass([1-4])$')
MODES = {1: '0', 2: '1', 3: '1', 4: '0'}
CONTEXTS = (128, 2048)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results', type=Path)
    args = parser.parse_args()
    records = {}
    config = None
    for number, line in enumerate(args.results.read_text().splitlines(), 1):
        row = json.loads(line)
        if row.get('kind') == 'config':
            config = row
            continue
        if row.get('kind') != 'measurement':
            continue
        match = LABEL.fullmatch(row.get('label', ''))
        if not match:
            continue
        if config is None:
            raise ValueError(f'{args.results}:{number}: measurement without config')
        size, enabled, pass_text = match.groups()
        pass_number = int(pass_text)
        context = row.get('context_tokens')
        key = (size, pass_number, context)
        if key in records:
            raise ValueError(f'{args.results}:{number}: duplicate {key}')
        errors = []
        if enabled != MODES[pass_number] or config.get('runtime_env', {}).get('SPINE_FA_WIDE_TILE') != enabled:
            errors.append('environment does not match label')
        if size not in Path(config['model']).name:
            errors.append('model does not match label')
        if context not in CONTEXTS or config.get('n_predict') != 32 or config.get('mode') != 'plain':
            errors.append('unexpected workload')
        results = row.get('results', [])
        if row.get('concurrency') != 1 or len(results) != 1:
            errors.append('expected one result')
        else:
            result = results[0]
            if result.get('error') or result.get('stop_type') != 'limit':
                errors.append('completion error or early stop')
            if result.get('tokens_predicted') != 32 or result.get('streamed_tokens') != 32:
                errors.append('incomplete generation')
            if not result.get('tokens_sha256'):
                errors.append('missing token IDs')
            if not result.get('ttft_ms') or not result.get('timings', {}).get('prompt_per_second'):
                errors.append('missing prefill timing')
        records[key] = (errors, results[0] if results else {})

    selected = []
    for size in ('2B', '4B'):
        missing = [(size, arm, context) for arm in MODES for context in CONTEXTS
                   if (size, arm, context) not in records]
        errors = [f'missing {key}' for key in missing]
        for arm in MODES:
            for context in CONTEXTS:
                record = records.get((size, arm, context))
                if record:
                    errors.extend(f'{size} pass{arm} context{context}: {error}' for error in record[0])
        if not errors:
            for context in CONTEXTS:
                hashes = {records[(size, arm, context)][1]['tokens_sha256'] for arm in MODES}
                if len(hashes) != 1:
                    errors.append(f'{size} context{context}: output token hashes differ')
        if not errors:
            for arm in (2, 3):
                log = args.results.parent / f'lifecycle-{size}-rvv32-1-pass{arm}.log'
                marker = 'SPINE_FA_WIDE_TILE: RVV tiled attention enabled for 256-dim heads'
                if not log.is_file() or marker not in log.read_text(errors='replace'):
                    errors.append(f'{size} pass{arm}: no proof the wide RVV kernel executed in {log}')
        if errors:
            for error in errors:
                print(f'SKIP {error}', file=sys.stderr)
            continue
        off = sum(records[(size, arm, 2048)][1]['ttft_ms'] for arm in (1, 4)) / 2
        on = sum(records[(size, arm, 2048)][1]['ttft_ms'] for arm in (2, 3)) / 2
        print(f'{size} 2k_TTFT_off_ms={off:.1f} on_ms={on:.1f} gain_pct={100 * (off - on) / off:.1f}', file=sys.stderr)
        print(size)
        selected.append(size)
    return 0 if selected else 1


if __name__ == '__main__':
    raise SystemExit(main())
