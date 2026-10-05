#!/usr/bin/env python3
"""Measure K1 RAM streaming and matched direct decode; estimate weight-only roofs."""
import argparse
import collections
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import signal
import statistics
import struct
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fast = load('k1-fast-test')
profiler = load('profile-k1-prefill')


def model_traffic(path):
    """Read only GGUF headers. Count main tensors and the tied/untied output head.

    This is a traffic proxy, not measured DDR bytes: state, activations and
    repeated KV loads are excluded, and tiny norms may remain cached.
    """
    path = Path(path)
    file_bytes = path.stat().st_size
    formats = {0: 'B', 1: 'b', 2: 'H', 3: 'h', 4: 'I', 5: 'i',
               6: 'f', 7: '?', 10: 'Q', 11: 'q', 12: 'd'}
    with path.open('rb') as f:
        def scalar(fmt):
            length = struct.calcsize('<' + fmt)
            data = f.read(length)
            if len(data) != length:
                raise ValueError('truncated GGUF header')
            return struct.unpack('<' + fmt, data)[0]

        def string(read=True):
            length = scalar('Q')
            if f.tell() + length > file_bytes:
                raise ValueError('invalid GGUF string')
            if not read:
                f.seek(length, 1); return None
            return f.read(length).decode()

        def value(kind, wanted=False):
            if kind == 8:
                return string(wanted)
            if kind == 9:
                element, count = scalar('I'), scalar('Q')
                if count > file_bytes or (wanted and count > 10000):
                    raise ValueError('invalid GGUF array')
                if not wanted and element in formats:
                    length = count * struct.calcsize('<' + formats[element])
                    if f.tell() + length > file_bytes:
                        raise ValueError('truncated GGUF array')
                    f.seek(length, 1); return None
                if wanted:
                    return [value(element, True) for _ in range(count)]
                for _ in range(count):
                    value(element, False)
                return None
            return scalar(formats[kind])

        if f.read(4) != b'GGUF' or scalar('I') not in (2, 3):
            raise ValueError('expected GGUF v2/v3')
        tensor_count, kv_count = scalar('Q'), scalar('Q')
        if max(tensor_count, kv_count) > 100000:
            raise ValueError('invalid GGUF header counts')
        meta = {}
        for _ in range(kv_count):
            key = string()
            wanted = key.startswith('qwen35.') or key == 'general.architecture'
            result = value(scalar('I'), wanted)
            if wanted:
                meta[key] = result
        tensors = {}
        for _ in range(tensor_count):
            name, nd = string(), scalar('I')
            if not 1 <= nd <= 4 or name in tensors:
                raise ValueError('invalid tensor name/dimensions')
            dims = [scalar('Q') for _ in range(nd)]
            kind, offset = scalar('I'), scalar('Q')
            block, size = {0: (1, 4), 1: (1, 2), 2: (32, 18), 8: (32, 34)}[kind]
            if any(d < 1 for d in dims) or dims[0] % block:
                raise ValueError('invalid quantized tensor shape')
            tensors[name] = {'bytes': math.prod(dims) // block * size,
                             'dims': dims, 'type': kind, 'offset': offset}
        if meta.get('general.architecture') != 'qwen35':
            raise ValueError('this audit supports the deployed Qwen3.5 models')
        main_layers = meta['qwen35.block_count'] - meta.get('qwen35.nextn_predict_layers', 0)
        blocks, draft_bytes = collections.Counter(), 0
        for name, tensor in tensors.items():
            match = re.match(r'^blk\.(\d+)\.', name)
            if match:
                layer = int(match[1])
                if layer < main_layers:
                    blocks[layer] += tensor['bytes']
                else:
                    draft_bytes += tensor['bytes']
        if set(blocks) != set(range(main_layers)):
            raise ValueError('missing main model layers')
        head = 'output.weight' if 'output.weight' in tensors else 'token_embd.weight'
        total = sum(blocks.values()) + tensors[head]['bytes'] + tensors['output_norm.weight']['bytes']
        attention_layers = sum(f'blk.{i}.attn_k_norm.weight' in tensors for i in range(main_layers))
        kv_heads = meta['qwen35.attention.head_count_kv']
        dk, dv = meta['qwen35.attention.key_length'], meta['qwen35.attention.value_length']
        return {'model_file': str(path), 'file_bytes': file_bytes,
                'main_layers': main_layers, 'full_attention_layers': attention_layers,
                'main_weight_read_proxy_bytes': total, 'mtp_draft_tensor_bytes': draft_bytes,
                'output_head': head, 'output_head_bytes': tensors[head]['bytes'],
                'f16_kv_bytes_per_context_token': attention_layers * kv_heads * (dk + dv) * 2,
                'blocks_bytes': dict(blocks), 'metadata': meta,
                'assumptions': 'One read of main tensors and full output head per decode step; '
                    'draft excluded. KV is a one-pass F16 estimate, not measured DDR traffic. '
                    'Recurrent state, activations, cache effects and repeated loads excluded.'}


