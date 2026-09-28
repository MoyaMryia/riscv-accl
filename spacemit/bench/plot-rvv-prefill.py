#!/usr/bin/env python3
"""Plot measured RVV-wide on/off TTFT versus prompt length as standalone SVG."""
import argparse
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean
from xml.sax.saxutils import escape

PATTERNS = ((re.compile(r'^(2B|4B)-rvv32-([01])-pass[1-4]$'), None),
            (re.compile(r'^8k-(2B|4B)-rvv32-([01])-pass[1-4]$'), 8192),
            (re.compile(r'^(2B|4B)-rvv32-integrated-12k-([01])$'), 12288))
COLORS = {'2B': '#2563eb', '4B': '#ea580c'}
CORE_CONTEXTS = (128, 2048, 8192)
CONTEXTS = CORE_CONTEXTS + (12288,)


def read(path, pattern, expected_context, groups):
    for row in map(json.loads, path.open()):
        if row.get('kind') != 'measurement':
            continue
        match = pattern.fullmatch(row.get('label', ''))
        if not match:
            continue
        model, enabled = match.groups()
        context = row.get('context_tokens')
        if (expected_context is not None and context != expected_context) or context not in CONTEXTS:
            raise ValueError(f'unexpected context in {row["label"]}')
        result = row['results'][0]
        if result.get('stop_type') != 'limit' or result.get('tokens_predicted') != 32:
            raise ValueError(f'incomplete {row["label"]}')
        groups[(model, enabled, context)].append(result['ttft_ms'] / 1000)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('short', type=Path)
    parser.add_argument('long', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--integrated', type=Path, help='optional same-integrated-binary 12k JSONL')
    args = parser.parse_args()
    groups = defaultdict(list)
    read(args.short, *PATTERNS[0], groups)
    read(args.long, *PATTERNS[1], groups)
    if args.integrated:
        read(args.integrated, *PATTERNS[2], groups)
    complete_12k = {}
    for model in ('2B', '4B'):
        for enabled in ('0', '1'):
            for context in CORE_CONTEXTS:
                key = (model, enabled, context)
                if len(groups[key]) != 2:
                    raise ValueError(f'expected two ABBA arms for {key}, got {len(groups[key])}')
            if len(groups[(model, enabled, 12288)]) > 1:
                raise ValueError(f'expected at most one integrated 12k arm for {model} RVV={enabled}')
        complete_12k[model] = all(len(groups[(model, enabled, 12288)]) == 1 for enabled in ('0', '1'))
    width, height = 1130, 535
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Client time to first token with RVV attention off and on for 2B and 4B models">',
             '<rect width="1130" height="535" fill="#fff"/>',
             '<text x="55" y="42" font-family="DejaVu Sans,Arial,sans-serif" font-size="22" font-weight="700" fill="#172133">256-bit RVV attention lowers cold first-token latency</text>',
             '<text x="55" y="65" font-family="DejaVu Sans,Arial,sans-serif" font-size="13" fill="#526071">MUSE-Pi-Pro · F16 KV · 32 generated tokens · 128–8k: two ABBA arms; 12k: one integrated pair</text>']
    for panel, model in enumerate(('2B', '4B')):
        left = 75 + panel * 545
        top, bottom = 130, 420
        x = {context: left + 55 + i * 120 for i, context in enumerate(CONTEXTS)}
        ymin, ymax = (3, 3000) if model == '2B' else (8, 10000)
        def y(value):
            return bottom - (math.log10(value) - math.log10(ymin)) / (math.log10(ymax) - math.log10(ymin)) * (bottom - top)
        parts.append(f'<text x="{left}" y="103" font-family="DejaVu Sans,Arial,sans-serif" font-size="18" font-weight="700" fill="{COLORS[model]}">{model}</text>')
        for tick in ((10, 100, 1000) if model == '2B' else (10, 100, 1000)):
            yy=y(tick)
            parts += [f'<line x1="{left}" y1="{yy:.1f}" x2="{left+480}" y2="{yy:.1f}" stroke="#e7ebf0"/>',
                      f'<text x="{left-10}" y="{yy+4:.1f}" text-anchor="end" font-family="DejaVu Sans,Arial,sans-serif" font-size="12" fill="#526071">{tick}</text>']
        parts += [f'<line x1="{left}" y1="{bottom}" x2="{left+480}" y2="{bottom}" stroke="#64748b"/>',
                  f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#64748b"/>']
        for context in CONTEXTS:
            parts.append(f'<text x="{x[context]}" y="{bottom+24}" text-anchor="middle" font-family="DejaVu Sans,Arial,sans-serif" font-size="12" fill="#3e4b5c">{context if context==128 else str(context//1024)+"k"}</text>')
        for enabled, color, dash in (('0', '#94a3b8', '6 4'), ('1', COLORS[model], 'none')):
            vals=[(context,mean(groups[(model,enabled,context)])) for context in CONTEXTS
                  if groups[(model,enabled,context)] and (context != 12288 or complete_12k[model])]
            path=' '.join(f'{"M" if i==0 else "L"}{x[context]},{y(value):.1f}' for i,(context,value) in enumerate(vals))
            parts.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="3" stroke-dasharray="{dash}"/>')
            for context,value in vals:
                xx,yy=x[context],y(value)
                marker = (f'<rect x="{xx-5}" y="{yy-5:.1f}" width="10" height="10" fill="{color}"/>'
                          if context == 12288 else
                          f'<circle cx="{xx}" cy="{yy:.1f}" r="5" fill="{color}"/>')
                parts.append(f'<g>{marker}<title>{escape(model)} {context} tokens RVV '
                             f'{"on" if enabled=="1" else "off"}: {value:.2f} s</title></g>')
        if not complete_12k[model]:
            parts.append(f'<text x="{x[12288]}" y="{bottom-55}" text-anchor="middle" font-family="DejaVu Sans,Arial,sans-serif" font-size="12" fill="#64748b">pending</text>')
        parts.append(f'<text x="{left+235}" y="{bottom+49}" text-anchor="middle" font-family="DejaVu Sans,Arial,sans-serif" font-size="12" fill="#526071">Prompt tokens</text>')
    parts += ['<text x="43" y="305" transform="rotate(-90 43 305)" text-anchor="middle" font-family="DejaVu Sans,Arial,sans-serif" font-size="13" fill="#3e4b5c">Client TTFT (s, log scale)</text>',
              '<line x1="76" y1="500" x2="108" y2="500" stroke="#94a3b8" stroke-width="3" stroke-dasharray="6 4"/>',
              '<text x="116" y="505" font-family="DejaVu Sans,Arial,sans-serif" font-size="13" fill="#334155">RVV off</text>',
              '<line x1="210" y1="500" x2="242" y2="500" stroke="#2563eb" stroke-width="3"/>',
              '<text x="250" y="505" font-family="DejaVu Sans,Arial,sans-serif" font-size="13" fill="#334155">RVV on (model color)</text>',
              '<text x="1080" y="505" text-anchor="end" font-family="DejaVu Sans,Arial,sans-serif" font-size="12" fill="#526071">Squares: single 12k pair; no extrapolation</text>',
              '</svg>']
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text('\n'.join(parts)+'\n')


if __name__ == '__main__':
    main()
