#!/usr/bin/env python3
"""Summarize 32-token prompt batch times from llama-server progress logs."""

import argparse
import re
from collections import defaultdict
from pathlib import Path

PROGRESS = re.compile(
    r'task\s+(\d+) \| prompt processing, n_tokens =\s*(\d+), progress =\s*[0-9.]+,'
    r' t =\s*([0-9.]+) s')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('logs', type=Path, nargs='+')
    parser.add_argument('--centers', type=int, nargs='+', default=[256, 2048, 8192, 12288])
    parser.add_argument('--radius', type=int, default=256)
    args = parser.parse_args()
    print('| Log | Task | Latest prompt tokens | ' + ' | '.join(f'Near context {n}: s/32' for n in args.centers) + ' |')
    print('| --- | ---: | ---: | ' + ' | '.join('---:' for _ in args.centers) + ' |')
    for path in args.logs:
        tasks = defaultdict(list)
        for line in path.read_text(errors='replace').splitlines():
            match = PROGRESS.search(line)
            if match:
                tasks[int(match[1])].append((int(match[2]), float(match[3])))
        for task, points in tasks.items():
            chunks = [(n, time - previous_time)
                      for (previous_n, previous_time), (n, time) in zip(points, points[1:])
                      if n - previous_n == 32]
            if not chunks:
                continue
            rates = []
            for center in args.centers:
                values = [elapsed for n, elapsed in chunks if abs(n - center) <= args.radius]
                rates.append(f'{sum(values) / len(values):.2f}' if values else '-')
            print(f'| {path.name} | {task} | {points[-1][0]} | ' + ' | '.join(rates) + ' |')


if __name__ == '__main__':
    main()