def bandwidth_groups(rows, cpus='0,1,2,3'):
    groups = {}
    for size in (256, 1024, 2304):
        selected = [r for r in rows if r['cpus'] == cpus and r['buffer_bytes'] == size * 1024**2]
        identities = {(r['stage'], r['round']) for r in selected}
        expected = {(stage, repeat) for stage in ('before', 'after') for repeat in range(5)}
        if (len(selected) != 10 or identities != expected
                or any(not r['validated'] or r['kernel'] != 'rvv_full_read' for r in selected)):
            raise ValueError('missing/invalid before-and-after bandwidth evidence')
        groups[str(size)] = {'median_GB_per_s': statistics.median(r['GB_per_s'] for r in selected),
                            'min_GB_per_s': min(r['GB_per_s'] for r in selected),
                            'max_GB_per_s': max(r['GB_per_s'] for r in selected),
                            'before_median_GB_per_s': statistics.median(r['GB_per_s'] for r in selected if r['stage'] == 'before'),
                            'after_median_GB_per_s': statistics.median(r['GB_per_s'] for r in selected if r['stage'] == 'after')}
    return groups


def comparisons(timing_rows, traffic, memory_rows):
    groups = bandwidth_groups(memory_rows)
    out = []
    for model in ('2B', '4B'):
        # Predeclared working-set match, not the fastest selected microbenchmark.
        bw = groups['1024' if model == '2B' else '2304']['median_GB_per_s'] * 1e9
        weight = traffic[model]['main_weight_read_proxy_bytes']
        for context in (256, 2048):
            arms = {}
            for mode in (0, 3):
                rows = sorted((r for r in timing_rows if (r['model'], r['context'], r['route']) == (model, context, mode)),
                              key=lambda r: r['repeat'])
                if len(rows) != 3 or [r['repeat'] for r in rows] != [0, 1, 2]:
                    raise ValueError('missing/duplicate timing pairs')
                arms[mode] = rows
            if len({r['prompt_sha256'] for rows in arms.values() for r in rows}) != 1:
                raise ValueError('prompt identity differs across arms')
            identity = len({(r['tokens_sha256'], r['text_sha256']) for rows in arms.values() for r in rows}) == 1
            if not identity:
                raise ValueError('output identity differs across routing arms')
            # Context grows during output; use the average length for this proxy.
            kv = traffic[model]['f16_kv_bytes_per_context_token'] * (context + 31.5)
            record = {'model': model, 'context': context, 'output_tokens': 64, 'paired_repeats': 3,
                      'output_identity': identity, 'bandwidth_GB_per_s': bw / 1e9,
                      'weight_only_roof_tps': bw / weight,
                      'weight_plus_one_pass_kv_roof_tps': bw / (weight + kv),
                      'raw_2666_bus_weight_only_roof_tps': 10.664e9 / weight,
                      'decode_throughput_gain_pct': statistics.median(
                          100 * (b['decode_tps'] / a['decode_tps'] - 1) for a, b in zip(arms[0], arms[3])),
                      'arms': {}}
            for mode, rows in arms.items():
                tps = statistics.median(r['decode_tps'] for r in rows)
                record['arms'][str(mode)] = {
                    'median_decode_tps': tps,
                    'min_decode_tps': min(r['decode_tps'] for r in rows),
                    'max_decode_tps': max(r['decode_tps'] for r in rows),
                    'median_prompt_tps': statistics.median(r['prompt_tps'] for r in rows),
                    'median_ttft_s': statistics.median(r['ttft_s'] for r in rows),
                    'weight_only_streaming_ratio': tps * weight / bw,
                    'weight_plus_kv_streaming_ratio': tps * (weight + kv) / bw}
            out.append(record)
    return {'cluster0_bandwidth': groups, 'comparisons': out}


