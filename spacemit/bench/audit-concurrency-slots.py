#!/usr/bin/env python3
"""Audit pinned 4B fixed-prompt direct/MTP ABBA output by physical slot."""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

LABEL = re.compile(r'^4B-(plain|mtp)-code-pinned-c(4|8)-pass([1-4])$')
EXPECTED = {1: 'plain', 2: 'mtp', 3: 'mtp', 4: 'plain'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results', type=Path)
    args = parser.parse_args()
    rows = {}
    config = None
    errors = []
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
            errors.append(f'line {number}: measurement without config')
            continue
        mode, concurrency_text, pass_text = match.groups()
        concurrency, arm = int(concurrency_text), int(pass_text)
        key = (concurrency, arm)
        if key in rows:
            errors.append(f'duplicate c{concurrency} pass{arm}')
        if (mode != EXPECTED[arm] or config.get('mode') != mode
                or config.get('concurrency') != concurrency or config.get('parallel') != 8
                or config.get('slot_assignment') != 'pinned'
                or config.get('slot_contexts') != [128] * concurrency
                or config.get('n_predict') != 128 or not config.get('ignore_eos')
                or not config.get('prompt_sha256')
                or '4B' not in Path(config.get('model', '')).name):
            errors.append(f'c{concurrency} pass{arm}: configuration mismatch')
        results = row.get('results', [])
        if len(results) != concurrency or row.get('repeat') != 0:
            errors.append(f'c{concurrency} pass{arm}: incomplete measurement')
        by_slot = {}
        for result in results:
            slot = result.get('slot')
            if slot in by_slot or slot not in range(concurrency):
                errors.append(f'c{concurrency} pass{arm}: bad slot {slot}')
            by_slot[slot] = result.get('tokens_sha256')
            if (result.get('server_slot') != slot or result.get('requested_slot') != slot
                    or result.get('stop_type') != 'limit' or result.get('error')
                    or result.get('tokens_predicted') != 128
                    or result.get('streamed_tokens') != 128
                    or not result.get('tokens_sha256')):
                errors.append(f'c{concurrency} pass{arm} slot{slot}: completion/slot mismatch')
        rows[key] = (by_slot, config.get('prompt_sha256'))
    for concurrency in (4, 8):
        expected = {(concurrency, arm) for arm in EXPECTED}
        missing = expected - rows.keys()
        for key in sorted(missing):
            errors.append(f'missing c{key[0]} pass{key[1]}')
        if missing:
            continue
        prompt_hashes = {rows[key][1] for key in expected}
        if len(prompt_hashes) != 1:
            errors.append(f'c{concurrency}: prompt differs between arms')
        for slot in range(concurrency):
            hashes = {rows[(concurrency, arm)][0].get(slot) for arm in EXPECTED}
            if len(hashes) != 1 or None in hashes:
                errors.append(f'c{concurrency} slot{slot}: direct/MTP token hashes differ')
        cross_slot = {rows[(concurrency, 1)][0].get(slot) for slot in range(concurrency)}
        print(f'c{concurrency}: {4 * concurrency} completions, {len(cross_slot)} cross-slot output variants')
    if errors:
        for error in errors:
            print('FAIL', error)
        return 1
    print('PASS: every pinned physical slot preserved its token IDs across plain/MTP ABBA')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
