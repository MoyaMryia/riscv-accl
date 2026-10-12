#!/usr/bin/env python3
"""Plot 128-token decode-rate windows from the fixed long-code lifecycle run."""

import argparse
import json
import re
from pathlib import Path
from statistics import mean
from xml.sax.saxutils import escape


LABEL = re.compile(r"^(2B|4B)-(plain|mtp)-code-long$")
COLORS = {"plain": "#2563eb", "mtp": "#ea580c"}


def windows(trace):
    if len(trace) != 4096:
        raise ValueError("require 4,096 streamed events")
    rates = []
    base_time = trace[0][0]
    base_tokens = trace[0][1]
    total = base_tokens
    for time_ms, count in trace[1:]:
        total += count
        if total - base_tokens >= 128:
            elapsed_ms = time_ms - base_time
            if elapsed_ms <= 0:
                raise ValueError("nonpositive window duration")
            rates.append(1000 * (total - base_tokens) / elapsed_ms)
            base_time, base_tokens = time_ms, total
    tail_tokens = total - base_tokens
    tail_ms = trace[-1][0] - base_time
    if tail_tokens >= 64 and tail_ms > 0:
        rates.append(1000 * tail_tokens / tail_ms)
    if len(rates) != 32:
        raise ValueError(f"expected 32 windows, got {len(rates)}")
    return rates


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    groups = {}
    for row in map(json.loads, args.input.open()):
        if row.get("kind") != "measurement":
            continue
        match = LABEL.fullmatch(row["label"])
        if not match:
            continue
        size, mode = match.groups()
        result = row["results"][0]
        if row["context_tokens"] != 128 or result["tokens_predicted"] != 4096 or result["stop_type"] != "limit":
            raise ValueError(f"incomplete trace: {row['label']}")
        groups.setdefault((size, mode), []).append((windows(result["event_trace"]), result["timings"]["predicted_per_second"]))
    if any(len(groups.get((size, mode), [])) != 2 for size in ("2B", "4B") for mode in ("plain", "mtp")):
        raise ValueError("require two complete traces per model and mode")

    width, height = 1120, 620
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Decode rates in 128-token windows for 2B and 4B, direct and MTP">',
             '<rect width="1120" height="620" fill="white"/>',
             '<text x="58" y="42" font-family="Arial,sans-serif" font-size="23" font-weight="700" fill="#172133">Long-code decode rate by 128-token window</text>',
             '<text x="58" y="67" font-family="Arial,sans-serif" font-size="13" fill="#526071">128-token C++ prompt · 4,096 generated tokens · two complete requests per mode · MUSE-Pi-Pro</text>']
    for panel, size in enumerate(("2B", "4B")):
        left = 75 + panel * 540
        top, bottom, right = 126, 490, left + 445
        ymax = 9.0 if size == "2B" else 3.5
        x = lambda i: left + (right - left) * i / 31
        y = lambda v: bottom - (bottom - top) * v / ymax
        parts.append(f'<text x="{left}" y="109" font-family="Arial,sans-serif" font-size="18" font-weight="700" fill="#172133">{size}</text>')
        for tick in (0, 2, 4, 6, 8) if size == "2B" else (0, 1, 2, 3):
            yy = y(tick)
            parts += [f'<line x1="{left}" y1="{yy:.1f}" x2="{right}" y2="{yy:.1f}" stroke="#e7ebf0"/>',
                      f'<text x="{left-12}" y="{yy+4:.1f}" text-anchor="end" font-family="Arial,sans-serif" font-size="12" fill="#526071">{tick}</text>']
        parts += [f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#64748b"/>',
                  f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#64748b"/>']
        for tick in (1, 8, 16, 24, 32):
            xx = x(tick - 1)
            parts.append(f'<text x="{xx:.1f}" y="{bottom+23}" text-anchor="middle" font-family="Arial,sans-serif" font-size="12" fill="#526071">{tick}</text>')
        for mode in ("plain", "mtp"):
            runs = groups[(size, mode)]
            vals = [mean(run[0][i] for run in runs) for i in range(32)]
            points = " ".join(f"{'M' if i == 0 else 'L'}{x(i):.1f},{y(value):.1f}" for i, value in enumerate(vals))
            color = COLORS[mode]
            parts.append(f'<path d="{points}" fill="none" stroke="{color}" stroke-width="2.8"/>')
            for i, value in enumerate(vals):
                parts.append(f'<circle cx="{x(i):.1f}" cy="{y(value):.1f}" r="2.5" fill="{color}"><title>{escape(size)} {escape(mode)} window {i+1}: {value:.3f} tok/s</title></circle>')
            avg = mean(run[1] for run in runs)
            parts.append(f'<text x="{left+8}" y="{bottom+58+(0 if mode == "plain" else 20)}" font-family="Arial,sans-serif" font-size="13" fill="{color}">{("Direct" if mode == "plain" else "MTP")}: {avg:.2f} tok/s overall</text>')
    parts += ['<text x="34" y="310" transform="rotate(-90 34 310)" text-anchor="middle" font-family="Arial,sans-serif" font-size="13" fill="#526071">Decode tokens/s</text>', '<text x="560" y="596" text-anchor="middle" font-family="Arial,sans-serif" font-size="12" fill="#526071">Window number (128 output tokens each); MTP and direct output diverge on this prompt</text>', '</svg>']
    args.output.write_text("\n".join(parts) + "\n")


if __name__ == "__main__":
    main()
