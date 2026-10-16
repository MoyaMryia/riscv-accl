"""用最终二进制执行 16k 和 32k 容量扩展对照。"""
import argparse
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import threading
import time
import traceback
import urllib.request
import experiment as common

GIB_KIB = 1024 * 1024
PLAN = [('2B', 16384, 0, 'final'), ('2B', 16384, 0, 'baseline'),
    ('4B', 16384, 0, 'baseline'), ('4B', 16384, 0, 'final'),
    ('2B', 32768, 0, 'baseline'), ('2B', 32768, 0, 'final'),
    ('4B', 32768, 0, 'final'), ('4B', 32768, 0, 'baseline'),
    ('4B', 16384, 1, 'final'), ('4B', 16384, 1, 'baseline'),
    ('2B', 16384, 1, 'baseline'), ('2B', 16384, 1, 'final')]


def save(path, data):
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(data, indent=2) + '\n')
    temp.replace(path)


def mem_available():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):
            return int(line.split()[1])
    raise RuntimeError('MemAvailable is absent')


def config_for(length):
    return dict(context=20480 if length == 16384 else 36864, timeout_s=8*3600 if length == 16384 else 24*3600)


def effective(text, context):
    lines = re.findall(r'^K1_EFFECTIVE_DEFAULTS (.+)$', text, re.MULTILINE)
    common.require(len(lines) == 1, 'effective defaults record differs')
    actual = dict(item.split('=', 1) for item in lines[0].split())
    expected = dict(threads='4', batch_threads='4', batch='32', ubatch='32', context=str(context),
        slots='1', flash='1', gpu='0', key='f16', value='f16', mask='3')
    common.require(actual == expected, 'capacity extension changes optimization defaults')
    return actual


