#!/usr/bin/env python3
"""List model sizes with complete 12k draft-window runs requiring same-binary controls."""

import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results', type=Path)
    args = parser.parse_args()
    found = {}
    if not args.results.exists():
        print(f'missing results: {args.results}', file=sys.stderr)
        return 1
    for line in args.results.read_text().splitlines():
        row = json.loads(line)
        if row.get('kind') != 'measurement':
            continue
        for size in ('2B', '4B'):
            if row.get('label') != f'{size}-window2k-12k':
                continue
            results = row.get('results', [])
            if (row.get('context_tokens') == 12288 and row.get('concurrency') == 1
                    and len(results) == 1 and results[0].get('stop_type') == 'limit'
                    and results[0].get('tokens_predicted') == 128
                    and results[0].get('streamed_tokens') == 128
                    and results[0].get('tokens_sha256') and not results[0].get('error')):
                found[size] = True
            else:
                print(f'SKIP {size}: incomplete windowed 12k run', file=sys.stderr)
    for size in ('2B', '4B'):
        if found.get(size):
            print(size)
        else:
            print(f'SKIP {size}: no complete windowed 12k run', file=sys.stderr)
    return 0 if found else 1


if __name__ == '__main__':
    raise SystemExit(main())
