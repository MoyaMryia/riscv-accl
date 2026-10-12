#!/usr/bin/env python3
"""Recompute the resumed-measures matrix cells from archived lifecycle records.

Parses the compact matrix table in a report (default 2026-09-27-resumed-measures.md),
recomputes TTFT, prefill, decode, end-to-end rate, and peak RSS from the archived
lifecycle JSONL records, and checks the exact-output claim per model and prompt
length. Numeric cells pass when the recomputed value rounds to the reported cell
within rounding plus 0.2% slack. Exits nonzero on any mismatch so it can gate
report edits. Exact claims require token and text hashes to match across both
RVV arms or both weight formats; Complete claims require a valid complete arm.
"""

import argparse
import json
import re
from pathlib import Path

ROW = re.compile(r'^\| (2B|4B) \| ([RI]) \| ([^|]+) \| ([01]) \| ([0-9,.]+) \| ([0-9,.]+) \|'
                 r' ([0-9,.]+) \| ([0-9,.]+) \| ([0-9,.]+) \| (.+?) \|$')

FILES = [
    'lifecycle-rvv32.jsonl',
    'lifecycle-rvv32-long.jsonl',
    'lifecycle-integrated-rvv-12k.jsonl',
    'lifecycle-integrated-4b-rvv-12k-resume.jsonl',
    'lifecycle-weight-compare-2k.jsonl',
    '2B-q4w-f16kv-16k-rvv0.jsonl',
    '2B-q4w-f16kv-16k-rvv1.jsonl',
    '4B-q4w-f16kv-16k-rvv1.jsonl',
    '4B-q4w-f16kv-16k-rvv0-extended.jsonl',
    '2B-q4w-f16kv-32768-rvv1-bounded.jsonl',
]


def cell_float(text):
    return float(text.replace(',', ''))


def decimals(text):
    return len(text.replace(',', '').partition('.')[2])


def load_entries(raw_dir):
    """Flat list of (file, label, context_tokens, record) measurement tuples."""
    entries = []
    for name in FILES:
        path = raw_dir / name
        if not path.exists():
            raise SystemExit(f'missing archived file: {path}')
        with path.open(encoding='utf-8') as handle:
            for line in handle:
                row = json.loads(line)
                if row.get('kind') == 'measurement':
                    entries.append((name, row['label'], row['context_tokens'], row))
    return entries


def pick(entries, wanted_file=None, label_set=None, model=None, prompt_tokens=None):
    out = []
    for name, label, context_tokens, record in entries:
        if wanted_file is not None and name != wanted_file:
            continue
        if label_set is not None and label not in label_set:
            continue
        if model is not None:
            prefix = f'8k-{model}-' if label.startswith('8k-') else f'{model}-'
            if not label.startswith(prefix):
                continue
        if prompt_tokens is not None and context_tokens != prompt_tokens:
            continue
        out.append(record)
    if not out:
        raise SystemExit(f'no records matched file={wanted_file} labels={label_set} '
                         f'model={model} prompt={prompt_tokens}')
    return out


def row_records(entries, model, build, prompt_cell, arm):
    """Map one matrix row to its archived records."""
    if prompt_cell.endswith('actual prompt'):
        if build != 'I':
            raise SystemExit(f'actual-prompt archives require integrated build: {build}')
        prompt_tokens = int(cell_float(prompt_cell.split()[0]))
        if prompt_tokens == 16384:
            name = f'{model}-q4w-f16kv-16k-rvv{arm}.jsonl'
            if model == '4B' and arm == '0':
                name = '4B-q4w-f16kv-16k-rvv0-extended.jsonl'
            return pick(entries, wanted_file=name)
        if prompt_tokens == 32768:
            if model != '2B' or arm != '1':
                raise SystemExit('32k archive contains only the optimized 2B arm')
            return pick(entries, wanted_file='2B-q4w-f16kv-32768-rvv1-bounded.jsonl')
        raise SystemExit(f'unhandled actual-prompt cell: {prompt_cell}')
    prompt_tokens = int(cell_float(prompt_cell.split()[0]))
    if 'weights' in prompt_cell:
        if build != 'I' or arm != '1':
            raise SystemExit('weight-comparison archives require integrated RVV-on build')
        weight = 'Q4' if 'Q4_0 weights' in prompt_cell else 'Q8'
        labels = {f'{model}-{weight}_0-f16kv-rvv-2k-pass{pass_n}' for pass_n in (1, 2, 3, 4)}
        return pick(entries, label_set=labels, model=model, prompt_tokens=prompt_tokens)
    if build == 'R':
        prefix = '8k-' if prompt_tokens == 8192 else ''
        labels = {f'{prefix}{model}-rvv32-{arm}-pass{pass_n}' for pass_n in (1, 2, 3, 4)}
        return pick(entries, label_set=labels, model=model, prompt_tokens=prompt_tokens)
    if prompt_tokens == 12288 and build == 'I':
        label = (f'2B-rvv32-integrated-12k-{arm}' if model == '2B'
                 else f'4B-rvv32-integrated-12k-resume-{arm}')
        return pick(entries, label_set={label}, model=model, prompt_tokens=prompt_tokens)
    raise SystemExit(f'unhandled row: {model} {build} {prompt_cell} arm={arm}')


