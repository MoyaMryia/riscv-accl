#!/usr/bin/env python3
"""Staged K1 validation; MTP diagnostics are independent of direct routing gates."""
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time

HERE = Path(__file__).resolve().parent
def module(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + '.py'))
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result); return result
fast = module('k1-fast-test')
bench = module('bench-lifecycle')
quality = module('document_quality_suite')


def first_difference(a, b):
    return next((i for i, (x, y) in enumerate(zip(a, b)) if x != y),
                min(len(a), len(b)) if len(a) != len(b) else None)


def complete_answer(result, prompt_tokens):
    usage = result.get('usage', {})
    return (result.get('finish_reason') == 'stop' and bool(result.get('answer', '').strip())
            and not result.get('reasoning_text') and '<think>' not in result.get('answer', '')
            and result.get('server_slot') == 0 and usage.get('prompt_tokens') == prompt_tokens
            and usage.get('completion_tokens', 0) > 0
            and usage.get('prompt_tokens_details', {}).get('cached_tokens') == 0)


def routing_gate(rows, labels, tokens=8192):
    requests = fast.check_model_records(rows, labels, tokens, output_tokens=64)
    arms = {mode: [r['results'][0] for r in requests if f'-q{mode}-' in r['label']] for mode in (0, 3)}
    for values in arms.values():
        if len(values) != 2 or any(r['timings'].get('predicted_n') != 64 for r in values):
            raise ValueError('incomplete sustained decode timing')
    comparisons = {phase: fast.gate([r['timings'][phase + '_ms'] for r in arms[0]],
                                    [r['timings'][phase + '_ms'] for r in arms[3]])
                   for phase in ('prompt', 'predicted')}
    return {'status': 'pass', 'requests': 4, 'input_tokens': tokens, 'output_tokens': 64,
            'outputs_equal': True, 'uncached_verified': True, 'comparisons': comparisons,
            'eligible': all(g['advance'] and not g['clear_regression'] for g in comparisons.values())}


def resource_snapshot():
    mem = {line.split(':')[0]: int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines()
           if len(line.split()) >= 2 and line.split()[1].isdigit()}
    vm = {line.split()[0]: int(line.split()[1]) for line in Path('/proc/vmstat').read_text().splitlines()}
    return {'mem_available_kib': mem['MemAvailable'], 'swap_used_kib': mem['SwapTotal'] - mem['SwapFree'],
            'pswpin_pages': vm.get('pswpin', 0), 'pswpout_pages': vm.get('pswpout', 0)}


def pilot_cases(readme):
    cases = quality.evidence_cases(readme)
    cases[0]['evidence'] += '\nReceipt A: 17 units.'
    cases[1]['evidence'] = '[S2] Synthetic trace: job orion uses route maple.'
    cases[2]['evidence'] = '[S3] Synthetic receipt B: 23 units.'
    cases[3]['evidence'] = '[S4] Synthetic trace: route maple reaches cabinet cedar.'
    cases[4]['evidence'] = '[S5] Synthetic receipt C: 38 units.'
    cases[5]['evidence'] = '[S6] Synthetic trace: cabinet cedar has color cobalt.'
    trace = dict(cases[5], case_id='trace', question='Follow job orion through its route and cabinet. '
                 'What color is its cabinet? Cite [S2], [S4], and [S6]. Answer briefly.',
                 fact_patterns=[r'\bcobalt\b'], required_facts=['cobalt'], citations=['S2', 'S4', 'S6'])
    total = dict(cases[4], case_id='aggregation', question='Add the units in receipts A, B, and C. '
                 'Give the total and cite [S1], [S3], and [S5]. Answer briefly.',
                 fact_patterns=[r'\b78\b'], required_facts=['78'], citations=['S1', 'S3', 'S5'])
    route = dict(cases[0], citations=['S1'])
    return cases, [route, trace, total]


