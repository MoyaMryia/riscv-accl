#!/usr/bin/env python3
"""从原始请求独立复算组合停止记录，不启动测试。"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import statistics


ORDER = ('C0', 'H', 'L', 'P', 'B', 'F', 'F', 'B', 'P', 'L', 'H', 'C0')
PAIRS = (('P', 'C0'), ('P', 'H'), ('P', 'L'), ('F', 'C0'), ('F', 'P'), ('F', 'B'))


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':')).encode()).hexdigest()


def metric(base, candidate):
    require(len(base) == len(candidate) == 2, 'paired request count differs')
    require(all(math.isfinite(x) and x > 0 for x in base + candidate), 'invalid time')
    mean = statistics.mean(base)
    reduction = 100 * (1 - statistics.mean(candidate) / mean)
    spread = 100 * (max(base) - min(base)) / mean
    return {'reduction_pct': reduction, 'control_range_pct': spread,
            'advance': reduction > max(3, spread),
            'clear_regression': reduction < -max(3, spread),
            'base_ms': base, 'candidate_ms': candidate}


def passed(values, pair, tokens, outputs):
    stable = lambda keys: all(not values[key]['clear_regression'] for key in keys)
    prefill = lambda: all(values[key]['advance'] for key in ('prefill', 'ttft'))
    if outputs == 1:
        return stable(values) if pair in (('P', 'L'), ('F', 'P')) else prefill()
    if pair == ('P', 'L') or (pair == ('F', 'P') and tokens == 512):
        return stable(values)
    if pair in (('F', 'C0'), ('F', 'P')) and tokens == 2048:
        return values['decode']['advance']
    return stable(('decode',))


def audit(root):
    archived = json.loads((root/'result.json').read_text())
    require(archived['order'] == list(ORDER), 'order differs')
    comparisons, requests, diagnostics = [], 0, []
    for tokens in (512, 2048):
        for model in ('2B', '4B'):
            for outputs in (1, 65):
                arms, input_hashes, output_hashes = {}, set(), set()
                for index, arm in enumerate(ORDER):
                    label = f'{model}-p{tokens}-n{outputs}-{arm}-{index}'
                    path = root/(label+'.jsonl')
                    if not path.exists():
                        require(not any(root.glob(f'{model}-p{tokens}-n{outputs}-*.jsonl')),
                                'partial configuration cannot be accepted')
                        return finish(archived, comparisons, requests, diagnostics)
                    rows = [json.loads(line) for line in path.read_text().splitlines()]
                    configs = [row for row in rows if row.get('kind') == 'config']
                    measurements = [row for row in rows if row.get('kind') == 'measurement']
                    require(len(configs) == len(measurements) == 1, 'request record count differs')
                    config, record = configs[0], measurements[0]
                    launch = json.loads((root/(label+'.config.json')).read_text())
                    bits = {'C0': 0, 'H': 2, 'L': 8, 'P': 6, 'B': 1, 'F': 7}[arm]
                    flags = {'SPINE_K1_FA_GQA': str(int(bool(bits & 1))),
                             'SPINE_K1_SSM_CONV': '3' if bits & 2 or arm == 'L' else '0',
                             'SPINE_GDN_PREFILL': str(int(bool(bits & 4) or arm == 'L')),
                             'SPINE_K1_GDN_REVISION': str(int(bool(bits & 4))),
                             'SPINE_K1_GEMM_ROUTE': '3', 'SPINE_FA_WIDE_TILE': '1',
                             'SPINE_FA_K1_LAYOUT': '0', 'SPINE_K1_TRACE': '1'}
                    require(all(launch['runtime'].get(k) == v for k, v in flags.items()),
                            'arm flags differ')
                    log = (root/(label+'.server.log')).read_text()
                    require('K1_GEMM_ROUTE mode=3' in log, 'route evidence absent')
                    require(('SPINE_GDN_PREFILL: scalar-gate K1 RVV fusion enabled' in log) ==
                            (flags['SPINE_GDN_PREFILL'] == '1'), 'GDN path differs')
                    require(('SPINE_GDN_PREFILL_R2: retained two state segments' in log) ==
                            (flags['SPINE_K1_GDN_REVISION'] == '1'), 'GDN revision path differs')
                    if bits & 4:
                        require(set(re.findall(r'K1_GDN_R2 worker=(\d+) workers=4 state=128', log)) ==
                                {'0', '1', '2', '3'}, 'GDN worker evidence differs')
                    if outputs == 65 and bits & 1:
                        workers = re.findall(r'K1_FA path=B1 .*? history=(\d+) .*? worker=(\d+) workers=4', log)
                        require({worker for history, worker in workers if int(history) >= 512} ==
                                {'0', '1', '2', '3'}, 'attention worker evidence differs')
                    if not bits & 1:
                        require('K1_FA path=B1 ' not in log, 'inactive attention path present')
                    require(config['label'] == record['label'] == label, 'label differs')
                    require(config['threads'] == 4 and config['batch_size'] == config['ubatch_size'] == 32,
                            'thread or batch configuration differs')
                    require(config['cache_type_k'] == config['cache_type_v'] == 'f16', 'KV type differs')
                    require(config['verify_cold'] and not config['cache_prompt'] and config['ignore_eos'],
                            'cold configuration differs')
                    require(config['n_predict'] == outputs and record['context_tokens'] == tokens,
                            'token count differs')
                    require(len(record['results']) == 1, 'concurrency differs')
                    value = record['results'][0]
                    require(not value['error'] and value['stop_type'] == 'limit', 'request failed')
                    require(value['tokens_predicted'] == value['streamed_tokens'] == outputs and
                            len(value['token_ids']) == outputs, 'output incomplete')
                    require(value['tokens_sha256'] == digest(value['token_ids']), 'output receipt differs')
                    require(value['timings']['cache_n'] == 0 and value['timings']['prompt_n'] == tokens,
                            'cache or prompt count differs')
                    require(record['prompt_token_sha256'], 'input receipt absent')
                    input_hashes.add(tuple(record['prompt_token_sha256']))
                    output_hashes.add((value['tokens_sha256'], value['sha256']))
                    snapshots = json.loads((root/(label+'.threads.json')).read_text())
                    require(snapshots and all(x['threads'] for x in snapshots), 'thread snapshot absent')
                    arms.setdefault(arm, []).append(value)
                    requests += 1
                require(len(input_hashes) == len(output_hashes) == 1, 'paired tokens or text receipt differs')
                for pair in PAIRS:
                    candidate, reference = pair
                    values = {}
                    for name, key in (('prefill', 'prompt_ms'), ('ttft', None), ('decode', 'predicted_ms')):
                        if name == 'decode' and outputs == 1:
                            continue
                        times = {arm: [v['timings'][key] if key else v['ttft_ms'] for v in arms[arm]]
                                 for arm in pair}
                        values[name] = metric(times[reference], times[candidate])
                    row = {'model': model, 'tokens': tokens, 'outputs': outputs,
                           'candidate': candidate, 'reference': reference, 'metrics': values,
                           'passed': passed(values, pair, tokens, outputs)}
                    comparisons.append(row)
                    if not row['passed']:
                        diagnostics.append({'configuration': [model, tokens, outputs],
                            'times_by_arm': {arm: {'prefill_ms': [x['timings']['prompt_ms'] for x in v],
                                                  'decode_ms': [x['timings']['predicted_ms'] for x in v]}
                                            for arm, v in arms.items()}})
                        return finish(archived, comparisons, requests, diagnostics)
    return finish(archived, comparisons, requests, diagnostics)


def finish(archived, comparisons, requests, diagnostics):
    require(comparisons == archived['comparisons'], 'independent comparison differs from controller')
    require(requests == archived['completed_requests'], 'request total differs')
    status = 'performance-gate-stopped' if any(not x['passed'] for x in comparisons) else 'eligible'
    require(status == archived['status'], 'stop status differs')
    return {'status': status, 'verified_requests': requests, 'verified_comparisons': len(comparisons),
            'failures': [x for x in comparisons if not x['passed']], 'diagnostics': diagnostics,
            'limitations': ['Input lists and output text are represented by saved receipts.',
                            'Thread snapshots do not prove worker placement during decode.',
                            'This audit does not compare complete state dumps or validate hardware causes.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('round_directory', type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.round_directory), ensure_ascii=False, indent=2))
