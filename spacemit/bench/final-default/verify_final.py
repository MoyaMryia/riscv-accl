"""核验下载后的最终对照，并汇总原始性能数据。"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import statistics

from effective import verify as effective
from verify_search import receipts, sha


def read(path):
    return json.loads(path.read_text())


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def require(value, reason):
    if not value:
        raise ValueError(reason)


def describe(values):
    return dict(n=len(values), mean=statistics.mean(values), median=statistics.median(values),
        min=min(values), max=max(values))


def metrics(row):
    return dict(ttft_ms=row['ttft_ms'], prompt_ms=row['timings']['prompt_ms'],
        prefill_tps=row['timings']['prompt_per_second'], decode_ms=row['decode_ms'],
        decode_tps=row['timings']['predicted_per_second'], wall_s=row['wall_s'],
        peak_rss_kib=row['rss_kib']['max'])


def verify(board, delivery, version):
    require(os.environ.get('TMUX'), 'run the check in tmux')
    comparison = board / ('comparison-' + version)
    validation = board / ('final-validation-' + version)
    tools = board / ('comparison-tools-' + version)
    policy = read(delivery / 'package/default-policy.json')
    config = policy['config']
    counts = dict(comparison=receipts(comparison), validation=receipts(validation))
    summary = read(comparison / 'summary.json')
    require(summary['status'] == 'pass' and summary['comparison'] == 'pass', 'comparison does not pass')
    validated = read(validation / 'summary.json')
    require(validated['status'] == 'verified-limited', 'delivery validation does not pass')
    require(validated['stages']['state']['records'] == 64, 'default state coverage differs')
    require(validated['stages']['relocation']['status'] == 'pass', 'relocation does not pass')
    identity = read(comparison / 'identity.json')['inputs']
    actual_tools = {p.name: sha(p) for p in tools.iterdir() if p.is_file()}
    require(actual_tools == identity['code'], 'comparison controller differs')
    validation_identity = read(validation / 'identity.json')
    require(sha(tools / 'validate_delivery.py') == validation_identity['tool_sha256'], 'validation controller differs')
    require(sha(tools / 'effective.py') == validation_identity['effective_tool_sha256'], 'default checker differs')
    require(sha(delivery / 'package/unified.patch') == validation_identity['source']['patch_sha256'], 'source patch differs')
    final_build = board / ('final-' + version) / 'build'
    record = read(final_build / 'build-receipt.json')
    require(record == validation_identity['final_build'], 'final build receipt differs')
    actual_binaries = {p.name: sha(p) for p in (final_build / 'bin').iterdir() if p.is_file()}
    require(actual_binaries == record['binaries'], 'final binary set differs')
    baseline = read(board / 'baseline-load-build/build-receipt.json')
    require(baseline['source_commit'] == '5ad05d8796cb094ee23a3a0152874f8a2b3060f8', 'baseline commit differs')
    require(baseline['graph_code_unchanged'], 'baseline graph differs')
    for kind, build in (('baseline', baseline), ('candidate', validation_identity['reference_build']), ('final', record)):
        pins = {Path(name).name: value for name, value in identity['builds'][kind].items()}
        require(all(build['binaries'][name] == value for name, value in pins.items()), 'comparison binary identity differs: ' + kind)
    for model in ('2B', '4B'):
        require(identity['models'][model]['sha256'] == read(delivery / 'package/manifest.json')['models'][model]['sha256'], 'model identity differs')
        effective((validation / ('relocated-' + model + '.server.log')).read_text(), config)
        launch = read(validation / ('relocated-' + model + '.launch.json'))
        require(set(launch['environment']) == {'LD_LIBRARY_PATH'}, 'relocation environment retains experiment flags')
    expected = [f'answer-{model}-{kind}' for model in ('2B', '4B') for kind in ('baseline', 'candidate', 'final')]
    for model, length in (('2B', 512), ('4B', 512), ('2B', 2048), ('4B', 2048)):
        expected.extend(f'compare-{model}-p{length}-{i}-' + ('baseline', 'final')[((i // 2) + i % 2) % 2] for i in range(6))
    expected.extend(('long-2B-p8192-0-baseline', 'long-2B-p8192-1-final',
        'long-4B-p8192-0-final', 'long-4B-p8192-1-baseline'))
    require(summary['completed'] == expected, 'comparison order or coverage differs')
    rows = {p.parent.name: read(p) for p in comparison.glob('*/result.json')}
    require(set(rows) == set(expected) and len(rows) == 34, 'comparison request set differs')
    prompts = read(comparison / 'prompts.json')
    natural = {}
    for name, row in rows.items():
        folder = comparison / name
        require(row['status'] == 'pass', 'request fails: ' + name)
        require(row['identity'] == digest(identity), 'request identity differs: ' + name)
        require(row['context'] == 12288, 'context differs: ' + name)
        require(row['config'] == (config if row['kind'] == 'final' else dict(mask=0, threads=4, ubatch=32)), 'request configuration differs')
        props = read(folder / 'properties.json')
        require(props['total_slots'] == 1 and props['default_generation_settings']['n_ctx'] == 12288, 'server properties differ')
        require(props['default_generation_settings']['params']['speculative.types'] == 'none', 'speculative decode is active')
        launch = read(folder / 'launch.json')
        if row['kind'] == 'final':
            effective((folder / 'server.log').read_text(), config)
            argv = launch['argv']
            require(argv[1::2] == ['-m', '--alias', '--host', '--port'] and len(argv) == 9, 'final launch adds performance flags')
            require(set(launch['environment']) == {'LD_LIBRARY_PATH'}, 'final environment retains experiment flags')
        request = read(folder / 'request.json')
        if row['natural']:
            answer = read(folder / 'answer.json')
            answer_hash = hashlib.sha256(answer['answer'].encode()).hexdigest()
            require(answer_hash == row['answer_sha256'] == answer['answer_sha256'], 'natural answer hash differs')
            require(answer['finish_reason'] == 'stop' and not answer['reasoning_text'], 'natural completion differs')
            require(answer['usage']['prompt_tokens_details']['cached_tokens'] == 0, 'natural answer reuses cache')
            require(answer['usage']['completion_tokens'] == row['output_tokens'], 'natural output count differs')
            require(row['quality']['pass'] and row['quality']['checks'] == 106, 'natural quality check fails')
            require(request == read(tools / (row['model'] + '-answer.json'))['request'], 'natural request differs')
            natural[name] = dict(sha256=answer_hash, output_tokens=row['output_tokens'], checks=row['quality']['checks'])
            continue
        length = row['input_tokens']
        prompt = prompts[row['model']]['tokens'][:length]
        forced = prompts[row['model']]['forced_token']
        require(request == dict(prompt=prompt, n_predict=65, temperature=0, seed=42,
            cache_prompt=False, stream=True, ignore_eos=True, return_tokens=True, id_slot=0,
            logit_bias=[[forced, 1000.0]]), 'performance payload differs')
        require(row['prompt_sha256'] == digest(prompt), 'prompt hash differs')
        require(row['token_ids'] == [forced] * 65 and row['tokens_predicted'] == row['output_tokens'] == 65, 'output history differs')
        require(hashlib.sha256(row['text'].encode()).hexdigest() == row['text_sha256'], 'output text hash differs')
        require(row['stop_type'] == 'limit' and row['error'] is None, 'performance request does not complete')
        timing = row['timings']
        require(timing['cache_n'] == 0 and timing['prompt_n'] == length and timing['predicted_n'] == 65, 'cold token counts differ')
        require(row['decode_ms'] == timing['predicted_ms'], 'decode timing differs')
        require(all(math.isfinite(value) and value > 0 for value in metrics(row).values()), 'performance metric is invalid')
        require(math.isclose(timing['prompt_per_second'], length * 1000 / timing['prompt_ms'], rel_tol=1e-8), 'prefill throughput differs')
        require(math.isclose(timing['predicted_per_second'], 65 * 1000 / timing['predicted_ms'], rel_tol=1e-8), 'decode throughput differs')
        samples = read(folder / 'threads.json')
        require(max(s['rss_kib'] for s in samples if s['rss_kib'] is not None) == row['rss_kib']['max'], 'RSS sample maximum differs')
    for model in ('2B', '4B'):
        require(natural[f'answer-{model}-final']['sha256'] == natural[f'answer-{model}-candidate']['sha256'] == policy['quality'][model]['selected'], 'final natural answer differs from selected control')
    measurements = []
    for model in ('2B', '4B'):
        for length in (512, 2048, 8192):
            selected = [r for r in rows.values() if not r['natural'] and r['model'] == model and r['input_tokens'] == length]
            arms = {kind: [r for r in selected if r['kind'] == kind] for kind in ('baseline', 'final')}
            count = 1 if length == 8192 else 3
            require(all(len(arm) == count for arm in arms.values()), 'performance sample count differs')
            require(len({r['prompt_sha256'] for r in selected}) == 1 and len({r['text_sha256'] for r in selected}) == 1, 'comparison work differs')
            aggregate = {kind: {metric: describe([metrics(r)[metric] for r in arm]) for metric in metrics(arm[0])} for kind, arm in arms.items()}
            changes = {}
            gates = {}
            for metric, values in aggregate['baseline'].items():
                ratio = aggregate['final'][metric]['mean'] / values['mean']
                changes[metric] = (ratio - 1) * 100
                if metric in ('ttft_ms', 'decode_ms'):
                    threshold = max(3, (values['max'] - values['min']) / values['mean'] * 100)
                    gates[metric] = dict(threshold_percent=threshold, regression=(ratio - 1) * 100 > threshold)
            measurements.append(dict(model=model, input_tokens=length, output_tokens=65, pairs=count,
                aggregate=aggregate, final_change_percent=changes, regression_checks=gates,
                scope='single observed pair' if count == 1 else 'three measured pairs'))
    return dict(status='pass', version=policy['version'], receipts=counts, requests=34, natural=natural,
        policy_sha256=sha(delivery / 'package/default-policy.json'), measurements=measurements,
        limitations=['fixed synthetic performance history', 'three short pairs per shape',
            'one long pair per model', 'formal model origin and conversion remain pending',
            'short default state does not establish long state acceptance'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', type=Path, required=True)
    parser.add_argument('--delivery', type=Path, required=True)
    parser.add_argument('--version', default='r3')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'output exists')
    result = verify(args.board, args.delivery, args.version)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
