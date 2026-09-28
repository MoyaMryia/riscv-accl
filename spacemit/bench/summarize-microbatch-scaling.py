#!/usr/bin/env python3
"""Fit how 32-token prefill chunk time grows with processed context.

Extracts the server's prompt-processing progress lines, converts them to
per-32-token chunk times, fits a least-squares line of chunk time against the
processed-context position, and reports bracket means with the linear share at
each bracket plus an extrapolated projection for a longer prompt. A rising
linear term is consistent with attention/history traffic scaling with context;
the fit alone does not attribute the cost to a specific operator.
"""

import argparse
import re
from pathlib import Path

PROGRESS = re.compile(
    r'task\s+(\d+) \| prompt processing, n_tokens =\s*(\d+), progress =\s*[0-9.]+,'
    r' t =\s*([0-9.]+) s')


def fit(points):
    """Least-squares fit of y = a + b*x over (x, y) points; returns a, b, r2."""
    n = len(points)
    mean_x = sum(x for x, _ in points) / n
    mean_y = sum(y for _, y in points) / n
    sxx = sum((x - mean_x) ** 2 for x, _ in points)
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in points)
    b = sxy / sxx
    a = mean_y - b * mean_x
    ss_res = sum((y - (a + b * x)) ** 2 for x, y in points)
    ss_tot = sum((y - mean_y) ** 2 for _, y in points)
    return a, b, 1 - ss_res / ss_tot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('logs', type=Path, nargs='+')
    parser.add_argument('--centers', type=int, nargs='+',
                        default=[256, 2048, 8192, 16384, 24576, 32768])
    parser.add_argument('--radius', type=int, default=256)
    parser.add_argument('--project-tokens', type=int, default=65536,
                        help='extrapolate total prefill seconds for this prompt length')
    args = parser.parse_args()

    for path in args.logs:
        tasks = {}
        for line in path.read_text(errors='replace').splitlines():
            match = PROGRESS.search(line)
            if match:
                tasks.setdefault(int(match[1]), []).append((int(match[2]), float(match[3])))
        for task, points in sorted(tasks.items()):
            chunks = [(n - 16, t - previous_t)
                      for (previous_n, previous_t), (n, t) in zip(points, points[1:])
                      if n - previous_n == 32]
            if len(chunks) < 10:
                raise SystemExit(f'{path} task {task}: too few 32-token chunks to fit')
            a, b, r2 = fit(chunks)
            print(f'| {path.name} | task {task} | {len(chunks)} | {a:.3f} | {b * 1000:.2f} | {r2:.4f} |')
            for center in args.centers:
                values = [elapsed for x, elapsed in chunks if abs(x - center) <= args.radius]
                if not values:
                    print(f'|   near {center:>6} | mean={float("nan"):.3f} s | linear share=- |')
                    continue
                mean_chunk = sum(values) / len(values)
                linear = b * center
                print(f'|   near {center:>6} | mean={mean_chunk:.3f} s '
                      f'| linear share={100 * linear / mean_chunk:.0f}% |')
            total_prompt = args.project_tokens
            n_chunks = total_prompt // 32
            projected = n_chunks * a + b * 32 * (n_chunks * (n_chunks + 1) / 2)
            print(f'|   projection | {total_prompt}-token cold prefill ~{projected:.0f} s '
                  f'(linear extrapolation of this fit, no warm/cache effects) |')


if __name__ == '__main__':
    main()
