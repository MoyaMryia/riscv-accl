#!/usr/bin/env python3
"""Verify layout activation and summarize the bounded same-binary comparison."""

import json
import re
import statistics
import sys
from pathlib import Path


def summarize(root):
    groups = {}
    for line in (root/'results.jsonl').read_text().splitlines():
        row = json.loads(line)
        if row['kind'] != 'measurement':
            continue
        match = re.fullmatch(r'(2B|4B)-layout-(0|16|32)-pass([1-6])', row['label'])
        if not match:
            raise ValueError('unexpected benchmark label')
        model, layout, _ = match.groups()
        log = (root/(row['label']+'.log')).read_text()
        if 'SPINE_FA_WIDE_TILE: RVV tiled attention enabled for 256-dim heads' not in log:
            raise ValueError(f'baseline RVV path did not activate: {row["label"]}')
        if layout != '0':
            marker = f'SPINE_FA_K1_LAYOUT: compact Q={layout} KV=64 F16 scratch enabled'
            if marker not in log:
                raise ValueError(f'layout did not activate: {row["label"]}')
        result = row['results'][0]
        groups.setdefault((model, row['context_tokens'], int(layout)), []).append(result)
    summaries = []
    for model in ('2B', '4B'):
        for context in (128, 2048):
            controls = groups[(model, context, 0)]
            for layout in (0, 16, 32):
                runs = groups[(model, context, layout)]
                if len(runs) != 2:
                    raise ValueError('each arm needs exactly two launches')
                base = statistics.mean(r['ttft_ms'] for r in controls)
                mean = statistics.mean(r['ttft_ms'] for r in runs)
                summaries.append({'model': model, 'prompt_tokens': context, 'layout_q_rows': layout,
                                  'ttft_ms_per_launch': [r['ttft_ms'] for r in runs],
                                  'mean_ttft_ms': mean, 'ttft_reduction_pct': 100*(1-mean/base),
                                  'mean_prefill_tokens_s': statistics.mean(r['timings']['prompt_per_second'] for r in runs),
                                  'mean_decode_tokens_s': statistics.mean(r['timings']['predicted_per_second'] for r in runs)})
    data = {'numeric_gate': (root/'numeric-status').read_text().strip(), 'comparisons': summaries,
            'limitations': 'Two launches per arm at 128/2048 tokens. No long-context result or statistical significance claim.'}
    (root/'summary.json').write_text(json.dumps(data, indent=2)+'\n')
    lines = ['# K1 compact attention layout pilot', '', data['numeric_gate'], '', data['limitations'], '',
             '| Model | Prompt | Query rows | TTFT seconds | Reduction | Prefill tok/s |',
             '| --- | ---: | ---: | ---: | ---: | ---: |']
    for r in summaries:
        lines.append(f"| {r['model']} | {r['prompt_tokens']} | {r['layout_q_rows'] or 64} | "
                     f"{r['mean_ttft_ms']/1000:.3f} | {r['ttft_reduction_pct']:.2f}% | {r['mean_prefill_tokens_s']:.3f} |")
    (root/'summary.md').write_text('\n'.join(lines)+'\n')


if __name__ == '__main__':
    summarize(Path(sys.argv[1]))
