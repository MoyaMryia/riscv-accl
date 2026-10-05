#!/usr/bin/env python3
"""Run bounded correctness, attention timing and one-token model screens on K1."""
import argparse
import hashlib
import itertools
import json
import math
import os
import re
import signal
from pathlib import Path
import statistics
import struct
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
LAYOUTS = (0, 16, 32)
OPERATOR_BUDGET_S = 300
ORDERS = ((0, 16, 32), (32, 16, 0), (16, 32, 0),
          (0, 32, 16), (32, 0, 16), (16, 0, 32))


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, data):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, indent=2) + '\n')
    temporary.replace(path)


def model_shape(path):
    """Read GGUF metadata only; skip vocabulary arrays without materializing them."""
    formats = {0: 'B', 1: 'b', 2: 'H', 3: 'h', 4: 'I', 5: 'i',
               6: 'f', 7: '?', 10: 'Q', 11: 'q', 12: 'd'}
    values = {}
    with path.open('rb') as f:
        def scalar(fmt):
            size = struct.calcsize('<' + fmt)
            data = f.read(size)
            if len(data) != size:
                raise ValueError('truncated GGUF metadata')
            return struct.unpack('<' + fmt, data)[0]
        def string(read=True):
            length = scalar('Q')
            if length > path.stat().st_size:
                raise ValueError('invalid GGUF string length')
            if read:
                data = f.read(length)
                if len(data) != length:
                    raise ValueError('truncated GGUF string')
                return data.decode()
            f.seek(length, 1)
        def value(kind, read=False):
            if kind == 8:
                return string(read)
            if kind == 9:
                element, count = scalar('I'), scalar('Q')
                if count > path.stat().st_size:
                    raise ValueError('invalid GGUF array length')
                if read:
                    raise ValueError('unexpected array-valued attention metadata')
                if element in formats:
                    f.seek(count * struct.calcsize('<' + formats[element]), 1)
                else:
                    for _ in range(count):
                        value(element)
                return None
            if kind not in formats:
                raise ValueError('unsupported GGUF metadata type')
            return scalar(formats[kind])
        if f.read(4) != b'GGUF' or scalar('I') not in (2, 3):
            raise ValueError('expected GGUF v2/v3')
        scalar('Q')
        count = scalar('Q')
        if count > 100000:
            raise ValueError('invalid GGUF metadata count')
        for _ in range(count):
            key = string()
            wanted = key == 'general.architecture' or any(key.endswith(s) for s in (
                '.attention.head_count', '.attention.head_count_kv',
                '.attention.key_length', '.attention.value_length'))
            result = value(scalar('I'), wanted)
            if wanted:
                values[key] = result
    arch = values['general.architecture']
    shape = {k: values[f'{arch}.attention.{field}'] for k, field in (
        ('heads', 'head_count'), ('kv_heads', 'head_count_kv'),
        ('dk', 'key_length'), ('dv', 'value_length'))}
    if (arch != 'qwen35' or shape['dk'] != 256 or shape['dv'] != 256
            or shape['heads'] % shape['kv_heads'] != 0):
        raise ValueError('model is not eligible for this layout experiment')
    return shape


def command(argv, log, timeout, env=None):
    with log.open('w') as output:
        proc = subprocess.Popen(list(map(str, argv)), stdout=output, stderr=subprocess.STDOUT,
                                start_new_session=True, env=env)
        try:
            status = proc.wait(timeout=timeout)
        except BaseException:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
            raise
        if status:
            raise subprocess.CalledProcessError(status, argv)


def gate(base, candidate, threshold=3.0):
    if len(base) < 2 or len(candidate) < 2:
        raise ValueError('screen needs at least two measurements per arm')
    if any(not math.isfinite(v) or v <= 0 for v in base + candidate):
        raise ValueError('invalid timing')
    control = statistics.mean(base)
    gain = 100 * (1 - statistics.mean(candidate) / control)
    noise = 100 * (max(base) - min(base)) / control
    return {'reduction_pct': gain, 'control_range_pct': noise,
            'advance': gain > max(threshold, noise),
            'clear_regression': gain < -max(threshold, noise),
            'base_ms': base, 'candidate_ms': candidate}


