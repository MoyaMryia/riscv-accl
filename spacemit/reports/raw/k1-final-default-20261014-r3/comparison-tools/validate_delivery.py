"""核验最终构建的算子数值、默认状态路径和迁移启动。"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import time
import traceback
from effective import verify as effective


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def require(value, reason):
    if not value:
        raise ValueError(reason)


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


class Run:
    def __init__(self, args):
        self.a = args
        self.root = args.output.resolve()
        self.root.mkdir(parents=True)
        self.started = time.monotonic()
        self.summary = dict(status='running', stages={})
        self.pkg = module('package', args.package / 'package.py')
        self.start = module('delivery_start', args.package / 'start.py')
        self.life = module('delivery_life', args.package / 'tests/lifecycle.py')
        self.config = json.loads((args.package / 'default-policy.json').read_text())['config']
        self.env = self.start.environment(args.build / 'bin', args.spert, args.tcm)
        self.models = {n: args.models / item['filename'] for n, item in self.pkg.manifest()['models'].items()}

    def phase(self, name):
        print(name, flush=True)
        (self.root / 'phase').write_text(name + '\n')
        self.summary['elapsed_s'] = time.monotonic() - self.started
        save(self.root / 'summary.json', self.summary)

    def command(self, argv, label, env=None, timeout=1800):
        selected = self.env if env is None else env
        argv = list(map(str, argv))
        save(self.root / (label + '.command.json'), dict(argv=argv, environment={k: v for k, v in selected.items()
            if k.startswith(('SPINE_', 'SPACEMIT_', 'LLAMA_')) or k == 'LD_LIBRARY_PATH'}))
        with (self.root / (label + '.log')).open('w') as log:
            proc = subprocess.run(argv, env=selected, stdout=log, stderr=subprocess.STDOUT,
                timeout=timeout, pass_fds=(9,))
        (self.root / (label + '.exit-status')).write_text(str(proc.returncode) + '\n')
        proc.check_returncode()
        return (self.root / (label + '.log')).read_text()

    def identity(self):
        self.phase('identity')
        require(os.environ.get('TMUX') and os.environ.get('K1_PACKAGE_LOCK_FD') == '9', 'use with-lock.sh in tmux')
        os.fstat(9)
        require(subprocess.run(['pgrep', '-x', 'llama-server'], stdout=subprocess.DEVNULL).returncode == 1,
            'another server is active')
        with socket.socket() as sock:
            require(sock.connect_ex(('127.0.0.1', self.a.port)) != 0, 'port is occupied')
        source = self.pkg.verify(self.a.source)
        for path in self.models.values():
            self.start.verify(self.a.build, path, self.a.spert, self.a.tcm)
        reference_receipt = json.loads((self.a.reference / 'build-receipt.json').read_text())
        self.reference = reference_receipt['binaries']
        self.check_reference()
        validation = self.a.reference.parent / 'validation'
        receipts = json.loads((validation / 'receipts.json').read_text())
        require(sha(validation / 'summary.json') == receipts['summary.json'], 'RC1 validation receipt differs')
        prior = json.loads((validation / 'summary.json').read_text())
        require(prior['stages']['native']['status'] == 'pass', 'RC1 numeric reference does not pass')
        self.native_hashes = prior['stages']['native']['hashes']
        save(self.root / 'identity.json', dict(source=source, policy=self.config,
            models={n: dict(path=str(p), sha256=sha(p)) for n, p in self.models.items()},
            final_build=json.loads((self.a.build / 'build-receipt.json').read_text()),
            reference_build=reference_receipt, reference_validation_sha256=receipts['summary.json'],
            tool_sha256=sha(Path(__file__)), effective_tool_sha256=sha(Path(__file__).with_name('effective.py')),
            hardware=dict(uname=subprocess.check_output(['uname', '-a'], text=True),
                cpuinfo=Path('/proc/cpuinfo').read_text(), meminfo=Path('/proc/meminfo').read_text(), uid=os.getuid())))
        self.summary['stages']['identity'] = 'pass'

    def check_reference(self):
        actual = {p.name: sha(p) for p in sorted((self.a.reference / 'bin').iterdir()) if p.is_file()}
        require(actual == self.reference, 'RC1 binaries differ')

    def native(self):
        self.phase('native')
        result = {}
        for name, arguments, count, reference in (
            ('route', [], 104, 'route-3'), ('attention', [], 95, 'reference-attention'),
            ('ssm', ['3'], 432, 'unified-ssm-c1'), ('gdn', [], 158, 'reference-gdn')):
            dump = self.root / (name + '.data')
            log = self.command([self.a.build / ('bin/test-' + name), *arguments, '--dump', dump], 'native-' + name)
            require('PASS: ' + str(count) in log, 'numeric case count differs: ' + name)
            value = sha(dump)
            require(value == self.native_hashes[reference], 'numeric dump differs: ' + name)
            result[name] = dict(cases=count, sha256=value)
        self.summary['stages']['native'] = dict(status='pass', results=result)

    def state(self):
        self.phase('default state')
        reference_env = self.start.environment(self.a.reference / 'bin', self.a.spert, self.a.tcm)
        reference_env.update(SPINE_K1_GEMM_ROUTE='3', SPINE_FA_WIDE_TILE='1', SPINE_FA_K1_LAYOUT='0',
            SPINE_K1_FA_GQA='0', SPINE_K1_SSM_CONV='0', SPINE_GDN_PREFILL='0', SPINE_K1_GDN_REVISION='0')
        result = {}
        for model, path in self.models.items():
            dumps = []
            for kind, arm, env in (('reference', 0, reference_env), ('default', -1, self.env)):
                label = 'state-' + model + '-' + kind
                self.phase(label)
                dump = self.root / (label + '.data')
                log = self.command([self.a.build / 'bin/test-default-state', path, arm, dump, 'short'], label, env)
                rows = [json.loads(line) for line in log.splitlines() if line.startswith('{')]
                require(len(rows) == 16 and all(r['bitwise_equal'] and r['max_abs'] == 0 for r in rows),
                    'default state values differ')
                require([(r['rs'], r['reset'], r['prefix']) for r in rows] ==
                    [(rs, reset, prefix) for rs in (0, 3) for reset in (0, 1) for prefix in (32, 33, 64, 96)],
                    'default state coverage differs')
                require('PASS: 16 full-vocabulary records' in log, 'default state count differs')
                dumps.append(sha(dump))
                result[label] = dict(sha256=dumps[-1], rows=rows)
            require(dumps[0] == dumps[1], 'default state differs from RC1 at the selected parameters')
        save(self.root / 'state.json', result)
        self.summary['stages']['state'] = dict(status='pass', records=64, context=4096,
            config=self.config, max_prefix=96, long_state_acceptance='pending')

    def relocate(self):
        self.phase('relocation')
        build = self.root / 'relocated-build'
        build.mkdir()
        shutil.copytree(self.a.build / 'bin', build / 'bin', symlinks=True)
        shutil.copy2(self.a.build / 'build-receipt.json', build / 'build-receipt.json')
        package = self.root / 'relocated-package'
        shutil.copytree(self.a.package, package, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        env = self.start.environment(build / 'bin', self.a.spert, self.a.tcm)
        for binary in sorted((build / 'bin').iterdir()):
            if binary.is_symlink() or not binary.is_file():
                continue
            log = self.command(['ldd', binary], 'ldd-' + binary.name, env, timeout=60)
            require('not found' not in log, 'missing shared library')
            for name in re.findall(r'=> (/\S+)', log):
                path = Path(name).resolve()
                allowed = (build.resolve(), self.a.spert.resolve(), self.a.tcm.resolve(), Path('/usr'), Path('/lib'))
                require(any(path == parent or parent in path.parents for parent in allowed),
                    'library resolves outside the package and declared runtimes: ' + name)
        for model, path in self.models.items():
            label = 'relocated-' + model
            self.phase(label)
            argv = list(map(str, [sys.executable, package / 'start.py', '--build', build, '--model', path,
                '--spert', self.a.spert, '--tcm', self.a.tcm, '--port', self.a.port,
                '--receipt', self.root / (label + '.launch.json')]))
            polluted = dict(os.environ, SPINE_K1_FA_GQA='invalid', SPINE_K1_SSM_CONV='invalid',
                SPINE_K1_TRACE='1', SPACEMIT_CORE_ARCH='invalid-inherited-value', LLAMA_ARG_THREADS='8')
            save(self.root / (label + '.command.json'), dict(argv=argv, pollution={k: v for k, v in polluted.items()
                if k.startswith(('SPINE_', 'SPACEMIT_', 'LLAMA_'))}))
            with (self.root / (label + '.server.log')).open('w') as log:
                proc = subprocess.Popen(argv, env=polluted, stdout=log, stderr=subprocess.STDOUT, pass_fds=(9,))
                try:
                    url = 'http://127.0.0.1:' + str(self.a.port)
                    self.life.wait_healthy(proc, url, 240)
                    actual = effective((self.root / (label + '.server.log')).read_text(), self.config)
                    save(self.root / (label + '.effective.json'), actual)
                    response = self.life.complete(url, self.life.make_prompt(url, 32), 8, 240, 0, True, False, True, True, True)
                    self.life.verify_cold(response, 32)
                    require(response['tokens_predicted'] == 8, 'relocated request does not complete')
                    save(self.root / (label + '.result.json'), response)
                finally:
                    proc.terminate()
                    try:
                        proc.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait()
                    (self.root / (label + '.server-exit-status')).write_text(str(proc.returncode) + '\n')
            launch = json.loads((self.root / (label + '.launch.json')).read_text())
            require(set(launch['environment']) == {'LD_LIBRARY_PATH'}, 'launcher retains optimization variables')
            require(launch['argv'] == [str(build / 'bin/llama-server'), '-m', str(path.resolve()), '--alias', 'local',
                '--port', str(self.a.port)], 'launcher adds performance parameters')
        self.summary['stages']['relocation'] = dict(status='pass', models=list(self.models),
            launch='compiled defaults', optimization_environment='absent')

    def run(self):
        try:
            self.identity()
            self.native()
            self.state()
            self.relocate()
            self.check_reference()
            self.pkg.verify(self.a.source)
            for path in self.models.values():
                self.start.verify(self.a.build, path, self.a.spert, self.a.tcm)
            self.summary['status'] = 'verified-limited'
        except BaseException as exc:
            self.summary.update(status='failed', error=f'{type(exc).__name__}: {exc}')
            traceback.print_exc()
            raise
        finally:
            self.phase(self.summary['status'])
            save(self.root / 'receipts.json', {str(p.relative_to(self.root)): sha(p)
                for p in sorted(self.root.rglob('*')) if p.is_file() and 'relocated-build' not in p.parts
                and '__pycache__' not in p.parts and p != self.root / 'receipts.json'})


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'package', 'build', 'reference', 'models', 'output', 'spert', 'tcm'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--port', type=int, default=18433)
    a = p.parse_args()
    for name in ('source', 'package', 'build', 'reference', 'models', 'output', 'spert', 'tcm'):
        setattr(a, name, getattr(a, name).resolve())
    Run(a).run()
