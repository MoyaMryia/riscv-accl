#!/usr/bin/env python3
"""Summarize long decode cadence and memory drift from lifecycle event traces."""

import argparse
import json
import statistics
from pathlib import Path


def window_rates(trace, tokens_per_window=128):
    if len(trace) < 2:
        return []
    rates = []
    base_time = trace[0][0]
    base_tokens = trace[0][1]
    total = base_tokens
    for time_ms, count in trace[1:]:
        total += count
        if total - base_tokens >= tokens_per_window:
            elapsed_ms = time_ms - base_time
            if elapsed_ms > 0:
                rates.append(1000 * (total - base_tokens) / elapsed_ms)
            base_time, base_tokens = time_ms, total
    tail_tokens = total - base_tokens
    tail_ms = trace[-1][0] - base_time
    if tail_tokens >= tokens_per_window // 2 and tail_ms > 0:
        rates.append(1000 * tail_tokens / tail_ms)
    return rates


def fmt(value, precision=2):
    return '-' if value is None else f'{value:.{precision}f}'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', type=Path, nargs='+')
    args = parser.parse_args()
    print('| Label | Prompt | Slot | Tokens | Decode tok/s | 128-token windows | Window min/median/max tok/s | Last/first % | Gap p99/max ms | Decode RSS range/drift MiB |')
    print('| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- | --- |')
    count = 0
    for path in args.files:
        for line_number, line in enumerate(path.read_text().splitlines(), 1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f'{path}:{line_number}: invalid JSON') from exc
            if row.get('kind') != 'measurement':
                continue
            for result in row['results']:
                if result.get('tokens_predicted', 0) < 512:
                    continue
                count += 1
                trace = result.get('event_trace', [])
                rates = window_rates(trace)
                rate_range = (f'{min(rates):.2f}/{statistics.median(rates):.2f}/{max(rates):.2f}'
                              if rates else '-')
                drift = 100 * (rates[-1] / rates[0] - 1) if len(rates) >= 2 else None
                gap = result.get('gap_ms', {})
                rss = row.get('rss_decode_kib', {})
                rss_range = ((rss['max'] - rss['min']) / 1024
                             if 'max' in rss and 'min' in rss else None)
                rss_drift = row.get('rss_decode_delta_kib')
                rss_drift = rss_drift / 1024 if rss_drift is not None else None
                print(f"| {row['label']} #{row['repeat']} | {row['context_tokens']} | "
                      f"{result['slot']} | {result['tokens_predicted']} | "
                      f"{fmt(result.get('timings', {}).get('predicted_per_second'))} | {len(rates)} | "
                      f"{rate_range} | {fmt(drift, 1)} | "
                      f"{fmt(gap.get('p99'))}/{fmt(gap.get('max'))} | "
                      f"{fmt(rss_range, 3)}/{fmt(rss_drift, 3)} |")
    if count == 0:
        raise SystemExit('no long completions found')


if __name__ == '__main__':
    main()
