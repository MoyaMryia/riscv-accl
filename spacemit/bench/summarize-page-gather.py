#!/usr/bin/env python3
"""Summarize occupied-page gather telemetry from a verbose server log."""

import argparse
import re
import statistics
from pathlib import Path

PATTERN = re.compile(r'SPINE_KV_PAGE_GATHER: physical_span=(\d+) gathered_span=(\d+) occupied_page_rows=(\d+)')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    args = parser.parse_args()
    spans = [tuple(map(int, match.groups())) for line in args.log.open(errors='replace')
             if (match := PATTERN.search(line))]
    if not spans:
        raise SystemExit('no span records; increase server log verbosity or check kernel activation')
    physical = [row[0] for row in spans]
    gathered = [row[1] for row in spans]
    compacted = [(p, g) for p, g in zip(physical, gathered) if g < p]
    print(f'records={len(spans)} compacted={len(compacted)} ({100 * len(compacted) / len(spans):.1f}%)')
    print(f'physical_span min/median/max={min(physical)}/{statistics.median(physical):g}/{max(physical)}')
    print(f'gathered_span min/median/max={min(gathered)}/{statistics.median(gathered):g}/{max(gathered)}')
    if compacted:
        saved = [p - g for p, g in compacted]
        ratio = [g / p for p, g in compacted if p]
        print(f'compacted_saved_rows min/median/max={min(saved)}/{statistics.median(saved):g}/{max(saved)}')
        print(f'compacted_span_ratio min/median/max={min(ratio):.3f}/{statistics.median(ratio):.3f}/{max(ratio):.3f}')


if __name__ == '__main__':
    main()