class Run:
    def __init__(self, root):
        self.root = root
        self.expected = json.loads((root / 'expected-provenance.json').read_text())
        self.routing = json.loads((root / 'routing-provenance.json').read_text())
        self.routing_run = json.loads((root / 'routing-run.json').read_text())
        self.started = time.monotonic()
        self.summary = {'status': 'running', 'stages': {}, 'protocol': {
            'routing_order': [0, 3, 3, 0], 'routing_tokens': 8192, 'routing_output': 64,
            'quality_document_budget': 4096, 'quality_cases': ['routes', 'trace', 'aggregation'],
            'quality_output_cap': 512, 'mtp_output': 512, 'teacher_forced_k': [1, 3],
            'feasibility_input_tokens': 32768, 'feasibility_output_tokens': 64,
            'feasibility_context': 33792, 'feasibility_budget_s': 18000,
            'minimum_available_kib': 2 * 1024 * 1024, 'overall_budget_s': 43200,
            '64k': 'not scheduled; conditional on a measured need and resources'},
            'limitations': 'Engineering pilot, not a RULER/LongBench score. Fixed-length timing and naturally stopped quality are separate. A single 32k request is feasibility only. No default is changed.'}

    def phase(self, name):
        (self.root / 'phase').write_text(name + '\n'); print(name, flush=True)

    def save(self):
        self.summary['elapsed_s'] = time.monotonic() - self.started
        fast.write_json(self.root / 'summary.json', self.summary)
        (self.root / 'summary.md').write_text('# K1 staged validation\n\nStatus: ' + self.summary['status']
            + '\n\n' + self.summary['limitations'] + '\n\n```json\n' + json.dumps(self.summary, indent=2) + '\n```\n')

    def stage(self, name, action):
        self.phase(name)
        try:
            result = action()
        except (Exception,) as error:
            if self.interrupted: raise
            result = {'status': 'failed', 'reason': f'{type(error).__name__}: {error}'}
        self.summary['stages'][name] = result; self.save(); return result

    def env(self, mode=0, rs=None):
        env = {k: v for k, v in os.environ.items() if not k.startswith(('SPINE_', 'SPACEMIT_'))}
        env.update(LD_LIBRARY_PATH=str(self.overlay) + ':' + self.expected['runtime']['LD_LIBRARY_PATH'],
                   SPINE_FA_WIDE_TILE='1', SPINE_FA_K1_LAYOUT='0', SPINE_K1_GEMM_ROUTE=str(mode))
        if rs is not None: env['SPINE_SPEC_RS'] = str(rs)
        return env

    def command(self, argv, name, budget, env=None):
        fast.command(argv, self.root / (name + '.driver.log'), budget, env or self.env())

    def prepare(self):
        self.phase('verify provenance and compile native probes')
        artifacts = self.expected['artifacts_sha256']
        self.server = next(Path(p) for p in artifacts if p.endswith('/llama-server'))
        self.source = self.server.parents[2]
        if subprocess.check_output(['git', '-C', self.source, 'rev-parse', '--short=7', 'HEAD'], text=True).strip() != 'a990751':
            raise ValueError('source revision changed')
        changed = set(subprocess.check_output(['git', '-C', self.source, 'diff', 'HEAD', '--name-only'], text=True).splitlines())
        if changed != set(self.expected['source_sha256']): raise ValueError('unexpected source changes')
        hashes = {}
        for relative, digest in self.expected['source_sha256'].items():
            path = self.source / relative; hashes[str(path)] = fast.digest(path)
            if hashes[str(path)] != digest: raise ValueError('source hash changed: ' + relative)
        for path, digest in artifacts.items():
            if any(part in path for part in ('/build/', '/.toolchain/', '/spert/')):
                hashes[path] = fast.digest(path)
                if hashes[path] != digest: raise ValueError('runtime hash changed: ' + path)
        for info in self.expected['models'].values():
            hashes[info['path']] = fast.digest(info['path'])
            if hashes[info['path']] != info['sha256']: raise ValueError('model hash changed')
        original_overlay = Path(self.routing_run['remote_root']) / 'lib'
        library = original_overlay / 'libggml-cpu.so.0.16.0'
        if fast.digest(library) != self.routing['candidate_library_sha256']: raise ValueError('routing library changed')
        # Copy the verified binary into this job, preserving the prior experiment.
        import shutil
        self.overlay = self.root / 'lib'; self.overlay.mkdir()
        shutil.copyfile(library, self.overlay / library.name)
        for name in ('libggml-cpu.so', 'libggml-cpu.so.0'): (self.overlay / name).symlink_to(library.name)
        compiler = self.routing['compile'][0]
        for name, source in (('state-probe', 'test-k1-recurrent-state.cpp'), ('perfect-draft', 'test-k1-perfect-draft.cpp')):
            self.command([compiler, '-O3', '-std=c++17', '-march=rv64gcv_zfh_zvfh_zicbop_zihintpause_zba',
                '-mabi=lp64d', '-I' + str(self.source / 'include'), '-I' + str(self.source / 'ggml/include'),
                HERE / source, '-L' + str(self.server.parent), '-L' + str(self.overlay),
                '-lllama', '-lggml', '-lggml-base', '-lggml-cpu', '-pthread', '-o', self.root / name], name + '-build', 180)
        code = {p.name: fast.digest(p) for p in HERE.iterdir() if p.suffix in ('.py', '.cpp', '.sh', '.txt')}
        runtime = {k: v for k, v in self.env().items() if k.startswith('SPINE_') or k == 'LD_LIBRARY_PATH'}
        fast.write_json(self.root / 'provenance.json', {'verified_sha256': hashes,
            'candidate_library_sha256': fast.digest(self.overlay / library.name), 'code_sha256': code,
            'probe_sha256': {n: fast.digest(self.root / n) for n in ('state-probe', 'perfect-draft')},
            'source_revision': 'a990751', 'runtime': runtime, 'settings': {
                'threads': 4, 'batch': 32, 'ubatch': 32, 'weights': 'Q4_0', 'kv': 'F16', 'context_shift': False}})
        self.route = module('k1-gemm-routing')

    def state_probe(self, model):
        name = model + '-state'
        self.command([self.root / 'state-probe', self.expected['models'][model]['path']], name, 1200)
        rows = [json.loads(line) for line in (self.root / (name + '.driver.log')).read_text().splitlines() if line.startswith('{"case"')]
        if not rows or not all(any(r['rs'] == rs and r['case'].startswith(kind) for r in rows)
            for rs in (0, 3) for kind in ('same-shape', 'full-fresh', 'full-dirty', 'partial-seeded', 'partial-dirty', 'whole-batch-rollback')):
            raise ValueError('missing state cases')
        fast.write_json(self.root / (name + '.json'), rows)
        counts = {s: sum(r['status'] == s for r in rows) for s in ('pass', 'mismatch', 'unsupported')}
        return {'status': 'mismatch' if counts['mismatch'] else 'incomplete coverage' if counts['unsupported'] else 'pass',
                'counts': counts, 'records': len(rows), 'sequence_isolation': 'deferred',
                'partial_fresh': 'seeded with matching attention prefix; partial snapshots omit attention KV'}

    def perfect(self, model):
        name = model + '-forced'; trajectory = self.root / (name + '-direct.jsonl')
        shared = ['--model', self.expected['models'][model]['path'], '--prompt-file', self.root / 'code-prompt.txt',
                  '--n-predict', 512, '--threads', 4, '--traj', trajectory]
        self.command([self.root / 'perfect-draft', 'direct', *shared], name + '-direct', 900)
        direct = [json.loads(line) for line in trajectory.read_text().splitlines()]
        if len(direct) != 512: raise ValueError('incomplete direct trajectory')
        results = {}
        for k in (1, 3):
            out = self.root / (name + f'-k{k}.jsonl')
            self.command([self.root / 'perfect-draft', 'verify', *shared, '--k', k, '--out', out], name + f'-k{k}', 900)
            rows = [json.loads(line) for line in out.read_text().splitlines()]
            if len(rows) != 512 or [r['i'] for r in rows] != list(range(512)):
                raise ValueError('incomplete forced replay')
            shifts = [abs(r['v_at_d' + str(i)] - r['d' + str(i)]) for r in rows for i in (1, 2)]
            if not all(math.isfinite(v) for v in shifts): raise ValueError('nonfinite forced logits')
            mismatches = [r for r in rows if not r['match']]
            results[str(k)] = {'positions': 512, 'first_flip': mismatches[0]['i'] if mismatches else None,
                               'flips': len(mismatches), 'max_top2_shift': max(shifts)}
        # Nine significant decimal digits round-trip FP32; allow serialization
        # decimal error only (not a backend numerical error budget).
        control_ok = results['1']['flips'] == 0 and results['1']['max_top2_shift'] == 0
        return {'status': 'pass' if control_ok else 'failed control', 'replays': results,
                'interpretation': 'Same forced token history; M>1 differences do not by themselves rule out a state bug.'}

    def lifecycle(self, model, label, tokens, outputs, route=0, mode='plain', rs=None, timeout=1800, ctx=12288, prompt=False):
        argv = [sys.executable, HERE / 'bench-lifecycle.py', '--server', self.server,
                '--model', self.expected['models'][model]['path'], '--label', label, '--mode', mode,
                '--contexts', tokens, '--n-predict', outputs, '--ignore-eos', '--verify-cold', '--capture-token-ids',
                '--gpu-layers', 0, '--ctx-size', ctx, '--no-context-shift', '--timeout', timeout,
                '--output', self.root / (label + '.jsonl'), '--log', self.root / (label + '.server.log')]
        if prompt: argv += ['--prompt-file', self.root / 'code-prompt.txt']
        self.command(argv, label, timeout + 120, self.env(route, rs))
        rows = [json.loads(line) for line in (self.root / (label + '.jsonl')).read_text().splitlines()]
        self.route.check_activation((self.root / (label + '.server.log')).read_text(), route, ('prefill', 'single'))
        fast.check_model_records(rows, [label], tokens, output_tokens=outputs)
        return rows

    def mtp(self, model):
        results = {}; records = {}
        for name, mode, rs in (('direct', 'plain', None), ('checkpoint', 'mtp', 0), ('rs', 'mtp', 1)):
            label = model + '-mtp512-' + name
            rows = self.lifecycle(model, label, 128, 512, mode=mode, rs=rs, timeout=1200, ctx=2048, prompt=True)
            records[name] = next(r['results'][0] for r in rows if r['kind'] == 'measurement')
        for name in ('checkpoint', 'rs'):
            a, b = records['direct'], records[name]
            results[name] = {'first_difference': first_difference(a['token_ids'], b['token_ids']),
                'tokens_equal': a['token_ids'] == b['token_ids'], 'text_equal': a['sha256'] == b['sha256'],
                'direct_decode_ms': a['timings']['predicted_ms'], 'mtp_decode_ms': b['timings']['predicted_ms']}
        return {'status': 'pass' if all(r['tokens_equal'] for r in results.values()) else 'mismatch',
                'results': results, 'output_tokens': 512, 'speed_claim': 'diagnostic only; identity gates deployment'}

    def long_routing(self, model):
        labels = []; rows = []
        for i, mode in enumerate((0, 3, 3, 0)):
            label = f'{model}-8192-q{mode}-pass{i+1}'; labels.append(label)
            self.phase('8k routing ' + label)
            rows.extend(self.lifecycle(model, label, 8192, 64, route=mode, timeout=2400))
        return routing_gate(rows, labels)

    def answers(self, model):
        chat = module('cached-document-chat')
        url = 'http://127.0.0.1:18085'; readme = (self.source / 'tools/server/README.md').read_text()
        blocks, cases = pilot_cases(readme); document = None; pairs = {}; counts = {}
        # Two fresh servers, all requests cold. Reverse case order in arm B.
        for mode in (0, 3):
            name = f'{model}-answers-q{mode}'
            argv = [str(self.server), '-m', self.expected['models'][model]['path'], '--alias', 'local',
                    '-t', '4', '-c', '6144', '--parallel', '1', '-b', '32', '-ub', '32', '-fa', 'on',
                    '-ctk', 'f16', '-ctv', 'f16', '-ngl', '0', '--no-context-shift', '--host', '127.0.0.1', '--port', '18085']
            with (self.root / (name + '.server.log')).open('w') as log:
                proc = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, env=self.env(mode))
                try:
                    bench.wait_healthy(proc, url, 120)
                    if document is None:
                        document, doc_tokens = quality.make_document(url, chat, blocks, readme, 4096, 120)
                        (self.root / (model + '-quality-document.txt')).write_text(document)
                        fast.write_json(self.root / (model + '-quality-cases.json'), {'blocks': blocks, 'cases': cases, 'document_tokens': doc_tokens})
                    for case in cases if mode == 0 else list(reversed(cases)):
                        self.phase(name + ' ' + case['case_id'])
                        payload = chat.request_body(chat.messages(document, case['question']), 'local', 0, 512)
                        payload.update(cache_prompt=False, stream_options={'include_usage': True}, verbose=True)
                        count = chat.count_prompt_tokens(url, payload, 120)
                        if count + 512 > 6144: raise ValueError('full document plus output does not fit')
                        key = case['case_id']
                        if key in counts and counts[key] != count: raise ValueError('quality input count changed')
                        counts[key] = count
                        result = chat.complete(url, payload, 1800, display=False)
                        result.update(case_id=key, mode=mode, prompt_tokens=count,
                            complete_cold=complete_answer(result, count), facts=quality.fact_check(case, result['answer']),
                            citations_ok=all('[' + c + ']' in result['answer'] for c in case['citations']),
                            document_sha256=hashlib.sha256(document.encode()).hexdigest(), request=payload)
                        pairs.setdefault(key, {})[str(mode)] = result
                        fast.write_json(self.root / (model + '-answers.json'), pairs)
                finally:
                    proc.terminate()
                    try: proc.wait(timeout=10)
                    except subprocess.TimeoutExpired: proc.kill(); proc.wait()
            self.route.check_activation((self.root / (name + '.server.log')).read_text(), mode, ('prefill', 'single'))
        comparisons = {}
        for case in cases:
            arms = pairs[case['case_id']]; a, b = arms['0'], arms['3']
            complete = a['complete_cold'] and b['complete_cold']
            a_facts, b_facts = a['facts']['required_fact_hits'], b['facts']['required_fact_hits']
            regress = any(x and not y for x, y in zip(a_facts, b_facts)) or (a['citations_ok'] and not b['citations_ok'])
            comparisons[case['case_id']] = {'complete_cold_pair': complete, 'text_identical': a['answer_sha256'] == b['answer_sha256'],
                'baseline_facts': a_facts, 'candidate_facts': b_facts, 'baseline_citations': a['citations_ok'],
                'candidate_citations': b['citations_ok'], 'regression': regress,
                'candidate_useful': all(b_facts) and b['citations_ok']}
        return {'status': 'pass' if all(r['complete_cold_pair'] and not r['regression'] and r['candidate_useful'] for r in comparisons.values()) else 'quality gate not cleared',
                'comparisons': comparisons, 'requests': 6, 'input': 'full ~4k fixture, all source blocks preserved',
                'timing_claim': 'none; one request per task and arm'}

    def feasibility(self):
        before = resource_snapshot()
        if before['mem_available_kib'] < 10 * 1024 * 1024 or before['swap_used_kib']:
            return {'status': 'skipped', 'reason': 'requires 10 GiB available and no swap before 32k allocation', 'resources_before': before}
        # Watch system headroom while the child owns its server process group.
        stop = threading.Event(); samples = []; low_memory = threading.Event()
        child = None
        label = '4B-32768-q3-feasibility'
        argv = [sys.executable, HERE / 'bench-lifecycle.py', '--server', self.server,
                '--model', self.expected['models']['4B']['path'], '--label', label,
                '--contexts', 32768, '--n-predict', 64, '--ignore-eos', '--verify-cold', '--capture-token-ids',
                '--gpu-layers', 0, '--ctx-size', 33792, '--no-context-shift', '--timeout', 18000,
                '--output', self.root / (label + '.jsonl'), '--log', self.root / (label + '.server.log')]
        def watch():
            while not stop.wait(2):
                sample = dict(resource_snapshot(), elapsed_s=time.monotonic() - started); samples.append(sample)
                if sample['mem_available_kib'] < 2 * 1024 * 1024 or sample['swap_used_kib']:
                    low_memory.set()
                    if child is not None and child.poll() is None:
                        try: os.killpg(child.pid, signal.SIGTERM)
                        except ProcessLookupError: pass
                    return
        started = time.monotonic()
        with (self.root / (label + '.driver.log')).open('w') as log:
            child = subprocess.Popen(list(map(str, argv)), stdout=log, stderr=subprocess.STDOUT,
                                     env=self.env(3), start_new_session=True)
            monitor = threading.Thread(target=watch); monitor.start()
            try:
                code = child.wait(timeout=18120)
                if code: raise RuntimeError('32k child failed' + (' after low-memory abort' if low_memory.is_set() else f' with exit {code}'))
            finally:
                stop.set(); monitor.join()
                # Also kill descendants if their parent exited under the memory abort.
                try: os.killpg(child.pid, signal.SIGTERM)
                except ProcessLookupError: pass
                try: child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL); child.wait()
                try: os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError: pass
                fast.write_json(self.root / '32k-resources.json', {'before': before, 'after': resource_snapshot(), 'samples': samples, 'low_memory_abort': low_memory.is_set()})
        rows = [json.loads(line) for line in (self.root / (label + '.jsonl')).read_text().splitlines()]
        self.route.check_activation((self.root / (label + '.server.log')).read_text(), 3, ('prefill', 'single'))
        requests = fast.check_model_records(rows, [label], 32768, output_tokens=64)
        return {'status': 'pass', 'claim': 'one bounded 4B/32k fixed-length feasibility request; no speedup or complete-answer claim',
                'request': requests[0], 'resources_before': before, 'resources_after': resource_snapshot(),
                'minimum_available_kib': min((r['mem_available_kib'] for r in samples), default=before['mem_available_kib'])}

    def run(self):
        self.interrupted = False
        def interrupted(signum, frame):
            self.interrupted = True; raise TimeoutError('overall board budget expired')
        signal.signal(signal.SIGTERM, interrupted)
        try:
            self.prepare(); self.save()
            for model in ('2B', '4B'):
                self.stage(model + '-state', lambda m=model: self.state_probe(m))
                self.stage(model + '-forced', lambda m=model: self.perfect(m))
                self.stage(model + '-mtp512', lambda m=model: self.mtp(m))
            for model in ('2B', '4B'):
                self.stage(model + '-8k-routing', lambda m=model: self.long_routing(m))
                self.stage(model + '-answers', lambda m=model: self.answers(m))
            eligible = all(self.summary['stages'][m + '-8k-routing'].get('eligible', False)
                           and self.summary['stages'][m + '-answers']['status'] == 'pass' for m in ('2B', '4B'))
            if eligible: self.stage('4B-32k-feasibility', self.feasibility)
            else: self.summary['stages']['4B-32k-feasibility'] = {'status': 'skipped', 'reason': 'combined routing/quality prerequisite not cleared'}
            self.summary.update(status='completed', combined_routing_eligible=eligible,
                mtp_identity_cleared=all(self.summary['stages'][m + '-mtp512']['status'] == 'pass'
                    and self.summary['stages'][m + '-state']['status'] == 'pass'
                    and self.summary['stages'][m + '-forced']['status'] == 'pass' for m in ('2B', '4B')))
            self.save(); self.phase('completed; inspect per-stage outcomes')
        except BaseException as error:
            self.summary.update(status='failed', reason=f'{type(error).__name__}: {error}'); self.save(); self.phase('failed'); raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('root', type=Path)
    Run(parser.parse_args().root.resolve()).run()
