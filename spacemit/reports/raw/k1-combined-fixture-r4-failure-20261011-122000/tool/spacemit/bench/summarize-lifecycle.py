#!/usr/bin/env python3
"""Print a compact table from one or more bench-lifecycle JSONL files."""

import argparse
import json
import statistics
from pathlib import Path


def mean(values):
    values = [x for x in values if x is not None]
    return statistics.mean(values) if values else None


def fmt(value, precision=2):
    return '-' if value is None else f'{value:.{precision}f}'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', type=Path, nargs='+')
    args = parser.parse_args()
    print('| Label | Prompt | Concurrency | TTFT s | Prefill tok/s | Decode tok/s | End-to-end tok/s | RSS peak MiB | Decode RSS range MiB | Decode RSS drift MiB | Event gap p99 ms | Drift % |')
    print('| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |')
    for path in args.files:
        for line_number, line in enumerate(path.read_text().splitlines(), 1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f'{path}:{line_number}: invalid JSON') from exc
            if row.get('kind') != 'measurement':
                continue
            results = row['results']
            ttft = mean([r['ttft_ms'] for r in results])
            prefill = mean([r['timings'].get('prompt_per_second') for r in results])
            decode = mean([r['timings'].get('predicted_per_second') for r in results])
            p99 = mean([r['gap_ms'].get('p99') for r in results])
            drift = mean([100 * (r['second_half_tps'] / r['first_half_tps'] - 1)
                          for r in results if r.get('first_half_tps') and r.get('second_half_tps')])
            decode_rss = row.get('rss_decode_kib', {})
            rss_range = decode_rss['max'] - decode_rss['min'] if 'min' in decode_rss and 'max' in decode_rss else None
            drift_kib = row.get('rss_decode_delta_kib')
            peak = row['rss_kib'].get('max')
            prompt_label = '/'.join(str(x) for x in row['slot_contexts']) if row.get('slot_contexts') else row['context_tokens']
            print(f"| {row['label']} #{row['repeat']} | {prompt_label} | {row['concurrency']} | "
                  f"{fmt(ttft / 1000 if ttft is not None else None)} | {fmt(prefill)} | {fmt(decode)} | "
                  f"{fmt(row.get('aggregate_tps'))} | {fmt(peak / 1024 if peak else None)} | "
                  f"{fmt(rss_range / 1024 if rss_range is not None else None, 3)} | "
                  f"{fmt(drift_kib / 1024 if drift_kib is not None else None, 3)} | {fmt(p99)} | {fmt(drift, 1)} |")


if __name__ == '__main__':
    main()
