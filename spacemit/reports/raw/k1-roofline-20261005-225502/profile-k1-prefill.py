#!/usr/bin/env python3
"""Sample verified cold requests on the existing K1 binary, without rebuilding."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import select
import signal
import subprocess
import time

HERE = Path(__file__).resolve().parent


def module(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


life, fast = module('bench-lifecycle'), module('k1-fast-test')


def samples(text):
    """Read period-weighted perf stacks; never count parent and child twice."""
    header = re.compile(r'^\S.*?:\s+(\d+)\s+cpu-clock:u:\s*$')
    frame = re.compile(r'^\s+[0-9a-f]+\s+(.+)\s+\(([^()]*)\)\s*$')
    period, stack = None, []
    for line in text.splitlines() + ['END']:
        found = header.match(line)
        if found or (line and not line[0].isspace()):
            if period is not None:
                if not stack:
                    raise ValueError('sample has no decoded leaf')
                yield period, stack
            period, stack = (int(found[1]), []) if found else (None, [])
        elif period is not None:
            found = frame.match(line)
            if found:
                stack.append((found[1], found[2]))


def summarize(text):
    groups, leaves, copies = Counter(), Counter(), 0
    total = count = deep = unresolved = 0
    for period, stack in samples(text):
        if period <= 0:
            raise ValueError('invalid sample weight')
        count += 1; total += period; deep += len(stack) > 1
        unresolved += stack[0][0] == '[unknown]'
        leaves[stack[0]] += period
        group = 'other_or_unattributed'
        for name, _ in stack:
            if 'gated_delta_net' in name or 'gdn_' in name:
                group = 'recurrent_visible_stack'; break
            if 'flash_attn' in name:
                group = 'attention_visible_stack'; break
            if any(s in name.lower() for s in ('gemm', 'matmul', 'mul_mat')):
                group = 'matmul_visible_stack'; break
        groups[group] += period
        if group == 'attention_visible_stack' and any(
                'memcpy2d' in n or 'memcpy' in n for n, _ in stack):
            copies += period
    if count < 100 or not total:
        raise ValueError(f'insufficient samples: {count}')
    return {'samples': count, 'sampled_cpu_s': total / 1e9,
            'multi_frame_samples_pct': 100 * deep / count,
            'unknown_leaf_samples_pct': 100 * unresolved / count,
            'cpu_share_pct': {k: 100 * v / total for k, v in groups.items()},
            'attention_copy_visible_cpu_pct': 100 * copies / total,
            'top_self': [{'symbol': n, 'dso': d, 'cpu_pct': 100 * v / total}
                         for (n, d), v in leaves.most_common(30)],
            'limitations': 'Visible stacks give lower bounds when frames are missing. '
            'Attention copy samples exclude inlined K transpose; they are not total packing cost. '
            'CPU shares are sampled user CPU time, not wall-time percentages or speedups.'}


def stop(proc, sig=signal.SIGTERM):
    if proc is None or proc.poll() is not None:
        return
    os.killpg(proc.pid, sig)
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL); proc.wait()


def control(proc, write_fd, read_fd, command):
    if proc.poll() is not None:
        raise RuntimeError('perf exited before control command')
    os.write(write_fd, (command + '\n').encode())
    # The board perf writes its terminating NUL after the acknowledgment line.
    if not select.select([read_fd], [], [], 10)[0] or os.read(read_fd, 32).rstrip(b'\0') != b'ack\n':
        raise RuntimeError('perf control acknowledgment missing')


def checked(argv, output, timeout=120):
    with output.open('w') as out, output.with_suffix(output.suffix + '.err').open('w') as err:
        subprocess.run(list(map(str, argv)), stdout=out, stderr=err, check=True, timeout=timeout)


class Profile:
    def __init__(self, root, tokens):
        self.root, self.tokens = root, tokens
        self.expected = json.loads((root / 'expected-provenance.json').read_text())
        self.summary = {'status': 'running', 'tokens': tokens, 'models': {},
                        'event': 'cpu-clock:u', 'frequency_hz': 199, 'call_graph': 'fp',
                        'scope': 'Cold request after health/tokenization; one output token included. '
                        'One diagnostic request per model; no throughput or quality claim.'}
        self.started = time.monotonic()

    def phase(self, name):
        (self.root / 'phase').write_text(name + '\n'); print(name, flush=True)

    def prepare(self):
        self.phase('verify provenance')
        paths = self.expected['artifacts_sha256']
        self.server = next(Path(p) for p in paths if p.endswith('/llama-server'))
        self.source = self.server.parents[2]
        head = subprocess.check_output(['git', '-C', self.source, 'rev-parse', '--short=7', 'HEAD'], text=True).strip()
        changed = set(subprocess.check_output(['git', '-C', self.source, 'diff', 'HEAD', '--name-only'], text=True).splitlines())
        if head != 'a990751' or changed != set(self.expected['source_sha256']):
            raise ValueError('unexpected reused source state')
        for name, expected in self.expected['source_sha256'].items():
            if fast.digest(self.source / name) != expected:
                raise ValueError('source hash mismatch: ' + name)
        libraries = {p: h for p, h in paths.items() if '/build/' in p or '/.toolchain/' in p or '/spert/' in p}
        for p, expected in libraries.items():
            if fast.digest(p) != expected:
                raise ValueError('binary/runtime hash mismatch: ' + p)
        for m, info in self.expected['models'].items():
            if fast.digest(info['path']) != info['sha256']:
                raise ValueError('model hash mismatch: ' + m)
        self.env = dict(os.environ, SPINE_FA_WIDE_TILE='1', SPINE_FA_K1_LAYOUT='0')
        provenance = {'source_commit': head, 'source_sha256': self.expected['source_sha256'],
                      'libraries_sha256': libraries, 'models': self.expected['models'],
                      'ops_sha256': fast.digest(self.source / 'ggml/src/ggml-cpu/ops.cpp'),
                      'code_sha256': {p.name: fast.digest(p) for p in HERE.glob('*.py')},
                      'perf_version': subprocess.check_output(['perf', '--version'], text=True).strip(),
                      'settings': {'threads': 4, 'batch': 32, 'ubatch': 32, 'f16_kv': True,
                                   'output_tokens': 1, 'layout': 0, 'frequency_hz': 199},
                      'runtime': {k: v for k, v in self.env.items() if k.startswith('SPINE_') or k == 'LD_LIBRARY_PATH'}}
        fast.write_json(self.root / 'provenance.json', provenance)

    def model(self, name):
        self.phase('profile ' + name)
        model = Path(self.expected['models'][name]['path'])
        url = 'http://127.0.0.1:18085'
        argv = [str(self.server), '-m', str(model), '-t', '4', '-c', '4096',
                '--parallel', '1', '-b', '32', '-ub', '32', '-fa', 'on', '-ngl', '0',
                '-ctk', 'f16', '-ctv', 'f16', '--host', '127.0.0.1', '--port', '18085']
        server = perf = None
        fds = []
        with (self.root / (name + '.server.log')).open('w') as log, (self.root / (name + '.perf.log')).open('w') as plog:
            try:
                server = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT,
                                          env=self.env, start_new_session=True)
                loaded = time.monotonic(); life.wait_healthy(server, url, 600)
                startup = time.monotonic() - loaded
                prompt = life.make_prompt(url, self.tokens)
                ctl_r, ctl_w = os.pipe(); ack_r, ack_w = os.pipe()
                fds = [ctl_r, ctl_w, ack_r, ack_w]
                data = self.root / (name + '.perf.data')
                perf_argv = ['perf', 'record', '-e', 'cpu-clock:u', '-F', '199', '--call-graph', 'fp',
                             '-D', '-1', '--control', f'fd:{ctl_r},{ack_w}',
                             '-p', str(server.pid), '-o', str(data)]
                perf = subprocess.Popen(perf_argv, stdout=plog, stderr=subprocess.STDOUT,
                                        pass_fds=(ctl_r, ack_w), start_new_session=True)
                control(perf, ctl_w, ack_r, 'enable')
                result = life.complete(url, prompt, 1, 900, 0, True, False, True, True)
                control(perf, ctl_w, ack_r, 'disable')
                life.verify_cold(result, self.tokens)
                if (result['error'] or result['stop_type'] != 'limit' or result['tokens_predicted'] != 1
                        or result['streamed_tokens'] != 1 or len(result.get('token_ids', [])) != 1):
                    raise ValueError('incomplete one-token request')
                result.pop('first_at'); result.pop('finished_at')
                stop(perf, signal.SIGINT)
                if perf.returncode not in (0, -signal.SIGINT):
                    raise RuntimeError('perf record failed')
                fast.write_json(self.root / (name + '.request.json'), {
                    'model': name, 'command': argv, 'startup_s': startup,
                    'prompt_token_sha256': hashlib.sha256(json.dumps(prompt, separators=(',', ':')).encode()).hexdigest(),
                    'result': result, 'profiler_command': perf_argv})
            finally:
                stop(perf, signal.SIGINT); stop(server)
                for fd in fds:
                    os.close(fd)
        if 'SPINE_FA_WIDE_TILE: RVV tiled attention enabled for 256-dim heads' not in (self.root / (name + '.server.log')).read_text():
            raise ValueError('wide attention activation missing')
        script = self.root / (name + '.stacks.txt')
        checked(['perf', 'script', '-i', data, '-F', 'comm,pid,tid,time,event,ip,sym,dso,period'], script)
        profile = summarize(script.read_text())
        checked(['perf', 'report', '-i', data, '--stdio', '--no-children', '--call-graph', 'none',
                 '--percent-limit', '0.1'], self.root / (name + '.self.txt'))
        # Save lost-event diagnostics separately; an incomplete recording cannot pass.
        lost = self.root / (name + '.lost.txt')
        checked(['perf', 'script', '-i', data, '--show-lost-events'], lost)
        if re.search(r'PERF_RECORD_LOST', lost.read_text()):
            raise ValueError('perf recording lost samples')
        annotations = []
        for i, symbol in enumerate(p['symbol'] for p in profile['top_self']
                                   if 'flash_attn' in p['symbol'] or 'gated_delta_net' in p['symbol'] or 'memcpy2d' in p['symbol']):
            target = self.root / f'{name}.annotate-{i}.txt'
            try:
                checked(['perf', 'annotate', '-i', data, '--stdio', '-s', symbol], target)
                annotations.append({'symbol': symbol, 'file': target.name, 'status': 'saved'})
            except (subprocess.SubprocessError, OSError) as exc:
                annotations.append({'symbol': symbol, 'file': target.name, 'status': str(exc)})
        profile.update(request=result, annotations=annotations, startup_s=startup)
        fast.write_json(self.root / (name + '.profile.json'), profile)
        return profile

    def save(self):
        self.summary['elapsed_s'] = time.monotonic() - self.started
        fast.write_json(self.root / 'summary.json', self.summary)
        lines = ['# K1 cold-prefill profile', '', 'Status: ' + self.summary['status'], '', self.summary['scope'], '',
                 '| Model | Cold prompt time | Samples | Recurrent visible | Attention visible | Matmul visible | Other |',
                 '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
        for m, p in self.summary['models'].items():
            shares = p['cpu_share_pct']
            percentages = [shares.get(k, 0) for k in ('recurrent_visible_stack', 'attention_visible_stack', 'matmul_visible_stack', 'other_or_unattributed')]
            lines.append(f"| {m} | {p['request']['timings']['prompt_ms']/1000:.2f} s | {p['samples']} | " +
                         ' | '.join(f'{v:.2f}%' for v in percentages) + ' |')
        lines += ['', 'Sampled CPU shares are not wall-time shares. Missing frames leave work unattributed.',
                  'Attention copy samples exclude inlined K transpose and do not measure total packing cost.',
                  'Profiling can perturb timings. No optimization speedup or answer-quality claim.', '', self.summary.get('reason', '')]
        (self.root / 'summary.md').write_text('\n'.join(lines) + '\n')

    def run(self):
        try:
            self.prepare()
            for m in ('2B', '4B'):
                self.summary['models'][m] = self.model(m); self.save()
            self.summary['status'] = 'complete'; self.save(); self.phase('complete')
        except BaseException as exc:
            self.summary.update(status='failed', reason=f'{type(exc).__name__}: {exc}')
            self.save(); self.phase('failed'); raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--tokens', type=int, default=2048)
    args = parser.parse_args()
    if not 32 <= args.tokens <= 2048:
        parser.error('require 32..2048 tokens')
    def interrupted(signum, frame):
        raise TimeoutError('profiling interrupted')
    signal.signal(signal.SIGTERM, interrupted)
    Profile(args.root.resolve(), args.tokens).run()