def check_model_records(rows, expected_labels, tokens, output_tokens=1):
    measurements = [r for r in rows if r.get('kind') == 'measurement']
    if len(measurements) != len(expected_labels):
        raise ValueError('missing or extra model requests')
    if {r['label'] for r in measurements} != set(expected_labels):
        raise ValueError('missing, extra or duplicate model arms')
    config = {r['label']: r for r in rows if r.get('kind') == 'config'}
    hashes, prompt_hashes = set(), set()
    for r in measurements:
        c = config[r['label']]
        if c['n_predict'] != output_tokens or c.get('cache_prompt') or not c.get('verify_cold'):
            raise ValueError('wrong screen configuration')
        if r['context_tokens'] != tokens or len(r['results']) != 1:
            raise ValueError('wrong prompt length or concurrency')
        x = r['results'][0]
        if (x.get('error') or x['stop_type'] != 'limit' or x['tokens_predicted'] != output_tokens
                or x['streamed_tokens'] != output_tokens or len(x.get('token_ids', [])) != output_tokens
                or x['timings'].get('cache_n') != 0 or x['timings'].get('prompt_n') != tokens):
            raise ValueError('incomplete, cached or invalid output-token screen')
        token_digest = hashlib.sha256(json.dumps(x['token_ids'], separators=(',', ':')).encode()).hexdigest()
        if (x.get('tokens_sha256') != token_digest or not re.fullmatch('[0-9a-f]{64}', x.get('sha256', ''))
                or not x.get('ttft_ms') or x['timings'].get('prompt_ms', 0) <= 0):
            raise ValueError('missing hashes or prefill timing')
        hashes.add((x['tokens_sha256'], x['sha256']))
        prompt_hashes.add(tuple(r.get('prompt_token_sha256', [])))
        if not all(re.fullmatch('[0-9a-f]{64}', h) for h in r.get('prompt_token_sha256', [])):
            raise ValueError('invalid prompt token hash')
    if len(hashes) != 1 or len(prompt_hashes) != 1 or not next(iter(prompt_hashes)):
        raise ValueError('output or input tokens differ across arms')
    return measurements


