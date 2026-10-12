#!/usr/bin/env python3
"""Summarize resident and virtual process memory from lifecycle JSONL records."""

import argparse
import json
from pathlib import Path


def mib(kib):
    return '-' if kib is None else f'{kib / 1024:.1f}'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', type=Path, nargs='+')
    args = parser.parse_args()
    print('| Label | Model | K/V | Ctx allocation | Prompt | RSS loaded MiB | RSS peak MiB | RSS increase MiB | VmSize loaded MiB | VmSize after MiB | MemAvailable range MiB |')
    print('| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |')
    for path in args.files:
        config = None
        for line_number, line in enumerate(path.read_text().splitlines(), 1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f'{path}:{line_number}: invalid JSON') from exc
            if row.get('kind') == 'config':
                config = row
                continue
            if row.get('kind') != 'measurement':
                continue
            if config is None:
                raise ValueError(f'{path}:{line_number}: missing config')
            loaded = config.get('rss_loaded_kib')
            peak = row.get('rss_kib', {}).get('max')
            increase = peak - loaded if peak is not None and loaded is not None else None
            available = row.get('mem_available_kib', {})
            available_range = (available['max'] - available['min']
                               if 'max' in available and 'min' in available else None)
            model = '2B' if '2B' in Path(config['model']).name else '4B'
            cache = config.get('cache_type_k', 'f16') + '/' + config.get('cache_type_v', 'f16')
            print(f"| {row['label']} #{row['repeat']} | {model} | {cache} | "
                  f"{config['ctx_size']} | {row['context_tokens']} | {mib(loaded)} | "
                  f"{mib(peak)} | {mib(increase)} | {mib(config.get('vms_loaded_kib'))} | "
                  f"{mib(row.get('vms_after_kib'))} | {mib(available_range)} |")


if __name__ == '__main__':
    main()