class Run:
    def __init__(self, root):
        self.root = root
        self.expected = json.loads((root / 'expected-provenance.json').read_text())
        self.routing = json.loads((root / 'routing-provenance.json').read_text())
        self.started = time.monotonic()
        self.memory_rows, self.timing_rows = [], []
        self.summary = {'status': 'running', 'models': {}, 'profiles': {}, 'requests_completed': 0,
                        'requests_planned': 24,
                        'limitations': 'Capped synthetic throughput, not useful-answer quality. '
                            'Streaming ratios are traffic proxies, not measured DDR utilization or removable overhead. '
                            'No hardware DDR counters or verified memory clock; raw peak assumes datasheet 2666 MT/s. '
                            'Three matched repetitions are an engineering screen, not a general performance guarantee.'}

    def save(self):
        self.summary['elapsed_s'] = time.monotonic() - self.started
        fast.write_json(self.root / 'summary.json', self.summary)

    def phase(self, value):
        (self.root / 'phase').write_text(value + '\n')
        print(value, flush=True); self.save()

    def prepare(self):
        self.phase('verify deployed model/runtime provenance')
        self.server = next(Path(p) for p in self.expected['artifacts_sha256'] if p.endswith('/llama-server'))
        paths = {p: h for p, h in self.expected['artifacts_sha256'].items()
                 if '/build/' in p or '/.toolchain/' in p or '/spert/' in p}
        for path, expected in paths.items():
            if fast.digest(path) != expected:
                raise ValueError('runtime hash mismatch: ' + path)
        candidate = Path(self.routing['link'][self.routing['link'].index('-o') + 1])
        if fast.digest(candidate) != self.routing['candidate_library_sha256']:
            raise ValueError('routing library hash mismatch')
        paths[str(candidate)] = self.routing['candidate_library_sha256']
        self.env = {k: v for k, v in os.environ.items() if not k.startswith('SPINE_')}
        self.env.update(self.routing['runtime'])
        self.env.update(SPINE_FA_WIDE_TILE='1', SPINE_FA_K1_LAYOUT='0', SPINE_SPEC_RS='0')
        self.traffic = {}
        for model, info in self.expected['models'].items():
            if fast.digest(info['path']) != info['sha256']:
                raise ValueError('model hash mismatch: ' + model)
            self.traffic[model] = model_traffic(info['path'])
        fast.write_json(self.root / 'model-traffic.json', self.traffic)
        compiler = self.routing['compile'][0]
        command = [compiler, '-O3', '-std=c++17', '-pthread', '-march=rv64gcv', '-mabi=lp64d',
                   str(self.root / 'k1-memory-read.cpp'), '-o', str(self.root / 'memory-read')]
        fast.command(command, self.root / 'compile.log', 120, self.env)
        hardware = {}
        for name in ('cpuinfo', 'meminfo', 'loadavg'):
            hardware[name] = Path('/proc/' + name).read_text()
        hardware['cpu_frequency_khz'] = {
            str(p): p.read_text().strip() for p in Path('/sys/devices/system/cpu').glob('cpu*/cpufreq/scaling_cur_freq')}
        fast.write_json(self.root / 'provenance.json', {
            'libraries_sha256': paths, 'models': self.expected['models'], 'compile': command,
            'compiler': subprocess.check_output([compiler, '--version'], text=True).splitlines()[0],
            'code_sha256': {p.name: fast.digest(p) for p in self.root.iterdir() if p.suffix in ('.py', '.cpp', '.sh')},
            'runtime': {k: v for k, v in self.env.items() if k.startswith('SPINE_') or k == 'LD_LIBRARY_PATH'},
            'hardware_before': hardware, 'routing_provenance': self.routing,
            'settings': {'threads': 4, 'batch': 32, 'ubatch': 32, 'kv': 'f16', 'mtp': False,
                         'routes': [0, 3], 'contexts': [256, 2048], 'repeats': 3, 'output_tokens': 64}})

    def memory(self, stage):
        self.phase('memory streaming ' + stage)
        cpus = ['0', '0,1', '0,1,2,3', '4,5,6,7', '0,1,2,3,4,5,6,7']
        cases = [(size, cpu) for size in (256, 1024, 2304) for cpu in cpus]
        if stage == 'after':
            cases.reverse()
        for size, cpu in cases:
            name = f'memory-{stage}-{size}-{cpu.replace(",", "_")}'
            self.phase(name)
            fast.command([self.root / 'memory-read', size, cpu, 5, 1], self.root / (name + '.jsonl'), 120, self.env)
            rows = [json.loads(line) for line in (self.root / (name + '.jsonl')).read_text().splitlines()]
            if len(rows) != 5 or any(not r['validated'] or r['kernel'] != 'rvv_full_read'
                                     or r['buffer_bytes'] != size * 1024**2 or r['cpus'] != cpu
                                     or not math.isfinite(r['GB_per_s']) or r['GB_per_s'] <= 0 for r in rows):
                raise ValueError('invalid memory measurement')
            self.memory_rows += [dict(r, stage=stage) for r in rows]
            fast.write_json(self.root / 'memory-results.json', self.memory_rows)

    def models(self):
        for model in ('2B', '4B'):
            for context in (256, 2048):
                raw_rows, labels = [], []
                for repeat in range(3):
                    for route in ((0, 3) if repeat % 2 == 0 else (3, 0)):
                        label = f'{model}-p{context}-r{repeat}-route{route}'; labels.append(label)
                        self.phase('direct inference ' + label)
                        env = dict(self.env, SPINE_K1_GEMM_ROUTE=str(route))
                        argv = [sys.executable, HERE / 'bench-lifecycle.py', '--server', self.server,
                                '--model', self.expected['models'][model]['path'], '--label', label,
                                '--mode', 'plain', '--contexts', context, '--n-predict', 64,
                                '--ignore-eos', '--verify-cold', '--capture-token-ids', '--gpu-layers', 0,
                                '--threads', 4, '--batch-size', 32, '--ubatch-size', 32, '--ctx-size', 4096,
                                '--timeout', 900, '--no-context-shift', '--output', self.root / (label + '.jsonl'),
                                '--log', self.root / (label + '.server.log')]
                        fast.command(argv, self.root / (label + '.driver.log'), 960, env)
                        rows = [json.loads(line) for line in (self.root / (label + '.jsonl')).read_text().splitlines()]
                        measured = fast.check_model_records(rows, [label], context, output_tokens=64)[0]
                        log = (self.root / (label + '.server.log')).read_text()
                        for phase in ('prefill', 'single'):
                            wanted = route == 3
                            marker = f'K1_GEMM_ROUTE mode={route} phase={phase} eligible=1 bypass={int(wanted)} buffer_size=131072'
                            if marker not in log:
                                raise ValueError('missing route activation: ' + marker)
                        if 'SPINE_FA_WIDE_TILE: RVV tiled attention enabled for 256-dim heads' not in log:
                            raise ValueError('wide attention activation missing')
                        x = measured['results'][0]; timings = x['timings']
                        if timings.get('predicted_n') != 64 or timings.get('predicted_ms', 0) <= 0:
                            raise ValueError('invalid decode timing')
                        self.timing_rows.append({
                            'model': model, 'context': context, 'repeat': repeat, 'route': route,
                            'decode_tps': 64000 / timings['predicted_ms'],
                            'prompt_tps': context * 1000 / timings['prompt_ms'],
                            'ttft_s': x['ttft_ms'] / 1000, 'wall_s': x['wall_s'],
                            'prompt_sha256': measured['prompt_token_sha256'][0],
                            'tokens_sha256': x['tokens_sha256'], 'text_sha256': x['sha256'],
                            'rss_kib': measured['rss_kib'], 'cold_verified': True})
                        raw_rows += rows
                        self.summary['requests_completed'] = len(self.timing_rows)
                        fast.write_json(self.root / 'timing-results.json', self.timing_rows); self.save()
                fast.check_model_records(raw_rows, labels, context, output_tokens=64)

    def profiles(self):
        # Diagnostic profiles use separate requests; their timing never enters comparisons.
        for model in ('2B', '4B'):
            self.phase('optimized 2k prefill CPU profile ' + model)
            profile = profiler.Profile(self.root, 2048)
            profile.server = self.server
            profile.env = dict(self.env, SPINE_K1_GEMM_ROUTE='3')
            try:
                result = profile.model(model)
                self.summary['profiles'][model] = {'status': 'complete', 'cpu_share_pct': result['cpu_share_pct'],
                                                  'top_self': result['top_self'], 'samples': result['samples']}
            except Exception as error:
                self.summary['profiles'][model] = {'status': 'failed', 'reason': f'{type(error).__name__}: {error}'}
            self.save()

    def report(self):
        analysis = comparisons(self.timing_rows, self.traffic, self.memory_rows)
        self.summary.update(analysis)
        lines = ['# K1 measured memory and direct-inference roofline', '',
                 'Status: ' + self.summary['status'], '', self.summary['limitations'], '',
                 '| Model | Prompt | DDR read proxy GB/s | Weight-only roof tok/s | + one KV pass roof tok/s | Route 0 tok/s | Route 3 tok/s | Paired gain |',
                 '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
        for row in analysis['comparisons']:
            lines.append(f"| {row['model']} | {row['context']} | {row['bandwidth_GB_per_s']:.3f} | "
                         f"{row['weight_only_roof_tps']:.3f} | {row['weight_plus_one_pass_kv_roof_tps']:.3f} | "
                         f"{row['arms']['0']['median_decode_tps']:.3f} | {row['arms']['3']['median_decode_tps']:.3f} | "
                         f"{row['decode_throughput_gain_pct']:.2f}% |")
        lines += ['', 'RAM bandwidth is the median of five scans before and five after inference on cores 0–3.',
                  'Working sets are predeclared: 1 GiB for 2B and 2.25 GiB for 4B. Source bytes only; initialization and warm-up excluded.',
                  'A streaming ratio near one suggests limited bandwidth headroom; a low ratio does not identify the bottleneck.',
                  'If inference exceeds this reference, examine access patterns and working-set assumptions; do not claim impossible hardware performance.',
                  'CPU profiles are separate optimized 2k/one-output-token diagnostics. CPU shares are not wall-time speedups.',
                  'No MTP, retrieval, KV compression, model change or production-default change.', '']
        (self.root / 'summary.md').write_text('\n'.join(lines))

    def run(self):
        try:
            self.prepare(); self.memory('before'); self.models(); self.profiles(); self.memory('after')
            self.summary['status'] = 'complete'
            self.report(); self.phase('complete')
        except BaseException as error:
            self.summary.update(status='failed', reason=f'{type(error).__name__}: {error}')
            self.phase('failed'); raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    def interrupted(signum, frame):
        raise TimeoutError('board budget expired')
    signal.signal(signal.SIGTERM, interrupted)
    Run(args.root.resolve()).run()
