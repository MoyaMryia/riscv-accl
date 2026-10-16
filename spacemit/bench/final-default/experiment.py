"""执行最终默认参数搜索与真实起始版本的匹配请求。"""
import argparse
import contextlib
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
import traceback
import urllib.request

from selection import choose, key

HERE = Path(__file__).resolve().parent
MODELS = {
    '2B': ('Qwen3.5-2B-MTP-Q4_0-embQ4_0-dv64k.gguf', '56f0ddd90dfa0e2456af6cb4718ece419678d21a75d65e27353319b5e431a2fa'),
    '4B': ('Qwen3.5-4B-MTP-Q4_0-embQ4_0-dv64k.gguf', '0adf6cce5df53921606033c39a13fae2054543b78af0e7ff98860e86f078ac0f'),
}
SHAPES = [('2B', 512), ('4B', 512), ('2B', 2048), ('4B', 2048)]


def module(name):
    path = HERE / (name + '.py')
    if not path.exists():
        path = HERE.parents[1] / 'release-candidate/tests' / (name + '.py')
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


life = module('lifecycle')
chat = module('chat')
quality = module('quality')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def environment(binary_dir, spert, tcm, config=None):
    env = {k: v for k, v in os.environ.items()
        if not k.startswith(('SPINE_', 'SPACEMIT_', 'GGML_', 'LLAMA_', 'OMP_', 'GOMP_', 'KMP_'))
        and k not in ('LD_LIBRARY_PATH', 'LD_PRELOAD', 'LD_AUDIT')}
    env['LD_LIBRARY_PATH'] = ':'.join(str(p.resolve()) for p in (binary_dir, tcm, spert / 'lib'))
    if config is not None:
        mask = config['mask']
        env.update(SPINE_FA_WIDE_TILE='1', SPINE_FA_K1_LAYOUT='0', SPINE_K1_GEMM_ROUTE='3',
            SPINE_K1_SSM_CONV='3' if mask & 2 else '0',
            SPINE_GDN_PREFILL='1' if mask & 4 else '0',
            SPINE_K1_GDN_REVISION='1' if mask & 4 else '0',
            SPINE_K1_FA_GQA='1' if mask & 1 else '0', SPINE_K1_FA_DECODE='0',
            SPINE_K1_CONV_SILU='0', SPINE_IME_SCALAR_SCHEDULE='0', SPINE_K1_TRACE='0')
    return env


def stream(url, payload, timeout):
    request = urllib.request.Request(url + '/completion', json.dumps(payload).encode(),
        {'Content-Type': 'application/json'})
    started = time.monotonic()
    first = None
    tokens = []
    text = []
    final = None
    with urllib.request.urlopen(request, timeout=timeout) as response:
        for raw in response:
            if not raw.startswith(b'data: '):
                continue
            body = raw[6:].strip()
            if body == b'[DONE]':
                continue
            item = json.loads(body)
            if item.get('error'):
                raise RuntimeError('completion error: ' + str(item['error']))
            if item.get('stop'):
                final = item
                break
            if item.get('tokens') or item.get('content'):
                if first is None:
                    first = time.monotonic()
                tokens.extend(item.get('tokens') or [])
                text.append(item.get('content', ''))
    finished = time.monotonic()
    require(final is not None and first is not None, 'incomplete response')
    timings = final.get('timings', {})
    require(all(math.isfinite(timings.get(n, float('nan'))) and timings[n] > 0
        for n in ('prompt_ms', 'predicted_ms')), 'nonfinite or empty timing')
    return dict(wall_s=finished - started, ttft_ms=(first - started) * 1000,
        decode_ms=timings['predicted_ms'], timings=timings, token_ids=tokens,
        text=''.join(text), text_sha256=hashlib.sha256(''.join(text).encode()).hexdigest(),
        tokens_predicted=final.get('tokens_predicted'), stop_type=final.get('stop_type'),
        error=final.get('error'))


