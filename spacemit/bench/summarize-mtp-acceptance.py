#!/usr/bin/env python3
"""Summarize server-side draft acceptance counters from MTP benchmark logs."""

import argparse
import re
from pathlib import Path

PATTERN = re.compile(
    r'draft acceptance =\s*[0-9.]+\s*\(\s*(\d+) accepted /\s*(\d+) generated\),'
    r' mean len =\s*([0-9.]+)')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('logs', type=Path, nargs='+')
    args = parser.parse_args()
    print('| Log | Requests | Accepted | Generated | Acceptance % | Mean draft length |')
    print('| --- | ---: | ---: | ---: | ---: | ---: |')
    for path in args.logs:
        matches = [tuple(map(float, match)) for match in PATTERN.findall(path.read_text(errors='replace'))]
        accepted = sum(int(row[0]) for row in matches)
        generated = sum(int(row[1]) for row in matches)
        mean_length = sum(row[2] for row in matches) / len(matches) if matches else None
        rate = f'{100 * accepted / generated:.2f}' if generated else '-'
        length = f'{mean_length:.2f}' if mean_length is not None else '-'
        print(f'| {path.name} | {len(matches)} | {accepted} | {generated} | {rate} | {length} |')


if __name__ == '__main__':
    main()