class Run:
    def __init__(self, args):
        self.a = args
        self.root = args.output
        self.root.mkdir(parents=True, exist_ok=args.resume)
        self.started = time.monotonic()
        self.summary = dict(status='running', completed=[], failed=[], expected_requests=len(PLAN),
            default_context=12288, scope='same final binary with explicit context capacity extension')
        self.url = 'http://127.0.0.1:' + str(args.port)
        self.models = {n: args.models / item[0] for n, item in common.MODELS.items()}
        self.builds = dict(final=args.original / 'final-r3/build', baseline=args.original / 'baseline-load-build')
        self.prompts = {}

    def phase(self, label):
        print(label, flush=True)
        (self.root / 'phase').write_text(label + '\n')
        self.summary['elapsed_s'] = time.monotonic() - self.started
        save(self.root / 'summary.json', self.summary)

    def identity(self):
        self.phase('identity')
        common.require(os.environ.get('TMUX') and os.environ.get('K1_PACKAGE_LOCK_FD') == '9', 'use common lock in tmux')
        os.fstat(9)
        common.require(subprocess.run(['pgrep', '-x', 'llama-server'], stdout=subprocess.DEVNULL).returncode == 1,
            'another server is active')
        with socket.socket() as sock:
            common.require(sock.connect_ex(('127.0.0.1', self.a.port)) != 0, 'port occupied')
        builds = {}
        for kind, build in self.builds.items():
            record = json.loads((build / 'build-receipt.json').read_text())
            actual = {p.name: common.sha(p) for p in sorted((build / 'bin').iterdir()) if p.is_file()}
            common.require(actual == record['binaries'], 'binary identity differs: ' + kind)
            builds[kind] = dict(path=str(build), binaries=actual, receipt_sha256=common.sha(build / 'build-receipt.json'))
            for name, value in record['dependencies'].items():
                common.require(common.sha(name) == value, 'runtime differs')
        common.require(builds['final']['binaries']['llama-server'] ==
            'f254f174919c0a97ef34366f116705f6d22574cab4c2bfc39928c0d315b5bfbd', 'final server differs')
        models = {}
        for model, path in self.models.items():
            common.require(common.sha(path) == common.MODELS[model][1], 'model identity differs')
            models[model] = dict(path=str(path), sha256=common.MODELS[model][1],
                stat=[path.stat().st_size, path.stat().st_mtime_ns])
        self.pins = dict(builds=builds, models=models,
            tools={p.name: common.sha(p) for p in sorted(Path(__file__).parent.iterdir()) if p.is_file()},
            protocol_sha256=common.sha(Path(__file__).parent.parent / 'PROTOCOL.md'), plan=PLAN)
        pinfile = self.root / 'identity.json'
        if pinfile.exists():
            prior = json.loads(pinfile.read_text())
            common.require(prior['inputs'] == json.loads(json.dumps(self.pins)), 'resume identity differs')
        else:
            save(pinfile, dict(inputs=self.pins, hardware=dict(uname=subprocess.check_output(['uname','-a'], text=True),
                meminfo=Path('/proc/meminfo').read_text(), cpuinfo=Path('/proc/cpuinfo').read_text(), uid=os.getuid(),
                frequency={str(p):p.read_text() for p in Path('/sys/devices/system/cpu').glob('cpu*/cpufreq/scaling_cur_freq')},
                governor={str(p):p.read_text() for p in Path('/sys/devices/system/cpu').glob('cpu*/cpufreq/scaling_governor')})))
        prompts = self.root / 'prompts.json'
        if prompts.exists():
            self.prompts = json.loads(prompts.read_text())

    def request(self, model, length, repeat, kind):
        label = f'{model}-p{length}-r{repeat}-{kind}'
        self.phase(label)
        parameters = config_for(length)
        job = dict(model=model, input_tokens=length, output_tokens=65, repeat=repeat, kind=kind,
            context=parameters['context'], timeout_s=parameters['timeout_s'], identity=common.digest(self.pins))
        common.require(subprocess.run(['pgrep','-x','llama-server'], stdout=subprocess.DEVNULL).returncode == 1,
            'another server is active')
        for n, path in self.models.items():
            common.require([path.stat().st_size,path.stat().st_mtime_ns] == self.pins['models'][n]['stat'], 'model file changes')
        folder = self.root / label
        if folder.exists() and (folder / 'receipts.json').exists():
            for name, value in json.loads((folder / 'receipts.json').read_text()).items():
                common.require(common.sha(folder / name) == value, 'existing request receipt differs')
            common.require(json.loads((folder / 'job.json').read_text()) == job, 'existing request differs')
            result = json.loads((folder / 'result.json').read_text())
            self.completed(label, result)
            return
        if folder.exists():
            folder.rename(self.root / (label + '.interrupted-' + str(time.time_ns())))
        folder.mkdir()
        save(folder / 'job.json', job)
        result = dict(job, status='failed')
        proc = None
        stopped = threading.Event()
        samples = []
        control = dict(deadline=None, violation=None)
        monitor = None
        try:
            common.require(mem_available() >= 8*GIB_KIB, 'less than 8 GiB available before launch')
            common.require(subprocess.run(['pgrep','-x','llama-server'], stdout=subprocess.DEVNULL).returncode == 1,
                'another server is active')
            for n, path in self.models.items():
                common.require([path.stat().st_size,path.stat().st_mtime_ns] == self.pins['models'][n]['stat'], 'model file changes')
            build = self.builds[kind]
            env = common.environment(build / 'bin', self.a.spert, self.a.tcm)
            argv = [str(build / 'bin/llama-server'), '-m', str(self.models[model]), '--alias', 'local',
                '--host', '127.0.0.1', '--port', str(self.a.port), '-c', str(parameters['context'])]
            if kind == 'baseline':
                argv += ['-t','4','-tb','4','--parallel','1','-b','32','-ub','32','-fa','on','-ctk','f16','-ctv','f16',
                    '-ngl','0','--no-context-shift']
            save(folder / 'launch.json', dict(argv=argv, environment={'LD_LIBRARY_PATH':env['LD_LIBRARY_PATH']},
                optimization_environment='absent', capacity_override=parameters['context']))
            with (folder / 'server.log').open('w') as log:
                proc = subprocess.Popen(argv, env=env, stdout=log, stderr=subprocess.STDOUT, pass_fds=(9,))
                loaded_at = time.monotonic()
                def sample():
                    while not stopped.wait(1):
                        if proc.poll() is not None:
                            break
                        rss = common.life.vmrss_kib(proc.pid)
                        available = mem_available()
                        row = dict(elapsed_s=time.monotonic()-loaded_at, rss_kib=rss, mem_available_kib=available)
                        samples.append(row)
                        reason = None
                        if available < GIB_KIB:
                            reason = 'available memory below 1 GiB'
                        elif rss is not None and rss > 12*GIB_KIB:
                            reason = 'server RSS above 12 GiB'
                        elif control['deadline'] and time.monotonic() > control['deadline']:
                            reason = 'request wall-time limit'
                        if reason:
                            control['violation'] = reason
                            proc.terminate()
                            break
                        if len(samples) % 30 == 0:
                            save(self.root / 'progress.json', dict(label=label, pid=proc.pid, **row))
                monitor = threading.Thread(target=sample, daemon=True)
                monitor.start()
                common.life.wait_healthy(proc, self.url, 300)
                with urllib.request.urlopen(self.url + '/props', timeout=30) as response:
                    props = json.load(response)
                save(folder / 'properties.json', props)
                common.require(props['default_generation_settings']['n_ctx'] == parameters['context'] and props['total_slots'] == 1,
                    'actual capacity or slots differ')
                common.require(props['default_generation_settings']['params']['speculative.types'] == 'none', 'draft decode enabled')
                if kind == 'final':
                    save(folder / 'effective-defaults.json', effective((folder / 'server.log').read_text(), parameters['context']))
                if model not in self.prompts:
                    tokens = common.life.make_prompt(self.url, 32768)
                    ids = common.life.post_json(self.url + '/tokenize', dict(content=' a', add_special=False))['tokens']
                    common.require(len(tokens) == 32768 and len(ids) == 1, 'prompt or forced token differs')
                    self.prompts[model] = dict(tokens=tokens, forced_token=ids[0])
                    save(self.root / 'prompts.json', self.prompts)
                common.require(common.life.make_prompt(self.url, 32) == self.prompts[model]['tokens'][:32], 'tokenizer differs')
                prompt = self.prompts[model]['tokens'][:length]
                forced = self.prompts[model]['forced_token']
                payload = dict(prompt=prompt, n_predict=65, temperature=0, seed=42, cache_prompt=False, stream=True,
                    ignore_eos=True, return_tokens=True, id_slot=0, logit_bias=[[forced,1000.0]])
                save(folder / 'request.json', payload)
                control['deadline'] = time.monotonic() + parameters['timeout_s']
                measured = common.stream(self.url, payload, parameters['timeout_s'] + 60)
                common.life.verify_cold(measured, length)
                common.require(measured['tokens_predicted'] == measured['timings']['predicted_n'] == 65, 'output count differs')
                common.require(measured['token_ids'] == [forced]*65, 'decode history differs')
                common.require(measured['stop_type'] == 'limit' and measured['error'] is None, 'request does not complete')
                result.update(measured, prompt_sha256=common.digest(prompt), status='pass')
        except Exception as exc:
            result.update(error=f'{type(exc).__name__}: {exc}', monitor_violation=control['violation'])
            (folder / 'traceback.txt').write_text(traceback.format_exc())
        finally:
            stopped.set()
            if monitor:
                monitor.join(timeout=3)
            if proc:
                proc.terminate()
                try:
                    proc.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    proc.kill(); proc.wait()
                (folder / 'server-exit-status').write_text(str(proc.returncode)+'\n')
            save(folder / 'memory-samples.json', samples)
            rss = [s['rss_kib'] for s in samples if s['rss_kib'] is not None]
            result['rss_kib'] = common.life.stats(rss)
            result['min_available_kib'] = min((s['mem_available_kib'] for s in samples), default=None)
            save(folder / 'result.json', result)
            save(folder / 'receipts.json', {p.name:common.sha(p) for p in sorted(folder.iterdir()) if p.is_file()})
            self.completed(label, result)

    def completed(self, label, result):
        self.summary['completed'].append(label)
        if result['status'] != 'pass':
            self.summary['failed'].append(label)
        self.summary['elapsed_s'] = time.monotonic()-self.started
        save(self.root / 'summary.json', self.summary)
        print(json.dumps(dict(label=label, status=result['status'], error=result.get('error'))), flush=True)

    def run(self):
        try:
            self.identity()
            for job in PLAN:
                self.request(*job)
            self.phase('final identity')
            for model,path in self.models.items():
                common.require(common.sha(path) == self.pins['models'][model]['sha256'], 'model identity changes')
            for kind,build in self.builds.items():
                common.require({p.name:common.sha(p) for p in sorted((build/'bin').iterdir()) if p.is_file()} ==
                    self.pins['builds'][kind]['binaries'], 'binary identity changes')
                record = json.loads((build/'build-receipt.json').read_text())
                common.require(common.sha(build/'build-receipt.json') == self.pins['builds'][kind]['receipt_sha256'], 'build receipt changes')
                common.require(all(common.sha(n) == h for n,h in record['dependencies'].items()), 'runtime changes')
            common.require({p.name:common.sha(p) for p in sorted(Path(__file__).parent.iterdir()) if p.is_file()} ==
                self.pins['tools'], 'controller changes')
            self.summary['status'] = 'pass' if not self.summary['failed'] else 'complete-with-failures'
        except BaseException as exc:
            self.summary.update(status='failed', error=f'{type(exc).__name__}: {exc}')
            traceback.print_exc()
        finally:
            self.phase(self.summary['status'])
            save(self.root / 'receipts.json', {str(p.relative_to(self.root)):common.sha(p)
                for p in sorted(self.root.rglob('*')) if p.is_file() and p != self.root/'receipts.json'})
        return 0 if self.summary['status']=='pass' else 1


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('original','output','models','spert','tcm'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--port',type=int,default=18443)
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    for name in ('original','output','models','spert','tcm'):
        setattr(args,name,getattr(args,name).resolve())
    raise SystemExit(Run(args).run())