class Run:
    def __init__(self, args):
        self.args = args
        self.root = args.output.resolve()
        self.root.mkdir(parents=True, exist_ok=args.resume)
        self.started = time.monotonic()
        self.summary = dict(status='running', stage=args.stage, completed=[])
        self.models = {n: args.models / item[0] for n, item in MODELS.items()}
        self.url = 'http://127.0.0.1:' + str(args.port)
        self.prompts = {}

    def phase(self, label):
        print(label, flush=True)
        (self.root / 'phase').write_text(label + '\n')
        self.summary['elapsed_s'] = time.monotonic() - self.started
        save(self.root / 'summary.json', self.summary)

    def identity(self):
        require(os.environ.get('TMUX') and os.environ.get('K1_PACKAGE_LOCK_FD') == '9', 'use with-lock.sh in tmux')
        os.fstat(9)
        require(subprocess.run(['pgrep', '-x', 'llama-server'], stdout=subprocess.DEVNULL).returncode == 1,
            'another server is active')
        with socket.socket() as sock:
            require(sock.connect_ex(('127.0.0.1', self.args.port)) != 0, 'port occupied')
        self.phase('identity')
        models = {}
        for n, p in self.models.items():
            require(sha(p) == MODELS[n][1], 'model hash differs: ' + n)
            models[n] = dict(path=str(p), sha256=MODELS[n][1], stat=[p.stat().st_size, p.stat().st_mtime_ns])
        builds = {}
        for name in ('baseline', 'candidate', 'final'):
            path = getattr(self.args, name)
            if path is None:
                continue
            builds[name] = {str(p.resolve()): sha(p) for p in sorted((path / 'bin').iterdir()) if p.is_file()}
        self.inputs = dict(models=models, builds=builds,
            code={p.name: sha(p) for p in sorted(HERE.iterdir()) if p.is_file()},
            dependencies={str(p.resolve()): sha(p) for folder in (self.args.spert / 'lib', self.args.tcm)
                for p in sorted(folder.glob('*.so*')) if p.is_file()})
        pin = self.root / 'identity.json'
        if pin.exists():
            old = json.loads(pin.read_text())
            require(old['inputs'] == self.inputs, 'resume inputs differ')
        else:
            save(pin, dict(inputs=self.inputs, hardware=dict(
                uname=subprocess.check_output(['uname', '-a'], text=True),
                cpuinfo=Path('/proc/cpuinfo').read_text(), meminfo=Path('/proc/meminfo').read_text(),
                uid=os.getuid(), session=os.environ['TMUX'],
                frequency={str(p): p.read_text() for p in Path('/sys/devices/system/cpu').glob('cpu*/cpufreq/scaling_cur_freq')},
                governor={str(p): p.read_text() for p in Path('/sys/devices/system/cpu').glob('cpu*/cpufreq/scaling_governor')},
                thermal={str(p): p.read_text() for p in Path('/sys/class/thermal').glob('thermal_zone*/temp')})))
        prompts = self.root / 'prompts.json'
        if prompts.exists():
            self.prompts = json.loads(prompts.read_text())

    @contextlib.contextmanager
    def server(self, model, kind, config, folder):
        build = getattr(self.args, kind).resolve()
        env = environment(build / 'bin', self.args.spert, self.args.tcm,
            config if kind == 'candidate' else None)
        argv = [build / 'bin/llama-server', '-m', self.models[model], '--alias', 'local',
            '--host', '127.0.0.1', '--port', str(self.args.port)]
        if kind != 'final':
            argv += ['-t', str(config['threads']), '-tb', str(config['threads']),
                '-c', '12288', '--parallel', '1', '-b', str(config['ubatch']), '-ub', str(config['ubatch']),
                '-fa', 'on', '-ctk', 'f16', '-ctv', 'f16', '-ngl', '0', '--no-context-shift']
        argv = list(map(str, argv))
        save(folder / 'launch.json', dict(argv=argv, environment={k: v for k, v in env.items()
            if k.startswith('SPINE_') or k == 'LD_LIBRARY_PATH'}, kind=kind, config=config))
        with (folder / 'server.log').open('w') as log:
            proc = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, env=env)
            try:
                life.wait_healthy(proc, self.url, 240)
                with urllib.request.urlopen(self.url + '/props', timeout=30) as response:
                    props = json.load(response)
                save(folder / 'properties.json', props)
                require(props['default_generation_settings']['n_ctx'] == 12288, 'effective context differs')
                require(props['total_slots'] == 1, 'effective slot count differs')
                if kind == 'final':
                    from effective import verify
                    actual = verify((folder / 'server.log').read_text(), config)
                    save(folder / 'effective-defaults.json', actual)
                yield proc
            finally:
                proc.terminate()
                try:
                    proc.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
                (folder / 'server-exit-status').write_text(str(proc.returncode) + '\n')

    def request(self, label, model, length, kind, config, count=65, natural=False):
        self.phase(label)
        folder = self.root / label
        expected = dict(model=model, input_tokens=length, kind=kind, config=config,
            output_tokens=count, natural=natural, context=12288, identity=digest(self.inputs))
        for name, path in self.models.items():
            stat = path.stat()
            require([stat.st_size, stat.st_mtime_ns] == self.inputs['models'][name]['stat'], 'model file changed')
        if folder.exists():
            if not (folder / 'receipts.json').exists():
                folder.rename(self.root / (label + '.interrupted-' + str(time.time_ns())))
        if folder.exists():
            receipt = json.loads((folder / 'receipts.json').read_text())
            for n, h in receipt.items():
                require(sha(folder / n) == h, 'resume evidence differs')
            require(json.loads((folder / 'job.json').read_text()) == expected, 'resume job differs')
            result = json.loads((folder / 'result.json').read_text())
            if label not in self.summary['completed']:
                self.summary['completed'].append(label)
            return result
        folder.mkdir()
        save(folder / 'job.json', expected)
        result = dict(expected, status='failed')
        try:
            with self.server(model, kind, config, folder) as proc:
                if model not in self.prompts:
                    tokens = life.make_prompt(self.url, 8192)
                    ids = life.post_json(self.url + '/tokenize', {'content': ' a', 'add_special': False})['tokens']
                    require(len(ids) == 1 and isinstance(ids[0], int), 'forced token is not singular')
                    self.prompts[model] = dict(tokens=tokens, forced_token=ids[0])
                    save(self.root / 'prompts.json', self.prompts)
                else:
                    require(life.make_prompt(self.url, 32) == self.prompts[model]['tokens'][:32], 'tokenizer differs')
                prompt = self.prompts[model]['tokens'][:length]
                samples = []
                stop = threading.Event()
                def sample():
                    while not stop.wait(.2):
                        try:
                            tasks = Path('/proc') / str(proc.pid) / 'task'
                            samples.append(dict(at=time.monotonic(), rss_kib=life.vmrss_kib(proc.pid),
                                threads={p.name: (p / 'stat').read_text() for p in tasks.iterdir()}))
                        except OSError:
                            pass
                thread = threading.Thread(target=sample)
                thread.start()
                try:
                    if natural:
                        payload = json.loads((HERE / (model + '-answer.json')).read_text())['request']
                        save(folder / 'request.json', payload)
                        answer = chat.complete(self.url, payload, 2400, display=False)
                        check = quality.check_code('unicode_runs', answer['answer'])
                        save(folder / 'answer.json', answer)
                        (folder / 'answer.md').write_text(answer['answer'] + '\n')
                        require(answer.get('finish_reason') == 'stop', 'answer has no natural stop')
                        require(answer['usage']['prompt_tokens_details']['cached_tokens'] == 0, 'answer is cached')
                        result.update(answer_sha256=hashlib.sha256(answer['answer'].encode()).hexdigest(),
                            quality=check, output_tokens=answer['usage']['completion_tokens'],
                            reasoning=answer.get('reasoning_text'), timings=answer['timings'])
                    else:
                        forced = self.prompts[model]['forced_token']
                        payload = dict(prompt=prompt, n_predict=count, temperature=0, seed=42,
                            cache_prompt=False, stream=True, ignore_eos=True, return_tokens=True,
                            id_slot=0, logit_bias=[[forced, 1000.0]])
                        save(folder / 'request.json', payload)
                        measured = stream(self.url, payload, 6000 if length >= 8192 else 1800)
                        life.verify_cold(measured, length)
                        require(measured['tokens_predicted'] == count and measured['timings']['predicted_n'] == count,
                            'output count differs')
                        require(measured['token_ids'] == [forced] * count, 'forced output differs')
                        result.update(measured, prompt_sha256=digest(prompt))
                finally:
                    stop.set()
                    thread.join()
                    save(folder / 'threads.json', samples)
                result['rss_kib'] = life.stats([r['rss_kib'] for r in samples if r['rss_kib'] is not None])
                result['status'] = 'pass'
        except Exception as exc:
            result['error'] = f'{type(exc).__name__}: {exc}'
            (folder / 'traceback.txt').write_text(traceback.format_exc())
        save(folder / 'result.json', result)
        save(folder / 'receipts.json', {p.name: sha(p) for p in sorted(folder.iterdir()) if p.is_file()})
        self.summary['completed'].append(label)
        return result

    def masks(self, parameters, cycle):
        configs = [dict(mask=m, **parameters) for m in range(8)]
        rows = []
        for round_id in (0, 1):
            shapes = SHAPES if round_id == 0 else list(reversed(SHAPES))
            for model, length in shapes:
                index = SHAPES.index((model, length))
                order = configs[index:] + configs[:index]
                if round_id:
                    order = list(reversed(order))
                for config in order:
                    label = f'masks-c{cycle}-r{round_id}-{model}-p{length}-{key(config)}'
                    rows.append(self.request(label, model, length, 'candidate', config))
        decision = choose(rows, configs, configs[0])
        save(self.root / f'masks-cycle-{cycle}.json', decision)
        return decision['selected']

    def parameters(self, selected, cycle):
        configs = [dict(mask=selected['mask'], threads=t, ubatch=u)
            for t in (4, 2) for u in (32, 16, 64, 128)]
        rows = []
        for model, length in SHAPES:
            order = configs if model == '2B' else [configs[0], *reversed(configs[1:])]
            for config in order:
                label = f'params-c{cycle}-{model}-p{length}-{key(config)}'
                rows.append(self.request(label, model, length, 'candidate', config))
        decision = choose(rows, configs, configs[0])
        save(self.root / f'parameters-cycle-{cycle}.json', decision)
        return decision['selected']

    def search(self):
        base = dict(mask=0, threads=4, ubatch=32)
        for model in MODELS:
            for kind in ('baseline', 'candidate'):
                result = self.request(f'preflight-{model}-{kind}', model, 512, kind, base, count=8)
                require(result['status'] == 'pass', 'preflight failed')
        parameters = dict(threads=4, ubatch=32)
        selected = None
        converged = False
        for cycle in range(2):
            mask_choice = self.masks(parameters, cycle)
            selected = self.parameters(mask_choice, cycle)
            new_parameters = {n: selected[n] for n in ('threads', 'ubatch')}
            if new_parameters == parameters:
                converged = True
                break
            parameters = new_parameters
        control = dict(mask=selected['mask'], threads=4, ubatch=32)
        if selected != control:
            rows = []
            for model, length in SHAPES:
                for i, config in enumerate((control, selected, selected, control)):
                    rows.append(self.request(f'confirm-{model}-p{length}-{i}-{key(config)}',
                        model, length, 'candidate', config))
            decision = choose(rows, [control, selected], control)
            save(self.root / 'confirmation.json', decision)
            selected = decision['selected']
        base = dict(mask=0, threads=4, ubatch=32)
        checks = {}
        for attempt in range(2):
            checks = {}
            for model in MODELS:
                a = self.request(f'selected-answer-{model}-control', model, 162, 'candidate', base, natural=True)
                b = self.request(f'selected-answer-{model}-{key(selected)}', model, 162, 'candidate', selected, natural=True)
                require(a['status'] == b['status'] == 'pass', 'selected answer request failed')
                valid = b['quality']['pass'] and b['quality']['checks'] == 106 and a['answer_sha256'] == b['answer_sha256']
                if not valid:
                    fallback = dict(mask=selected['mask'], threads=4, ubatch=32)
                    save(self.root / f'quality-rejection-{attempt}.json', dict(model=model, rejected=selected,
                        fallback=fallback, control=a, candidate=b))
                    require(selected != fallback and attempt == 0, 'selected quality gate failed')
                    selected = fallback
                    break
                checks[model] = dict(control=a['answer_sha256'], selected=b['answer_sha256'], checks=106)
            if len(checks) == 2:
                break
        require(len(checks) == 2, 'selected quality coverage is incomplete')
        save(self.root / 'selected-default.json', dict(version='k1-final-20261013-r1',
            config=selected, objective='balanced tested configurations',
            context=12288, cache_type_k='f16', cache_type_v='f16', gpu_layers=0,
            flash_attention=True, parallel=1, source='combined-r1', quality=checks,
            search_converged=converged))
        self.summary['search_converged'] = converged
        self.summary['selected'] = selected

    def compare(self):
        selected = json.loads(self.args.policy.read_text())['config']
        baseline = dict(mask=0, threads=4, ubatch=32)
        for model in MODELS:
            results = {}
            for kind in ('baseline', 'candidate', 'final'):
                config = baseline if kind != 'final' else selected
                result = self.request(f'answer-{model}-{kind}', model, 162, kind, config, natural=True)
                require(result['status'] == 'pass', 'natural answer request failed')
                results[kind] = result
            final = results['final']
            require(final['quality']['pass'] and final['quality']['checks'] == 106, 'final code check failed')
            require(not final.get('reasoning'), 'final answer includes reasoning')
            require(final['answer_sha256'] == results['candidate']['answer_sha256'], 'final answer differs from verified control')
        for model, length in SHAPES:
            for index in range(6):
                kind = ('baseline', 'final')[((index // 2) + index % 2) % 2]
                config = baseline if kind == 'baseline' else selected
                result = self.request(f'compare-{model}-p{length}-{index}-{kind}', model, length, kind, config)
                require(result['status'] == 'pass', 'matched comparison failed')
        for model in MODELS:
            for index, kind in enumerate(('baseline', 'final') if model == '2B' else ('final', 'baseline')):
                config = baseline if kind == 'baseline' else selected
                result = self.request(f'long-{model}-p8192-{index}-{kind}', model, 8192, kind, config)
                require(result['status'] == 'pass', 'long comparison failed')
        self.summary['comparison'] = 'pass'

    def run(self):
        try:
            self.identity()
            if self.args.stage == 'search':
                self.search()
            else:
                self.compare()
            for name, files in self.inputs['builds'].items():
                require(all(sha(p) == h for p, h in files.items()), 'binary changed: ' + name)
            for n, p in self.models.items():
                require(sha(p) == MODELS[n][1], 'model changed: ' + n)
            require(all(sha(p) == h for p, h in self.inputs['dependencies'].items()), 'runtime changed')
            require(self.inputs['code'] == {p.name: sha(p) for p in sorted(HERE.iterdir()) if p.is_file()}, 'tool changed')
            self.summary['status'] = 'pass'
        except BaseException as exc:
            self.summary.update(status='failed', error=f'{type(exc).__name__}: {exc}')
            traceback.print_exc()
            raise
        finally:
            self.phase(self.summary['status'])
            save(self.root / 'receipts.json', {str(p.relative_to(self.root)): sha(p)
                for p in sorted(self.root.rglob('*')) if p.is_file() and p != self.root / 'receipts.json'})


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage', choices=('search', 'compare'), required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--final', type=Path)
    p.add_argument('--policy', type=Path)
    p.add_argument('--models', type=Path, required=True)
    p.add_argument('--spert', type=Path, required=True)
    p.add_argument('--tcm', type=Path, required=True)
    p.add_argument('--port', type=int, default=18423)
    p.add_argument('--resume', action='store_true')
    Run(p.parse_args()).run()