def per_launch_metrics(record):
    result = record['results'][0]
    return {
        'ttft': result['ttft_ms'] / 1000,
        'prefill': result['timings']['prompt_per_second'],
        'decode': result['timings']['predicted_per_second'],
        'e2e': result['streamed_tokens'] / result['wall_s'],
        'rss': record['rss_kib']['max'] / 1024,
        'hash': result.get('tokens_sha256'),
        'text_hash': result.get('sha256'),
        'tokens': result.get('streamed_tokens'),
        'tokens_predicted': result.get('tokens_predicted'),
        'error': result.get('error'),
    }


def valid_hash(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-fA-F]{64}', value) is not None


def comparison_key(model, build, prompt_cell):
    # Weight-format measurements are a separate campaign from RVV comparisons
    # with the same nominal prompt length.
    family = 'weights' if 'weights' in prompt_cell else ('actual' if prompt_cell.endswith('actual prompt') else 'rvv')
    return model, build, family, int(cell_float(prompt_cell.split()[0]))


def close(recomputed, reported, digits):
    tolerance = 10 ** -digits + 0.002 * abs(reported)
    rounded = float(f'%.{digits}f' % recomputed)
    return abs(rounded - reported) <= tolerance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('raw_dir', type=Path)
    args = parser.parse_args()

    entries = load_entries(args.raw_dir)
    checked = 0
    failures = []
    comparisons = {}
    print('| Row | TTFT | Prefill | Decode | End-to-end | Peak RSS | Launches | Output audit |')
    print('| --- | --- | --- | --- | --- | --- | ---: | --- |')

    for line in args.report.read_text(encoding='utf-8').splitlines():
        match = ROW.match(line)
        if not match:
            continue
        model, build, prompt_cell, arm, ttft_c, prefill_c, decode_c, e2e_c, rss_c, audit_c = match.groups()
        prompt_cell = prompt_cell.strip()
        metrics = [per_launch_metrics(r) for r in row_records(entries, model, build, prompt_cell, arm)]
        cells = [('TTFT', ttft_c, 'ttft'), ('Prefill', prefill_c, 'prefill'),
                 ('Decode', decode_c, 'decode'), ('E2E', e2e_c, 'e2e'), ('RSS', rss_c, 'rss')]
        status = []
        for name, cell, key in cells:
            recomputed = sum(m[key] for m in metrics) / len(metrics)
            ok = close(recomputed, cell_float(cell), decimals(cell))
            status.append(f'{name} {"OK" if ok else "MISMATCH"}')
            if not ok:
                failures.append(f'{model} {prompt_cell} rvv={arm} {name}: '
                                f'recomputed {recomputed:.4f} vs reported {cell}')
        hashes = {m['hash'].lower() if valid_hash(m['hash']) else None for m in metrics}
        text_hashes = {m['text_hash'].lower() if valid_hash(m['text_hash']) else None for m in metrics}
        complete = all(m['tokens'] == m['tokens_predicted'] == 32 and m['error'] is None for m in metrics)
        audit_ok = len(hashes) == len(text_hashes) == 1 and None not in hashes and None not in text_hashes and complete
        claim = audit_c.strip().split(';', 1)[0]
        if claim not in ('Exact', 'Complete'):
            failures.append(f'{model} {prompt_cell}: unsupported output audit claim {audit_c}')
        if not audit_ok:
            failures.append(f'{model} {prompt_cell} rvv={arm}: distinct hashes={len(hashes)} '
                            f'text hashes={len(text_hashes)} missing/invalid={None in hashes or None in text_hashes} '
                            f'complete={complete}')
        key = comparison_key(model, build, prompt_cell)
        variant = ('Q4_0' if 'Q4_0 weights' in prompt_cell else 'Q8_0') if key[2] == 'weights' else arm
        comparisons.setdefault(key, []).append({'variant': variant, 'claim': claim,
                                                'hashes': hashes, 'text_hashes': text_hashes})
        print(f'| {model} {build} {prompt_cell} rvv={arm} | ' + ' | '.join(status) +
              f' | {len(metrics)} | {"hash-ok" if audit_ok else "BAD"} |')
        checked += 1

    for key, rows in comparisons.items():
        if not any(row['claim'] == 'Exact' for row in rows):
            continue
        expected = {'Q4_0', 'Q8_0'} if key[2] == 'weights' else {'0', '1'}
        variants = {row['variant'] for row in rows}
        if variants != expected or len(rows) != 2:
            failures.append(f'{key}: Exact requires both distinct comparison arms {sorted(expected)}')
        hashes = set().union(*(row['hashes'] for row in rows))
        text_hashes = set().union(*(row['text_hashes'] for row in rows))
        if len(hashes) != 1 or None in hashes or len(text_hashes) != 1 or None in text_hashes:
            failures.append(f'{key}: Exact token/text hashes differ across comparison arms or are missing')

    print(f'\nrows checked: {checked}')
    if not checked:
        raise SystemExit('no matrix rows parsed from the report')
    if failures:
        print('FAILURES:')
        for failure in failures:
            print(f'  {failure}')
        raise SystemExit(1)
    print('all recomputed cells match the report within rounding tolerance')


if __name__ == '__main__':
    main()
