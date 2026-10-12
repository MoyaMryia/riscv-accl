#!/usr/bin/env python3
"""Reinspect archived decode profiles locally; never launch inference or SSH."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
RUN = REPO / 'spacemit/reports/raw/k1-decode-audit-20261007-074314'
HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser_path = RUN / 'profile-k1-prefill.py'
    run = json.loads((RUN / 'run.json').read_text())
    receipt = json.loads((RUN / 'collection-receipt.json').read_text())
    for name in ('exit-status', 'collector-exit-status'):
        assert (RUN / name).read_text().strip() == '0'
    assert digest(parser_path) == run['code_sha256'][parser_path.name]
    spec = importlib.util.spec_from_file_location('frozen_profile', parser_path)
    profile = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(profile)

    # Tie the read-only source inspection to the existing local clean snapshot
    # and measured release, rather than an unrelated current checkout.
    source_manifest = json.loads((REPO / 'spacemit/reports/raw/'
        'local-reference-quality-20261006-194015/source-verification.json').read_text())
    clean = REPO / 'lab/local-reference/source-a990751-clean'
    source_checks = {}
    for name in ('ggml/src/ggml-cpu/ops.cpp', 'ggml/src/ggml-cpu/vec.cpp',
                 'ggml/src/ggml-cpu/vec.h', 'ggml/src/ggml-cpu/ggml-cpu.c'):
        actual = digest(clean / name)
        assert actual == source_manifest['files_sha256'][name]
        source_checks[str((clean / name).relative_to(REPO))] = actual
    manifest = json.loads((REPO / 'spacemit/release/manifest.json').read_text())
    for name, expected in manifest['measured_baseline_source_sha256'].items():
        path = REPO / 'lab/release-preparation' / name
        assert digest(path) == expected
        source_checks[str(path.relative_to(REPO))] = expected
    candidate = REPO / 'spacemit/reports/raw/k1-gemm-routing-20261003-005740/candidate-gemm-routing.cpp'
    expected = manifest['patched_source_sha256']['ggml/src/ggml-cpu/spacemit/ime.cpp']
    assert digest(candidate) == expected
    source_checks[str(candidate.relative_to(REPO))] = expected

    cases = []
    inputs = {str(parser_path.relative_to(REPO)): digest(parser_path)}
    for model in ('2B', '4B'):
        for length in (256, 2048):
            prefix = f'{model}-{length}-profile'
            paths = [RUN / (prefix + suffix) for suffix in
                     ('.stacks.txt', '.profile.json', '.request.json')]
            for path in paths:
                actual = digest(path)
                assert actual == receipt['files_sha256'][path.name]
                inputs[str(path.relative_to(REPO))] = actual
            stacks, saved, request = paths
            original = json.loads(saved.read_text())
            measured = json.loads(request.read_text())
            total = count = 0
            leaves = Counter()
            dot_attention = dot_other_caller = dot_no_caller = 0
            visible = 0
            for period, stack in profile.samples(stacks.read_text()):
                total += period
                count += 1
                leaf = stack[0][0]
                leaves[leaf] += period
                has_attention = any('flash_attn' in name for name, _ in stack)
                visible += period if has_attention else 0
                if leaf == 'ggml_vec_dot_f16':
                    if has_attention:
                        dot_attention += period
                    elif any(name != '[unknown]' and name != leaf for name, _ in stack[1:]):
                        dot_other_caller += period
                    else:
                        dot_no_caller += period
            assert count == original['samples']
            assert abs(total / 1e9 - original['sampled_cpu_s']) < 1e-9
            for entry in original['top_self']:
                # These named symbols are unique in this run's CPU library.
                if entry['symbol'] in ('ggml_vec_dot_f16', 'LOOP_INNER360', 'LOOP_K360'):
                    assert abs(100 * leaves[entry['symbol']] / total - entry['cpu_pct']) < 1e-9
            pct = lambda value: 100 * value / total
            attention_leaf = sum(v for k, v in leaves.items() if 'flash_attn' in k)
            dot = leaves['ggml_vec_dot_f16']
            cases.append({
                'model': model, 'prompt_tokens': length, 'samples': count,
                'decode_tokens_s': measured['timings']['predicted_per_second'],
                'attention_leaf_self_cpu_pct': pct(attention_leaf),
                'attention_visible_stack_cpu_pct': pct(visible),
                'f16_dot_leaf_self_cpu_pct': pct(dot),
                'f16_dot_with_attention_frame_cpu_pct': pct(dot_attention),
                'f16_dot_with_other_decoded_caller_cpu_pct': pct(dot_other_caller),
                'f16_dot_without_decoded_caller_cpu_pct': pct(dot_no_caller),
                'attention_or_f16_dot_leaf_cpu_pct': pct(attention_leaf + dot),
                'ime_leaf_self_cpu_pct': pct(leaves['LOOP_INNER360'] + leaves['LOOP_K360']),
            })
    result = {
        'scope': 'Offline source/hash checks and archived decode stack reanalysis only.',
        'cases': cases, 'source_checks_sha256': source_checks,
        'inputs_sha256': inputs,
        'limitations': [
            'CPU sample shares are not wall-time savings or achievable speedups.',
            'The attention-or-dot column is a union of disjoint self leaves, not attribution of every dot to attention.',
            'Missing caller frames prevent definitive reassignment of most F16 dot samples.',
            'A generic RVV F16 dot already exists; the absent path is a dedicated DK=DV=256 decode implementation.',
            'No new board, model, kernel or quality measurement was performed.',
        ],
    }
    (HERE / 'analysis.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'cases': cases, 'source_files_verified': len(source_checks)}, indent=2))


if __name__ == '__main__':
    main()
