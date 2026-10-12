#!/usr/bin/env python3
"""Build isolated K1 libraries and run the first experiment gates."""
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


ime = module('board_ime', BENCH/'k1-ime-test.py')
ssm = module('board_ssm', BENCH/'k1-ssm-conv.py')
prepare = module('board_prepare', HERE/'prepare.py')
fast = ime.fast


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


class Run:
    def __init__(self, root):
        self.root = root.resolve()
        self.arms = sys.argv[2:] or ['A1', 'B1', 'C', 'D']
        if any(arm not in ('A1', 'B1', 'C', 'D') for arm in self.arms):
            raise ValueError('unknown candidate')
        self.expected = json.loads((root/'expected-provenance.json').read_text())
        self.server = next(Path(p) for p in self.expected['artifacts_sha256'] if p.endswith('/llama-server'))
        self.source = self.server.parents[2]
        self.build = self.source/'build'
        self.baseline = {}
        self.commands = []
        self.started = time.monotonic()
        self.summary = {'status': 'running', 'candidates': {}, 'models': 'pending',
                        'scope': 'K1 correctness and operator screen. Model performance remains unverified.'}
        self.tool = Path.home()/'Projects/llm-bench/.toolchain/gcc14/usr/bin/g++-14'

    def save(self):
        self.summary['elapsed_s'] = time.monotonic()-self.started
        fast.write_json(self.root/'summary.json', self.summary)

    def phase(self, name):
        (self.root/'phase').write_text(name+'\n')
        print(name, flush=True)
        self.save()

    def env(self, arm):
        env = dict(os.environ)
        for key in list(env):
            if key.startswith('SPINE_'):
                del env[key]
        env.update(SPINE_FA_WIDE_TILE='1', SPINE_FA_K1_LAYOUT='0', SPINE_K1_GEMM_ROUTE='3',
                   SPINE_K1_TRACE='1', SPINE_GDN_PREFILL='0', SPINE_K1_SSM_CONV='0',
                   SPINE_K1_FA_DECODE='0', SPINE_K1_FA_GQA='0', SPINE_K1_CONV_SILU='0',
                   LD_LIBRARY_PATH=self.expected['runtime']['LD_LIBRARY_PATH'])
        if arm != 'original':
            env['LD_LIBRARY_PATH'] = str(self.root/arm/'lib')+':'+env['LD_LIBRARY_PATH']
        return env

    def command(self, argv, label, arm='control', timeout=600, cwd=None, updates=None):
        env = self.env(arm)
        env.update(updates or {})
        argv = list(map(str, argv))
        self.commands.append({'argv': argv, 'log': label+'.log', 'arm': arm, 'cwd': str(cwd or self.root),
                              'environment': {k: v for k, v in env.items() if k.startswith('SPINE_') or k == 'LD_LIBRARY_PATH'}})
        fast.write_json(self.root/'commands.json', self.commands)
        with (self.root/(label+'.log')).open('w') as stream:
            subprocess.run(argv, cwd=cwd or self.root, env=env, stdout=stream,
                           stderr=subprocess.STDOUT, check=True, timeout=timeout)
        return (self.root/(label+'.log')).read_text(errors='replace')

    def verify(self):
        self.phase('verify baseline and payload')
        rev = subprocess.check_output(['git', '-C', self.source, 'rev-parse', 'HEAD'], text=True).strip()
        if rev != 'a990751d55a4c54acf2bb77d44282c2093652359':
            raise ValueError('baseline revision differs')
        changed = set(subprocess.check_output(['git', '-C', self.source, 'diff', 'HEAD', '--name-only'], text=True).splitlines())
        if changed != set(self.expected['source_sha256']):
            raise ValueError('baseline source changes differ')
        for rel, value in dict(prepare.PINS, **self.expected['source_sha256']).items():
            self.baseline[str(self.source/rel)] = value
        for path, value in self.expected['artifacts_sha256'].items():
            if '/build/' in path or '/.toolchain/' in path or '/spert/' in path:
                self.baseline[path] = value
        for info in self.expected['models'].values():
            if digest(info['path']) != info['sha256']:
                raise ValueError('model hash differs')
        self.verify_baseline()
        for arm in ('control', 'A1', 'B1', 'C', 'D'):
            path = self.root/arm
            manifest = json.loads((path/'manifest.json').read_text())
            if manifest['candidate'] != arm:
                raise ValueError('candidate label differs')
            for rel, value in manifest['files_sha256'].items():
                if digest(path/'overlay'/rel) != value:
                    raise ValueError('candidate hash differs: '+rel)
        self.recipes = {}
        self.links = {}
        for name, version in (('ggml-cpu', '0.16.0'), ('llama', '0.0.7')):
            target = 'bin/lib'+name+'.so.'+version
            lines = subprocess.check_output(['ninja', '-C', self.build, '-t', 'commands', target], text=True).splitlines()
            self.recipes[name] = lines
            self.links[name] = next(line for line in lines if ' -shared ' in line and ' -o '+target+' ' in line)
            for word in shlex.split(self.links[name].split(' && ')[1]):
                if word.endswith('.o'):
                    p = self.build/word
                    self.baseline[str(p)] = digest(p)
        fast.write_json(self.root/'baseline-before.json', self.baseline)

    def verify_baseline(self):
        bad = [p for p, value in self.baseline.items() if digest(p) != value]
        fast.write_json(self.root/'baseline-check.json', {'unchanged': not bad, 'different': bad})
        if bad:
            raise ValueError('baseline changed: '+str(bad))

    def compile_object(self, arm, rel):
        original = self.source/rel
        lines = set()
        for rows in self.recipes.values():
            for line in rows:
                words = shlex.split(line)
                if '-c' in words and words[words.index('-c')+1] == str(original):
                    lines.add(line)
        if len(lines) != 1:
            raise ValueError('compile recipe is not unique: '+rel)
        obj = self.root/arm/(original.name+'.o')
        argv = ime.compile_argv(next(iter(lines)), self.root/arm/'overlay'/rel, obj, original.parent)
        argv.insert(1, '-I'+str(BENCH))
        self.command(argv, arm+'-'+original.name+'-compile', cwd=self.build)
        return obj

    def link(self, arm, name, replacements):
        directory = self.root/arm/'lib'
        directory.mkdir(exist_ok=True)
        version = '0.16.0' if name == 'ggml-cpu' else '0.0.7'
        library = directory/('lib'+name+'.so.'+version)
        argv = ssm.rewrite_link(self.links[name], library, replacements)
        self.command(argv, arm+'-'+name+'-link', cwd=self.build)
        for suffix in ('.so', '.so.0'):
            (directory/('lib'+name+suffix)).symlink_to(library.name)

    def harness(self, arm, source, name, model=False):
        libs = ['-lllama', '-lggml'] if model else []
        argv = [self.tool, '-O3', '-std=c++17', '-DSPINE_K1_BOARD',
                '-march=rv64gcv_zfh_zvfh_zicbop_zihintpause_zba', '-mabi=lp64d',
                '-I'+str(BENCH), '-I'+str(self.source/'include'),
                '-I'+str(self.source/'ggml/include'), '-I'+str(self.source/'ggml/src/ggml-cpu'), source,
                '-L'+str(self.root/arm/'lib'), '-L'+str(self.server.parent),
                *libs, '-lggml-cpu', '-lggml-base', '-pthread', '-o', self.root/arm/name]
        self.command(argv, arm+'-'+name+'-build', arm)

    def build_all(self):
        self.phase('compile isolated libraries')
        route = self.compile_object('control', 'ggml/src/ggml-cpu/spacemit/ime.cpp')
        self.link('control', 'ggml-cpu', {'/ime.cpp.o': route})
        self.harness('control', HERE/'test-attention.cpp', 'test-attention')
        self.harness('control', BENCH/'test-k1-ssm-conv.cpp', 'test-ssm')
        for arm in self.arms:
            self.phase('compile '+arm)
            try:
                objects = {'/ime.cpp.o': route,
                           '/ops.cpp.o': self.compile_object(arm, 'ggml/src/ggml-cpu/ops.cpp')}
                if arm == 'D':
                    objects['/ggml-cpu.c.o'] = self.compile_object(arm, 'ggml/src/ggml-cpu/ggml-cpu.c')
                self.link(arm, 'ggml-cpu', objects)
                if arm in ('C', 'D'):
                    model_objects = {'/'+Path(rel).name+'.o': self.compile_object(arm, rel)
                                     for rel in ('src/models/delta-net-base.cpp', 'src/models/qwen35.cpp')}
                    self.link(arm, 'llama', model_objects)
                if arm in ('A1', 'B1'):
                    self.harness(arm, HERE/'test-attention.cpp', 'test-attention')
                elif arm == 'C':
                    self.harness(arm, BENCH/'test-k1-ssm-conv.cpp', 'test-ssm')
                    self.harness(arm, BENCH/'test-k1-gdn.cpp', 'test-gdn')
                    self.harness(arm, self.root/arm/'test-c-state.cpp', 'test-state', True)
                else:
                    self.harness(arm, HERE/'test-conv-silu.cpp', 'test-conv-silu')
                self.summary['candidates'][arm] = {'build': 'pass'}
            except Exception as exc:
                self.summary['candidates'][arm] = {'build': 'fail', 'error': str(exc)}
            self.save()
        fast.write_json(self.root/'libraries.json', {str(p): digest(p) for p in self.root.glob('*/lib/*.so.*') if p.is_file()})

    def dump(self, arm, binary, args, label, expected):
        path = self.root/(label+'.bin')
        text = self.command([binary, *args, '--dump', path], label, arm)
        if expected not in text:
            raise ValueError('numeric count differs: '+label)
        value = digest(path)
        path.unlink()
        return value, text

    def numeric(self, arm, reference_attention, reference_ssm):
        self.phase('correctness '+arm)
        base = self.root/arm
        if arm in ('A1', 'B1'):
            value, text = self.dump(arm, base/'test-attention', [], arm+'-numeric', 'PASS: 95')
            if value != reference_attention:
                raise ValueError('attention control differs from original')
            if 'path='+arm not in text:
                raise ValueError('attention activation is absent')
            return {'cases': 95, 'original_control_sha256': value}
        if arm == 'C':
            values = {}
            for mode in (0, 3):
                value, text = self.dump(arm, base/'test-ssm', [mode], 'C-ssm-'+str(mode), 'PASS: 432')
                if value != reference_ssm:
                    raise ValueError('convolution differs from original')
                values[str(mode)] = value
            text = self.command([base/'test-gdn'], 'C-gdn-numeric', arm)
            if 'PASS: 158' not in text:
                raise ValueError('GDN numeric count differs')
            return {'ssm_cases_per_arm': 432, 'ssm_sha256': values, 'gdn_cases': 158}
        text = self.command([base/'test-conv-silu'], 'D-numeric', arm)
        if 'PASS: 144' not in text or 'result=paired' not in text:
            raise ValueError('pair numeric count or activation differs')
        text = self.command([base/'test-conv-silu', '--diagnose'], 'D-diagnostic', arm)
        if 'K1_CONV_SILU_DIAG worker=' not in text:
            raise ValueError('pair diagnostic is absent')
        return {'cases': 144, 'diagnostic': 'D-diagnostic.log',
                'diagnostic_scope': 'Time between convolution return and SiLU entry. Includes dispatch and synchronization.'}

    def comparisons(self, rows, keys, arm_key='arm', candidate=1, minimum_ms=100):
        groups = {}
        for row in rows:
            if not math.isfinite(row['wall_ms']) or row['wall_ms'] < minimum_ms:
                raise ValueError('operator budget differs')
            key = tuple(row[k] for k in keys)
            groups.setdefault(key, {0: [], candidate: []})[row[arm_key]].append(row['ms_per_call'])
        comparisons = []
        for key, arms in groups.items():
            if any(len(values) != 6 for values in arms.values()):
                raise ValueError('operator block count differs')
            comparisons.append(dict(zip(keys, key), **fast.gate(arms[0], arms[candidate])))
        return comparisons

    def operators(self, arm):
        self.phase('operator screen '+arm)
        binary = self.root/arm
        if arm == 'C':
            rows = []
            for block in range(6):
                for channels in (6144, 8192):
                    for tokens in (1, 32):
                        for mode in ((0, 3) if block%2 == 0 else (3, 0)):
                            label = f'C-ssm-c{channels}-t{tokens}-b{block}-m{mode}'
                            text = self.command([binary/'test-ssm', '--bench', mode, channels, 4, tokens, 1], label, arm,
                                                updates={'SPINE_K1_TRACE': '0'})
                            records = [json.loads(line) for line in text.splitlines() if line.startswith('{')]
                            if len(records) != 1:
                                raise ValueError('SSM operator count differs')
                            rows.append(dict(records[0], block=block))
            fast.write_json(self.root/'C1-operators.json', rows)
            c1 = self.comparisons(rows, ['channels', 'tokens'], 'mode', 3, 200)
            text = self.command([binary/'test-gdn', '--bench'], 'C2-operators', arm,
                                updates={'SPINE_K1_TRACE': '0'})
            rows = [json.loads(line) for line in text.splitlines() if line.startswith('{')]
            c2 = self.comparisons(rows, ['heads', 'tokens'], 'mode')
            return {'C1': c1, 'C2': c2}
        argv = [binary/'test-attention', '--bench', arm] if arm in ('A1', 'B1') else [binary/'test-conv-silu', '--bench']
        text = self.command(argv, arm+'-operators', arm, updates={'SPINE_K1_TRACE': '0'})
        rows = [json.loads(line) for line in text.splitlines() if line.startswith('{')]
        return {arm: self.comparisons(rows, ['history', 'heads'] if arm in ('A1', 'B1') else ['channels', 'tokens'])}

    def execute(self):
        self.verify()
        self.build_all()
        reference_attention, _ = self.dump('original', self.root/'control/test-attention', [], 'original-attention', 'PASS: 95')
        control_attention, _ = self.dump('control', self.root/'control/test-attention', [], 'control-attention', 'PASS: 95')
        reference_ssm, _ = self.dump('original', self.root/'control/test-ssm', [0], 'original-ssm', 'PASS: 432')
        control_ssm, _ = self.dump('control', self.root/'control/test-ssm', [0], 'control-ssm', 'PASS: 432')
        if reference_attention != control_attention or reference_ssm != control_ssm:
            raise ValueError('route control differs from original')
        self.summary['original_control'] = {'attention_sha256': reference_attention, 'ssm_sha256': reference_ssm}
        qualified = []
        for arm, result in self.summary['candidates'].items():
            if result['build'] != 'pass':
                continue
            try:
                result['numeric'] = self.numeric(arm, reference_attention, reference_ssm)
                result['operators'] = self.operators(arm)
                result['eligible'] = []
                for name, comparisons in result['operators'].items():
                    if not any(row['clear_regression'] for row in comparisons) and any(row['advance'] for row in comparisons):
                        result['eligible'].append(name)
                        qualified.append(name)
                result['status'] = 'operator-screen-complete'
            except Exception as exc:
                result.update(status='failed', error=str(exc))
                (self.root/(arm+'-failure.txt')).write_text(traceback.format_exc())
            self.save()
        self.summary['eligible_for_model_gates'] = qualified
        self.summary['models'] = 'pending' if qualified else 'not-eligible'
        self.summary['status'] = 'operator-screen-complete'
        self.phase('operator screen complete; model gates pending' if qualified else 'operator screen complete; no eligible candidate')


def main():
    run = Run(Path(sys.argv[1]))
    lock_path = Path.home()/'Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock'
    with lock_path.open('a') as lock:
        run.phase('wait for shared experiment lock')
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            run.execute()
        except Exception as exc:
            run.summary.update(status='failed', error=str(exc))
            traceback.print_exc()
            return 1
        finally:
            try:
                run.verify_baseline()
            finally:
                run.save()
    return 0


if __name__ == '__main__':
    sys.exit(main())
