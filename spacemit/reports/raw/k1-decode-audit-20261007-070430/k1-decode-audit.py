#!/usr/bin/env python3
"""Isolated decode CPU profiling and branch-aware GEMM diagnostics; no speedup claim."""
import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import re
import select
import signal
import subprocess
import time
import urllib.request

HERE = Path(__file__).resolve().parent
import importlib.util


def module(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ime = module('k1-ime-test')
profile = module('profile-k1-prefill')
patcher = module('make-k1-decode-audit')
fast, life = ime.fast, profile.life
SECTIONS = ('activation_quantization', 'staging_copies', 'gemm', 'grid_wait', 'pair_wait')


def perf_control(proc, write_fd, read_fd, command):
    if proc.poll() is not None:
        raise RuntimeError('perf exited before control command')
    os.write(write_fd, (command+'\n').encode())
    deadline = time.monotonic()+10
    ack = b''
    while time.monotonic() < deadline:
        if not select.select([read_fd], [], [], max(0, deadline-time.monotonic()))[0]:
            break
        chunk = os.read(read_fd, 64)
        if not chunk:
            break
        # Board perf can send the acknowledgment's NUL in a separate write.
        ack += chunk.replace(b'\0', b'')
        if b'\n' in ack:
            if ack != b'ack\n':
                raise RuntimeError('unexpected perf control acknowledgment')
            return
    raise RuntimeError('perf control acknowledgment missing')


def verify_sample_window(text, window):
    clocks = [int(float(m[1])*1e9) for m in re.finditer(r'\s(\d+\.\d+):\s+\d+\s+cpu-clock:u:', text)]
    if not clocks or min(clocks) < window['enable_sent_ns']-1_000_000 or max(clocks) > window['disable_ack_ns']+1_000_000:
        raise ValueError('perf samples outside declared decode window')
    return dict(first_sample_ns=min(clocks), last_sample_ns=max(clocks), timed_samples=len(clocks),
                tolerance_ns=1_000_000)


def stream(url, prompt, on_first, on_final):
    payload = dict(prompt=prompt, n_predict=65, temperature=0, seed=42,
                   cache_prompt=False, stream=True, ignore_eos=True,
                   return_tokens=True, id_slot=0)
    request = urllib.request.Request(url + '/completion', json.dumps(payload).encode(),
                                     {'Content-Type': 'application/json'})
    start = time.monotonic_ns()
    first = None
    ids, parts = [], []
    final = None
    with urllib.request.urlopen(request, timeout=1200) as response:
        for raw in response:
            if not raw.startswith(b'data: '):
                continue
            event = raw[6:].strip()
            if event == b'[DONE]':
                continue
            item = json.loads(event)
            if item.get('stop'):
                final = item
                break
            if item.get('tokens') or item.get('content'):
                if first is None:
                    first = time.monotonic_ns()
                    on_first()
                tokens = item.get('tokens')
                if not isinstance(tokens, list) or any(not isinstance(t, int) for t in tokens):
                    raise ValueError('missing full streamed token IDs')
                ids.extend(tokens)
                parts.append(item.get('content', ''))
    end = time.monotonic_ns()
    on_final()
    if final is None or first is None:
        raise ValueError('incomplete stream')
    result = dict(request_start_ns=start, first_token_ns=first, request_end_ns=end,
                  wall_s=(end-start)/1e9, ttft_ms=(first-start)/1e6,
                  token_ids=ids, text=''.join(parts), timings=final.get('timings', {}),
                  tokens_predicted=final.get('tokens_predicted'), stop_type=final.get('stop_type'),
                  server_slot=final.get('id_slot'), error=final.get('error'))
    life.verify_cold(result, len(prompt))
    if result['error'] or result['server_slot'] != 0 or result['stop_type'] != 'limit' or result['tokens_predicted'] != 65 or len(ids) != 65:
        raise ValueError('incomplete 65-token diagnostic request')
    result['sha256'] = hashlib.sha256(result['text'].encode()).hexdigest()
    result['tokens_sha256'] = hashlib.sha256(json.dumps(ids, separators=(',', ':')).encode()).hexdigest()
    return result


def aggregate(rows):
    total = sum(r['total_ns'] for r in rows)
    sums = {name: sum(r['section_ns'][i] for r in rows) for i, name in enumerate(SECTIONS)}
    return dict(records=len(rows), worker_elapsed_ns=total, section_ns=sums,
                elapsed_fraction={name: value/total if total else 0 for name, value in sums.items()},
                packing_input_bytes=sum(r['packing_input_bytes'] for r in rows),
                staging_copy_bytes=sum(r['copy_bytes'] for r in rows),
                buffer_sizes=sorted({r['buffer_size'] for r in rows}))


def paired_branches(rows, boundary_ns=0):
    # Match adjacent GEMM executions on worker zero, not cached pointers across
    # tokens. Other workers are attached using the same per-worker execution index.
    workers = {}
    for ith in sorted({r['ith'] for r in rows}):
        workers[ith] = sorted((r for r in rows if r['ith'] == ith), key=lambda r: r['begin_ns'])
    primary = workers.get(0, [])
    if any(len(w) != len(primary) for w in workers.values()):
        raise ValueError('worker execution counts differ')
    pairs = []
    consumed = set()
    pattern = re.compile(r'^(.*)ffn_(gate|up)\.weight$')
    for i, (a, b) in enumerate(zip(primary, primary[1:])):
        if i in consumed or i+1 in consumed:
            continue
        aa, bb = pattern.match(a['weight']), pattern.match(b['weight'])
        if not aa or not bb or aa[1] != bb[1] or {aa[2], bb[2]} != {'gate', 'up'}:
            continue
        if any(a[k] != b[k] for k in ('input', 'activation', 'm', 'k', 'n', 'nth')):
            continue
        bound = []
        for ith, worker in workers.items():
            if i+1 >= len(worker):
                raise ValueError('worker execution count differs in FFN pair')
            x, y = worker[i:i+2]
            if any(x[k] != a[k] or y[k] != b[k] for k in ('weight', 'activation', 'input', 'm', 'n', 'k', 'nth')):
                raise ValueError('worker FFN execution identity differs')
            bound.append((x, y))
        if len(bound) != a['nth']:
            raise ValueError('missing FFN workers')
        consumed.update((i, i+1))
        if min(x['begin_ns'] for pair in bound for x in pair) < boundary_ns:
            continue
        pairs.append(dict(layer=aa[1].rstrip('.'), m=a['m'], k=a['k'], n=a['n'],
                          gate_up_worker_packing_ns=sum(x['section_ns'][0]+y['section_ns'][0] for x, y in bound),
                          smaller_branch_worker_packing_ns=min(sum(x['section_ns'][0] for x, _ in bound),
                                                              sum(y['section_ns'][0] for _, y in bound)),
                          smaller_branch_input_bytes=min(sum(x['packing_input_bytes'] for x, _ in bound),
                                                         sum(y['packing_input_bytes'] for _, y in bound))))
    total = sum(r['total_ns'] for r in rows if r['begin_ns'] >= boundary_ns)
    packing = sum(p['smaller_branch_worker_packing_ns'] for p in pairs)
    return dict(adjacent_same_input_pairs=len(pairs), pairs_by_layer=dict(Counter(p['layer'] for p in pairs)),
                smaller_branch_worker_packing_ns=packing,
                smaller_branch_input_bytes=sum(p['smaller_branch_input_bytes'] for p in pairs),
                worker_elapsed_fraction=packing/total if total else 0,
                implementation_priority_signal=bool(pairs and total and packing/total >= .03),
                caveat='Same input addresses/names/shapes in adjacent executions identify a reuse opportunity, not prove a safe lifetime. '
                       'Worker elapsed overlaps and instrumentation overhead prevent a wall-time savings estimate. No pointer cache is implemented.')


def audit_summary(rows, request):
    if not rows:
        raise ValueError('missing audit records')
    for r in rows:
        if not request['request_start_ns'] <= r['begin_ns'] <= request['request_end_ns']:
            raise ValueError('audit clock does not align with request CLOCK_MONOTONIC')
        if len(r['section_ns']) != 5 or any(not math.isfinite(v) or v < 0 for v in [r['total_ns'], *r['section_ns']]) or sum(r['section_ns']) > r['total_ns']*1.001:
            raise ValueError('invalid timing sections')
        if r['nth'] != 4 or r['ith'] not in range(4) or r['buffer_size'] != 0:
            raise ValueError('unexpected workers or route-3 staging')
    # Requests have prompt lengths divisible by 32. Use stream first-token
    # boundary as well as M=1; discard the crossing decode execution.
    decode = [r for r in rows if r['m'] == 1 and r['begin_ns'] >= request['first_token_ns']]
    prefill = [r for r in rows if r['m'] > 1]
    if not decode or not prefill:
        raise ValueError('missing distinct prefill/decode records')
    # Align from the full single-row execution sequence before trimming the
    # stream boundary, which can fall inside a multi-worker graph execution.
    single_rows = [r for r in rows if r['m'] == 1]
    return dict(prefill=aggregate(prefill), decode=aggregate(decode),
                decode_weights={w: aggregate([r for r in decode if r['weight'] == w]) for w in sorted({r['weight'] for r in decode})},
                ffn_pairs=paired_branches(single_rows, request['first_token_ns']))


class Run(ime.Run):
    verified_modified_kernel = True
    compile_timeout = 480
    kernel_relative = 'ggml/src/ggml-cpu/spacemit/ime.cpp'
    tag = 'decode-audit'
    harness = 'test-k1-gemm-routing.cpp'
    binary = 'test-decode-audit'
    title = 'K1 sustained decode packing audit'

    def generate(self, text):
        return patcher.generate(text)

    def baseline(self):
        routing = json.loads((self.root/'routing-provenance.json').read_text())
        lib = Path(routing['link'][routing['link'].index('-o')+1])
        if fast.digest(lib) != routing['candidate_library_sha256'] or routing['original_object_sha256'] != self.provenance['original_object_sha256']:
            raise ValueError('route-3 baseline library or original objects changed')
        self.base_env = dict(os.environ, **routing['runtime'], SPINE_K1_GEMM_ROUTE='3', SPINE_GEMM_AUDIT='0')
        self.env.update(SPINE_K1_GEMM_ROUTE='3')
        self.provenance['baseline_route3_library'] = dict(path=str(lib), sha256=fast.digest(lib))
        self.provenance['settings'].update(output_tokens=65, contexts=[256, 2048], mtp=False)
        fast.write_json(self.root/'provenance.json', self.provenance)

    def native_gate(self):
        self.phase('104 native cases per baseline / audit-off / audit-on arm')
        hashes = {}
        for label, env in [('baseline', self.base_env), ('audit-off', dict(self.env, SPINE_GEMM_AUDIT='0')), ('audit-on', dict(self.env, SPINE_GEMM_AUDIT='1'))]:
            output = self.root/(label+'.native.data')
            self.command([self.root/self.binary, '--dump', output], label+'.native.log', 180, env)
            if 'PASS: 104 production graph cases;' not in (self.root/(label+'.native.log')).read_text():
                raise ValueError('native gate incomplete')
            hashes[label] = fast.digest(output)
        if len(set(hashes.values())) != 1:
            raise ValueError('native dump identity failed')
        self.summary['stages']['native'] = dict(cases_per_arm=104, output_sha256=hashes, bitwise_equal=True)
        self.save()

    def request(self, model, tokens, audited):
        label = f'{model}-{tokens}-'+('audit' if audited else 'profile')
        self.phase(label)
        env = dict(self.env, SPINE_GEMM_AUDIT='1') if audited else self.base_env
        url = 'http://127.0.0.1:18089'
        argv = [str(self.server), '-m', self.expected['models'][model]['path'], '-t', '4', '-c', '4096',
                '--parallel', '1', '-b', '32', '-ub', '32', '-fa', 'on', '-ngl', '0',
                '-ctk', 'f16', '-ctv', 'f16', '--host', '127.0.0.1', '--port', '18089']
        server = perf = None
        fds = []
        window = {}
        data = self.root/(label+'.perf.data')
        with (self.root/(label+'.server.log')).open('w') as log, (self.root/(label+'.perf.log')).open('w') as plog:
            try:
                server = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
                life.wait_healthy(server, url, 600)
                prompt = life.make_prompt(url, tokens)
                if not audited:
                    ctl_r, ctl_w = os.pipe(); ack_r, ack_w = os.pipe()
                    fds = [ctl_r, ctl_w, ack_r, ack_w]
                    perf = subprocess.Popen(['perf', 'record', '-e', 'cpu-clock:u', '-F', '199', '--call-graph', 'fp',
                                             '-D', '-1', '--control', f'fd:{ctl_r},{ack_w}', '-p', str(server.pid), '-o', str(data)],
                                            stdout=plog, stderr=subprocess.STDOUT, pass_fds=(ctl_r, ack_w), start_new_session=True)
                def first():
                    window['enable_sent_ns'] = time.monotonic_ns()
                    if perf:
                        perf_control(perf, ctl_w, ack_r, 'enable')
                    window['enable_ack_ns'] = time.monotonic_ns()
                def final():
                    window['disable_sent_ns'] = time.monotonic_ns()
                    if perf:
                        perf_control(perf, ctl_w, ack_r, 'disable')
                    window['disable_ack_ns'] = time.monotonic_ns()
                result = stream(url, prompt, first, final)
                result['prompt_ids'] = prompt
                result['profile_window'] = window
                result['server_command'] = argv
                fast.write_json(self.root/(label+'.request.json'), result)
                profile.stop(perf, signal.SIGINT)
                if perf and perf.returncode not in (0, -signal.SIGINT):
                    raise ValueError('perf failed')
            finally:
                profile.stop(perf, signal.SIGINT); profile.stop(server)
                for fd in fds:
                    os.close(fd)
        text = (self.root/(label+'.server.log')).read_text()
        if 'K1_GEMM_ROUTE mode=3' not in text or 'SPINE_FA_WIDE_TILE: RVV tiled attention enabled' not in text:
            raise ValueError('route / wide-attention activation missing')
        records = [json.loads(line.split('K1_DECODE_AUDIT ', 1)[1]) for line in text.splitlines() if line.startswith('K1_DECODE_AUDIT ')]
        if audited:
            (self.root/(label+'.counters.jsonl')).write_text(''.join(json.dumps(r)+'\n' for r in records))
            attribution = audit_summary(records, result)
            fast.write_json(self.root/(label+'.attribution.json'), attribution)
        else:
            if records:
                raise ValueError('uninstrumented baseline contains audit')
            stacks = self.root/(label+'.stacks.txt')
            profile.checked(['perf', 'script', '-i', data, '-F', 'comm,pid,tid,time,event,ip,sym,dso,period'], stacks)
            attribution = profile.summarize(stacks.read_text())
            attribution['sample_window_verification'] = verify_sample_window(stacks.read_text(), window)
            profile.checked(['perf', 'report', '-i', data, '--stdio', '--no-children', '--call-graph', 'none', '--percent-limit', '.1'], self.root/(label+'.self.txt'))
            lost = self.root/(label+'.lost.txt')
            profile.checked(['perf', 'script', '-i', data, '--show-lost-events'], lost)
            if 'PERF_RECORD_LOST' in lost.read_text():
                raise ValueError('lost profile samples')
            attribution['window'] = window
            attribution['scope'] = 'Enabled after receiving first streamed token, disabled after final event; excludes prefill. Pipelining may omit part of the first decode execution.'
            fast.write_json(self.root/(label+'.profile.json'), attribution)
        return result, attribution

    def run(self):
        try:
            self.summary['limitations'] = 'Diagnostic only. Separate profiler and counter runs; instrumentation perturbs timings. CPU shares and overlapping GEMM worker elapsed are not removable wall-time fractions. Capped tokens do not measure useful answers.'
            self.prepare(); self.baseline(); self.native_gate()
            for model in ('2B', '4B'):
                for tokens in (256, 2048):
                    baseline, cpu = self.request(model, tokens, False)
                    audited, counters = self.request(model, tokens, True)
                    if any(baseline[k] != audited[k] for k in ('prompt_ids', 'token_ids', 'text')):
                        raise ValueError('model output or prompt identity failed')
                    self.summary['stages'][f'{model}-{tokens}'] = dict(exact_identity=True, cpu_profile=cpu, counters=counters,
                        baseline_timings=baseline['timings'], diagnostic_timings=audited['timings'])
                    self.save()
            self.summary.update(status='diagnostic complete', reason='Select the next implementation using decode CPU and branch packing evidence; no new optimization qualified by this diagnostic.')
            self.save(); self.phase('diagnostic complete')
        except BaseException as exc:
            self.summary.update(status='failed', reason=f'{type(exc).__name__}: {exc}')
            self.save(); self.phase('failed'); raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    def interrupted(signum, frame):
        raise TimeoutError('board budget expired')
    signal.signal(signal.SIGTERM, interrupted)
    Run(args.root.resolve()).run()