class Runner:
    def __init__(self, root, build_run, mode):
        self.root, self.build_run, self.mode = root, build_run, mode
        self.source = build_run / 'source'
        self.server = self.source / 'build/bin/llama-server'
        self.models = {m: Path.home() / f'Projects/spacemit-llama/models/Qwen3.5-{m}-MTP-Q4_0-embQ4_0-dv64k.gguf'
                       for m in ('2B', '4B')}
        self.summary = {'status': 'running', 'mode': mode, 'stages': {},
                        'limitations': 'Engineering screen, no significance, decode or answer-quality claim.'}
        self.started = time.monotonic()

    def phase(self, text):
        (self.root / 'phase').write_text(text + '\n')
        print(text, flush=True)

    def stage(self, name, function):
        self.phase(name)
        ledger = self.root / (name + '.stage.json')
        if ledger.exists():
            old = json.loads(ledger.read_text())
            if old['fingerprint'] != self.fingerprint:
                raise ValueError('resume provenance mismatch')
            if any(digest(self.root / p) != h for p, h in old['artifacts'].items()):
                raise ValueError('resume artifact mismatch')
            self.summary['stages'][name] = old
            return old['result']
        started = time.monotonic()
        result, artifacts = function()
        state = {'fingerprint': self.fingerprint, 'duration_s': time.monotonic() - started,
                 'result': result, 'artifacts': {str(p.relative_to(self.root)): digest(p) for p in artifacts}}
        write_json(ledger, state)
        self.summary['stages'][name] = state
        self.save()
        return result

    def prepare(self):
        self.phase('prepare')
        if (self.build_run / 'exit-status').read_text().strip() != '0':
            raise ValueError('reuse requires a successfully completed layout build')
        expected = json.loads((self.root / 'expected-source.json').read_text())
        if subprocess.check_output(['git', '-C', str(self.source), 'rev-parse', '--short=7', 'HEAD'], text=True).strip() != 'a990751':
            raise ValueError('unexpected reused source commit')
        changed = set(subprocess.check_output(['git', '-C', str(self.source), 'diff', '--name-only'], text=True).splitlines())
        if changed != set(expected):
            raise ValueError('unexpected changed files in reused checkout')
        for name, h in expected.items():
            if digest(self.source / name) != h:
                raise ValueError(f'reused source mismatch: {name}')
        command(['cmake', '--build', self.source / 'build', '--target', 'llama-server', '-j4'],
                self.root / 'build.log', 600)
        cxx = Path.home() / 'Projects/llm-bench/.toolchain/gcc14/usr/bin/g++-14'
        command([cxx, '-O3', '-std=c++17', '-march=rv64gcv_zfh_zvfh_zicbop_zihintpause_zba', '-mabi=lp64d',
                 *['-I' + str(self.source / p) for p in ('ggml/include', 'ggml/src', 'ggml/src/ggml-cpu')],
                 HERE / 'test-k1-attention-layout.cpp', '-L' + str(self.server.parent),
                 '-lggml-cpu', '-lggml-base', '-pthread', '-o', self.root / 'test-layout'],
                self.root / 'test-build.log', 120)
        self.shapes = {m: model_shape(p) for m, p in self.models.items()}
        artifacts = [self.server, *self.server.parent.glob('*.so*'),
                     self.source / 'build/CMakeCache.txt', self.root / 'test-layout',
                     HERE / 'k1-fast-test.py', HERE / 'bench-lifecycle.py',
                     HERE / 'test-k1-attention-layout.cpp', HERE / 'run-k1-fast-test-board.sh',
                     Path.home() / 'Projects/llm-bench/.toolchain/spine-tcm/libspine_tcm.so']
        # Vendor runtime filenames vary. Record actual shared objects in both directories.
        artifacts = [p for p in artifacts if p.exists()]
        for directory in os.environ['LD_LIBRARY_PATH'].split(':')[:2]:
            artifacts.extend(Path(directory).glob('*.so*'))
        provenance = {'source_sha256': expected, 'artifacts_sha256': {str(p): digest(p) for p in artifacts if p.is_file()},
                      'models': {m: {'path': str(p), 'sha256': digest(p), 'shape': self.shapes[m]}
                                 for m, p in self.models.items()},
                      'compiler': subprocess.check_output([str(cxx), '--version'], text=True).splitlines()[0],
                      'runtime': {k: v for k, v in os.environ.items() if k.startswith('SPINE_') or k == 'LD_LIBRARY_PATH'},
                      'settings': {'threads': 4, 'batch': 32, 'ubatch': 32, 'output_tokens': 1,
                                   'threshold_pct': 3, 'operator_blocks': 6, 'operator_budget_s': OPERATOR_BUDGET_S}}
        self.fingerprint = hashlib.sha256(json.dumps(provenance, sort_keys=True).encode()).hexdigest()
        old = self.root / 'provenance.json'
        if old.exists() and json.loads(old.read_text()) != provenance:
            raise ValueError('resume source/build/model/runtime changed')
        write_json(old, provenance)
        self.summary['fingerprint'] = self.fingerprint
        self.summary['shapes'] = self.shapes

    def numeric(self):
        files = []
        hashes = []
        for rows in LAYOUTS:
            log, output = self.root / f'numeric-{rows}.log', self.root / f'layout-{rows}.bin'
            command([self.root / 'test-layout', output, '--long'], log, 120,
                    dict(os.environ, SPINE_FA_K1_LAYOUT=str(rows)))
            if 'PASS: 241 concurrent cases' not in log.read_text():
                raise ValueError('native numerical cases incomplete')
            files.extend((log, output)); hashes.append(digest(output))
        if len(set(hashes)) != 1:
            raise ValueError('native output differs between layouts')
        return {'cases_per_layout': 241, 'bitwise_equal': True, 'concurrent': True}, files

    def operators(self):
        deadline = time.monotonic() + OPERATOR_BUDGET_S
        all_rows, files = [], []
        shapes = [self.shapes[m][k] for m in ('2B', '4B') for k in ('heads', 'kv_heads')]
        for block, order in enumerate(ORDERS):
            for layout in order:
                env = dict(os.environ, SPINE_FA_K1_LAYOUT=str(layout))
                out, log = self.root / f'operator-{block}-{layout}.jsonl', self.root / f'operator-{block}-{layout}.log'
                left = deadline - time.monotonic()
                if left <= 0:
                    raise TimeoutError(f'operator stage exceeded {OPERATOR_BUDGET_S} seconds')
                with out.open('w') as stdout, log.open('w') as stderr:
                    subprocess.run(list(map(str, [self.root / 'test-layout', '--bench', block, *shapes])),
                                   stdout=stdout, stderr=stderr, env=env, check=True, timeout=left)
                marker = f'SPINE_FA_K1_LAYOUT: compact Q={layout} KV=64 F16 scratch enabled'
                if layout and marker not in log.read_text():
                    raise ValueError('operator layout did not activate')
                batch = [json.loads(l) for l in out.read_text().splitlines()]
                expected = {(self.shapes[m]['heads'], self.shapes[m]['kv_heads'], nk, mask)
                            for m in self.models for nk in (128, 2048, 8192) for mask in (0, 1)}
                if len(batch) != len(expected) or {(r['heads'], r['kv_heads'], r['kv_rows'], r['mask']) for r in batch} != expected:
                    raise ValueError('operator shapes incomplete')
                for r in batch:
                    if (r['layout'] != layout or r['block'] != block or r['slowest_worker_ms'] < 100
                            or r['worker_cpus'] != [0, 1, 2, 3]
                            or not math.isfinite(r['ms_per_call']) or r['ms_per_call'] <= 0):
                        raise ValueError('invalid operator timing or affinity')
                all_rows.extend(batch); files.extend((out, log))
        comparisons = []
        for m, shape in self.shapes.items():
            for nk, mask in itertools.product((128, 2048, 8192), (0, 1)):
                arm = {l: [r['ms_per_call'] for r in all_rows if r['heads'] == shape['heads']
                           and r['kv_heads'] == shape['kv_heads'] and r['kv_rows'] == nk
                           and r['mask'] == mask and r['layout'] == l] for l in LAYOUTS}
                for l in (16, 32):
                    comparisons.append({'model': m, 'kv_rows': nk, 'mask': mask, 'layout': l,
                                        **gate(arm[0], arm[l])})
        return {'records': len(all_rows), 'blocks': 6, 'comparisons': comparisons,
                'input_policy': 'Repeated deterministic tensors, warm allocation; model confirmation required.'}, files

    def model_stage(self, name, model, tokens, order):
        files, rows, labels = [], [], []
        for i, layout in enumerate(order):
            left = self.model_deadline - time.monotonic()
            if left < 1:
                raise TimeoutError('model stage budget exceeded')
            label = f'{name}-{model}-q{layout}-pass{i+1}'
            out, log, driver = [self.root / (label + suffix) for suffix in ('.jsonl', '.log', '.driver.log')]
            for path in (out, log, driver):
                if path.exists():
                    attempt = 1
                    while path.with_name(path.name + f'.attempt{attempt}').exists():
                        attempt += 1
                    path.rename(path.with_name(path.name + f'.attempt{attempt}'))
            command([sys.executable, HERE / 'bench-lifecycle.py', '--server', self.server,
                     '--model', self.models[model], '--label', label, '--mode', 'plain',
                     '--contexts', tokens, '--n-predict', 1, '--ignore-eos', '--verify-cold',
                     '--capture-token-ids', '--gpu-layers', 0, '--ctx-size', 12288 if tokens == 8192 else 4096,
                     '--timeout', min(1800, int(left)), '--output', out, '--log', log], driver, left,
                    dict(os.environ, SPINE_FA_K1_LAYOUT=str(layout)))
            text = log.read_text()
            if 'SPINE_FA_WIDE_TILE: RVV tiled attention enabled for 256-dim heads' not in text:
                raise ValueError('model RVV activation missing')
            if layout and f'SPINE_FA_K1_LAYOUT: compact Q={layout} KV=64 F16 scratch enabled' not in text:
                raise ValueError('model compact activation missing')
            rows.extend(json.loads(l) for l in out.read_text().splitlines()); labels.append(label)
            files.extend((out, log, driver))
        measured = check_model_records(rows, labels, tokens)
        by_layout = {l: [r['results'][0] for r in measured if r['label'].split('-q')[1].split('-')[0] == str(l)] for l in set(order)}
        comparison = {}
        for l in set(order) - {0}:
            base = [r['timings']['prompt_ms'] for r in by_layout[0]]
            candidate = [r['timings']['prompt_ms'] for r in by_layout[l]]
            if len(base) >= 2:
                comparison[str(l)] = gate(base, candidate)
            else:
                comparison[str(l)] = {'reduction_pct': 100 * (1 - candidate[0] / base[0]),
                                      'base_ms': base, 'candidate_ms': candidate, 'single_pair': True}
            comparison[str(l)]['ttft_ms'] = {str(k): [r['ttft_ms'] for r in v] for k, v in by_layout.items()}
        return {'model': model, 'tokens': tokens, 'order': list(order), 'requests': len(measured),
                'comparisons': comparison, 'outputs_equal': True, 'uncached_verified': True}, files

    def save(self):
        self.summary['elapsed_s'] = time.monotonic() - self.started
        write_json(self.root / 'summary.json', self.summary)
        lines = ['# K1 fast test', '', 'Status: ' + self.summary['status'], '', self.summary['limitations'], '',
                 '| Stage | Seconds | Result |', '| --- | ---: | --- |']
        for name, s in self.summary['stages'].items():
            r = s['result']
            description = (f"{r['cases_per_layout']} cases per layout, bitwise equal" if 'cases_per_layout' in r
                           else f"{r['blocks']} balanced blocks, {r['records']} records" if 'blocks' in r
                           else '; '.join(f"Q{k}: {v['reduction_pct']:.2f}% prompt-time reduction"
                                          for k, v in r.get('comparisons', {}).items()))
            lines.append(f"| {name} | {s['duration_s']:.2f} | {description} |")
        lines.extend(['', self.summary.get('reason', ''), '', 'No answer-quality or decode-rate conclusion follows from one-token requests.'])
        (self.root / 'summary.md').write_text('\n'.join(lines) + '\n')

    def run(self):
        try:
            self.prepare()
            self.stage('numeric', self.numeric)
            if self.mode == 'smoke':
                self.summary.update(status='smoke passed', reason='Native gate only; no model performance claim.')
            else:
                self.stage('operators', self.operators)
                self.model_deadline = time.monotonic() + (7200 if self.mode == 'confirm-long' else 2700)
                screen = self.stage('screen', lambda: self.model_stage('screen', '2B', 512, (0, 16, 32, 32, 16, 0)))
                candidates = [int(k) for k, v in screen['comparisons'].items() if v['advance']]
                if not candidates:
                    self.summary.update(status='inconclusive', reason='No candidate exceeds the 3%/control-noise screen. Long and quality tests skipped.')
                else:
                    qualified = []
                    for layout in candidates:
                        result = self.stage(f'confirm-2B-q{layout}', lambda l=layout: self.model_stage('confirm', '2B', 2048, (0, l, l, 0)))
                        if result['comparisons'][str(layout)]['advance']:
                            qualified.append((layout, result['comparisons'][str(layout)]['reduction_pct']))
                    if qualified:
                        winner = max(qualified, key=lambda item: item[1])[0]
                        result = self.stage('confirm-4B', lambda: self.model_stage('confirm', '4B', 1024, (0, winner, winner, 0)))
                        if result['comparisons'][str(winner)]['advance']:
                            self.summary.update(status='screen eligible', winner=winner,
                                                reason='Both-model screen passed; fresh long-context and quality confirmation remain.')
                            if self.mode == 'confirm-long':
                                for model, order in (('2B', (0, winner)), ('4B', (winner, 0))):
                                    self.stage('long-' + model, lambda m=model, o=order: self.model_stage('long', m, 8192, o))
                                long_results = [self.summary['stages']['long-' + m]['result']['comparisons'][str(winner)] for m in self.models]
                                self.summary.update(status='long pilot complete', reason='Single 8k pair per model; no significance or quality claim.')
                                if any(r['reduction_pct'] < -3 for r in long_results):
                                    self.summary.update(status='long regression', reason='Long-context pilot regressed by more than 3%; retain control.')
                        else:
                            self.summary.update(status='inconclusive', reason='4B confirmation failed the benefit threshold; retain control.')
                    else:
                        self.summary.update(status='inconclusive', reason='2B/2k confirmation failed the benefit threshold; retain control.')
            self.save(); self.phase(self.summary['status'])
            return 0
        except Exception as exc:
            self.summary.update(status='failed', reason=f'{type(exc).__name__}: {exc}')
            self.save(); self.phase('failed')
            raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path)
    p.add_argument('build_run', type=Path)
    p.add_argument('--mode', choices=('smoke', 'screen', 'confirm-long'), default='screen')
    args = p.parse_args()
    return Runner(args.root.resolve(), args.build_run.resolve(), args.mode).run()


if __name__ == '__main__':
    raise SystemExit(main())
