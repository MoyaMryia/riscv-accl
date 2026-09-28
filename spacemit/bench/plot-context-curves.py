#!/usr/bin/env python3
"""Render measured direct prefill/decode context curves as a standalone SVG."""

import argparse
import json
import math
from pathlib import Path
from xml.sax.saxutils import escape

COLORS = {'2B': '#2259a7', '4B': '#d76519'}
CONTEXT_TICKS = (128, 2048, 8192, 12288)


def read_points(path):
    points = {'2B': {}, '4B': {}}
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get('kind') != 'measurement' or row.get('concurrency') != 1:
            continue
        model = row.get('label', '').split('-')[0]
        context = row.get('context_tokens')
        if model not in points or context not in CONTEXT_TICKS or row.get('mode') != 'plain':
            continue
        result = row['results'][0]
        timing = result.get('timings', {})
        if result.get('stop_type') != 'limit' or timing.get('predicted_n') != 32:
            continue
        if context in points[model]:
            raise ValueError(f'duplicate {model} {context} point')
        points[model][context] = {
            'prefill': timing['prompt_per_second'],
            'decode': timing['predicted_per_second'],
        }
    return points


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('jsonl', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    points = read_points(args.jsonl)
    if not any(points.values()):
        parser.error('no completed direct 32-token context measurements found')

    width, height = 1200, 550
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
             f'viewBox="0 0 {width} {height}" role="img" '
             f'aria-label="Qwen3.5 2B and 4B prefill and decode throughput versus context length">',
             '<rect width="1200" height="550" fill="#ffffff"/>',
             '<text x="60" y="42" font-family="DejaVu Sans,Arial,sans-serif" font-size="22" '
             'font-weight="700" fill="#172133">Direct throughput versus prompt length</text>',
             '<text x="60" y="67" font-family="DejaVu Sans,Arial,sans-serif" font-size="13" '
             'fill="#4b5563">MUSE-Pi-Pro · Qwen3.5 Q4_0 · F16 KV · 32 generated tokens · synthetic fixed-token prompt</text>']
    for idx, (metric, title, unit, step) in enumerate((
        ('prefill', 'Prompt processing', 'tokens/s', 5),
        ('decode', 'Token generation', 'tokens/s', 1),
    )):
        left = 70 + idx * 570
        top, plot_w, plot_h = 120, 490, 320
        right, bottom = left + plot_w, top + plot_h
        values = [point[metric] for model in points.values() for point in model.values()]
        y_max = max(step, math.ceil(max(values) * 1.08 / step) * step)
        parts += [f'<text x="{left}" y="100" font-family="DejaVu Sans,Arial,sans-serif" '
                  f'font-size="17" font-weight="600" fill="#172133">{escape(title)} ({unit})</text>']
        for tick in range(0, int(y_max) + 1, step):
            y = bottom - plot_h * tick / y_max
            parts += [f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" '
                      'stroke="#e6ebf1" stroke-width="1"/>',
                      f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" '
                      f'font-family="DejaVu Sans,Arial,sans-serif" font-size="12" fill="#4b5563">{tick}</text>']
        for context in CONTEXT_TICKS:
            x = left + plot_w * context / CONTEXT_TICKS[-1]
            parts += [f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{bottom}" '
                      'stroke="#edf1f5" stroke-width="1"/>',
                      f'<text x="{x:.1f}" y="{bottom+22}" text-anchor="middle" '
                      'font-family="DejaVu Sans,Arial,sans-serif" font-size="12" '
                      f'fill="#4b5563">{context//1024}k</text>' if context >= 1024 else
                      f'<text x="{x:.1f}" y="{bottom+22}" text-anchor="middle" '
                      f'font-family="DejaVu Sans,Arial,sans-serif" font-size="12" fill="#4b5563">{context}</text>']
        parts += [f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#536174"/>',
                  f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#536174"/>',
                  f'<text x="{(left+right)/2:.1f}" y="{bottom+50}" text-anchor="middle" '
                  'font-family="DejaVu Sans,Arial,sans-serif" font-size="13" fill="#374151">Prompt tokens</text>']
        for model, color in COLORS.items():
            series = sorted(points[model].items())
            if not series:
                continue
            coords = [(left + plot_w * context / CONTEXT_TICKS[-1],
                       bottom - plot_h * point[metric] / y_max, context, point[metric])
                      for context, point in series]
            path = ' '.join(f'{"M" if i == 0 else "L"}{x:.1f},{y:.1f}' for i, (x, y, _, _) in enumerate(coords))
            parts += [f'<path d="{path}" fill="none" stroke="{color}" stroke-width="3" '
                      'stroke-linejoin="round" stroke-linecap="round"/>']
            for x, y, context, value in coords:
                parts += [f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{color}"/>',
                          f'<title>{model} {context} tokens: {value:.2f} {unit}</title>']
    parts += ['<line x1="75" y1="515" x2="103" y2="515" stroke="#2259a7" stroke-width="3"/>',
              '<text x="112" y="519" font-family="DejaVu Sans,Arial,sans-serif" font-size="13">2B</text>',
              '<line x1="165" y1="515" x2="193" y2="515" stroke="#d76519" stroke-width="3"/>',
              '<text x="202" y="519" font-family="DejaVu Sans,Arial,sans-serif" font-size="13">4B</text>',
              '<text x="1160" y="519" text-anchor="end" font-family="DejaVu Sans,Arial,sans-serif" '
              'font-size="12" fill="#4b5563">Lines connect measured points only; no extrapolation</text>',
              '</svg>']
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text('\n'.join(parts) + '\n')


if __name__ == '__main__':
    main()
