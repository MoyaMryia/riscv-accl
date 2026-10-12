#!/usr/bin/env python3
"""Replay frozen board prompts on a clean generic CPU build and identical GGUFs."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import socket
import subprocess
import tarfile
import time


def module(name, directory):
    spec = importlib.util.spec_from_file_location(name, directory / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    temporary.replace(path)


def clean_env():
    return {k: v for k, v in os.environ.items()
            if not k.startswith(('SPINE_', 'SPACEMIT_', 'LLAMA_', 'GGML_'))
            and k not in ('LD_PRELOAD', 'LD_LIBRARY_PATH')}


class Run:
    def __init__(self, root):
        self.root = root.resolve()
        self.config = json.loads((root / 'run.json').read_text())
        self.board = Path(self.config['board_evidence'])
        self.pilot = module('mtp-quality', self.board)
        self.checks = self.pilot.checks
        self.chat = self.pilot.chat
        self.judge = module('judge-shared-document-cache', self.board)
        self.started = time.monotonic()
        self.summary = {'status': 'running', 'planned_requests': 12,
                        'requests_completed': 0, 'models': {},
                        'limitations': 'x86 generic CPU versus K1 is a cross-backend quality check, not an isolated causal or speed comparison. Same seed at temperature zero does not ensure identical floating-point logits across architectures.'}

    def phase(self, text):
        (self.root / 'phase').write_text(text + '\n')
        print(text, flush=True)

    def save(self):
        self.summary['elapsed_s'] = time.monotonic() - self.started
        write(self.root / 'summary.json', self.summary)

    def command(self, args, log, timeout):
        with (self.root / log).open('w') as output:
            proc = subprocess.Popen([str(a) for a in args], stdout=output,
                                    stderr=subprocess.STDOUT, env=clean_env())
            try:
                code = proc.wait(timeout=timeout)
            except BaseException:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
                raise
        if code:
            raise RuntimeError(f'{log}: command failed with exit {code}')

    def copy_models(self):
        expected = json.loads((self.root / 'board-expected-provenance.json').read_text())
        evidence = {}
        for name, info in expected['models'].items():
            target = Path(self.config['models_dir']) / Path(info['path']).name
            if not target.exists() or digest(target) != info['sha256']:
                # Resume only task-owned partial files, then verify the full SHA-256.
                partial = target.with_suffix(target.suffix + '.partial')
                offset = partial.stat().st_size // (1024 * 1024) if partial.exists() else 0
                remote = ('dd if=' + shlex.quote(info['path']) +
                          ' bs=1048576 skip=' + str(offset) + ' status=none')
                start = time.monotonic()
                with partial.open('r+b' if partial.exists() else 'wb') as output:
                    output.truncate(offset * 1024 * 1024)
                    output.seek(0, 2)
                    with (self.root / (name + '-transfer.log')).open('w') as log:
                        proc = subprocess.Popen([
                            'ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=20',
                            '-o', 'ServerAliveInterval=30', '-o', 'ServerAliveCountMax=3',
                            self.config.get('ssh_host', 'musepipro'), remote],
                            stdout=output, stderr=log)
                        try:
                            code = proc.wait(timeout=24 * 3600)
                        except BaseException:
                            proc.terminate()
                            proc.wait(timeout=10)
                            raise
                if code:
                    raise RuntimeError(name + ' SSH model transfer failed with exit ' + str(code))
                if digest(partial) != info['sha256']:
                    raise ValueError(name + ' transferred partial model hash differs')
                partial.replace(target)
                write(self.root / (name + '-transfer-receipt.json'), {
                    'bytes': target.stat().st_size, 'elapsed_s': time.monotonic() - start,
                    'resumed_from_bytes': offset * 1024 * 1024,
                    'sha256': info['sha256'],
                    'ssh_host': self.config.get('ssh_host', 'musepipro')})
            actual = digest(target)
            if actual != info['sha256']:
                raise ValueError(name + ' local model SHA-256 differs from board')
            evidence[name] = {'path': str(target), 'sha256': actual,
                              'bytes': target.stat().st_size}
            write(self.root / 'model-verification.json', evidence)
        return evidence

    def build(self):
        prior = self.config.get('prior_preparation_run')
        if prior:
            deadline = time.monotonic() + 1800
            while not (Path(prior) / 'exit-status').exists():
                if time.monotonic() > deadline:
                    raise TimeoutError('previous preparation still owns the shared build directory')
                time.sleep(2)
        source = Path(self.config['source'])
        deadline = time.monotonic() + 1200
        while not (source / 'CMakeLists.txt').exists():
            if time.monotonic() > deadline:
                raise TimeoutError('clean source transfer did not complete')
            time.sleep(2)
        # Verify the whole extracted snapshot, not just the modified CPU files.
        archive = Path(self.config['source_archive'])
        with tarfile.open(archive) as tar:
            checked = {}
            for item in tar:
                if item.isfile():
                    path = source / item.name
                    expected = hashlib.sha256(tar.extractfile(item).read()).hexdigest()
                    if digest(path) != expected:
                        raise ValueError('clean source snapshot mismatch: ' + item.name)
                    checked[item.name] = expected
        write(self.root / 'source-verification.json', {
            'commit': self.config['source_commit'], 'archive_sha256': digest(archive),
            'verified_files': len(checked), 'files_sha256': checked})
        build = Path(self.config['build_dir'])
        options = {key: 'OFF' for key in (
            'GGML_NATIVE', 'GGML_SSE42', 'GGML_AVX', 'GGML_AVX2', 'GGML_AVX_VNNI',
            'GGML_AVX512', 'GGML_AVX512_VBMI', 'GGML_AVX512_VNNI', 'GGML_AVX512_BF16',
            'GGML_BMI2', 'GGML_FMA', 'GGML_F16C', 'GGML_AMX_TILE', 'GGML_AMX_INT8',
            'GGML_AMX_BF16', 'GGML_CPU_REPACK', 'GGML_CPU_KLEIDIAI', 'GGML_BLAS',
            'GGML_CUDA', 'GGML_VULKAN', 'GGML_SYCL', 'GGML_OPENCL', 'GGML_RPC',
            'GGML_CPU_RISCV64_SPACEMIT', 'GGML_BACKEND_DL', 'GGML_CPU_ALL_VARIANTS',
            'LLAMA_BUILD_TESTS', 'LLAMA_BUILD_EXAMPLES', 'LLAMA_CURL')}
        options.update(LLAMA_BUILD_SERVER='ON', CMAKE_BUILD_TYPE='Release',
                       CMAKE_EXPORT_COMPILE_COMMANDS='ON')
        configure = ['cmake', '-S', source, '-B', build, '-G', 'Ninja']
        configure += ['-D' + k + '=' + v for k, v in options.items()]
        write(self.root / 'build-config.json', {'command': [str(x) for x in configure],
              'settings': options, 'note': 'Ordinary release compiler optimization and baseline x86 ABI remain; no project patches, AVX/AMX, repacking, BLAS or accelerator backend.'})
        self.command(configure, 'configure.log', 600)
        self.command(['cmake', '--build', build, '--target', 'llama-server', '-j', '6'],
                     'build.log', 1800)
        server = build / 'bin/llama-server'
        with (self.root / 'reference-help.txt').open('w') as log:
            subprocess.run([server, '--help'], stdout=log, stderr=subprocess.STDOUT,
                           check=True, env=clean_env(), timeout=30)
        forbidden = ('SPINE_K1_', 'SPINE_FA_WIDE_TILE', 'SPINE_FA_K1_LAYOUT')
        changed = [str(p) for p in source.rglob('*') if p.is_file() and
                   p.suffix in ('.cpp', '.c', '.h') and
                   any(word in p.read_text(errors='replace') for word in forbidden)]
        if changed:
            raise ValueError('custom benchmark dispatch markers in clean source: ' + str(changed[:3]))
        write(self.root / 'build-verification.json', {
            'source_commit': self.config['source_commit'],
            'server_sha256': digest(server),
            'cmake_cache_sha256': digest(build / 'CMakeCache.txt'),
            'compile_commands_sha256': digest(build / 'compile_commands.json'),
            'custom_dispatch_markers_absent': True,
            'compiler': subprocess.check_output(['c++', '--version'], text=True).splitlines()[0]})
        return server

    def generate(self, server, models):
        port = self.config['port']
        url = f'http://127.0.0.1:{port}'
        with socket.socket() as probe:
            if probe.connect_ex(('127.0.0.1', port)) == 0:
                raise ValueError('local reference port already occupied')
        for model in ('2B', '4B'):
            cases = json.loads((self.root / ('board-' + model + '-cases.json')).read_text())['cases']
            board_pairs = json.loads((self.root / ('board-' + model + '-pairs.json')).read_text())
            argv = [str(server), '-m', models[model]['path'], '--alias', 'local',
                    '-t', '4', '-c', '6144', '--parallel', '1', '-b', '32', '-ub', '32',
                    '-fa', 'off', '-ctk', 'f16', '-ctv', 'f16', '-ngl', '0',
                    '--no-context-shift', '--host', '127.0.0.1', '--port', str(port)]
            write(self.root / (model + '-server-config.json'), {
                'command': argv, 'custom_runtime_variables': {}, 'flash_attention': False,
                'mtp': False, 'cpu_only': True})
            records = {}
            self.phase(model + ' clean reference server startup')
            with (self.root / (model + '-reference.server.log')).open('w') as log:
                proc = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, env=clean_env())
                try:
                    self.pilot.bench.wait_healthy(proc, url, 300)
                    for case in cases:
                        self.phase(model + ' reference ' + case['case_id'])
                        board = board_pairs[case['case_id']]['control']
                        payload = board['request']
                        if payload['seed'] != 42 or payload['temperature'] != 0 or payload['cache_prompt']:
                            raise ValueError('frozen sampling/cold prompt differs')
                        count = self.chat.count_prompt_tokens(url, payload, 120)
                        if count != board['prompt_tokens']:
                            raise ValueError('reference prompt token count differs from board')
                        answer = self.chat.complete(url, payload, 3600, display=False)
                        audit = self.pilot.audit_result(answer, payload, count)
                        audit['draft_disabled'] = answer['timings'].get('draft_n', 0) == 0
                        if not all(value for key, value in audit.items() if key != 'complete'):
                            raise ValueError('reference cold input/completion audit failed: ' + str(audit))
                        facts = self.checks.fact_check(case, answer['answer'])
                        code = self.checks.check_code(case['case_id'], answer['answer']) if case['kind'] == 'code' else {}
                        record = dict(answer, model=model, case_id=case['case_id'], request=payload,
                                      request_sha256=board['request_sha256'], prompt_tokens=count,
                                      audit=audit, facts=facts, code_test=code,
                                      text_identical_to_board_control=answer['answer'] == board['answer'],
                                      text_identical_to_board_hybrid=answer['answer'] == board_pairs[case['case_id']]['hybrid']['answer'])
                        records[case['case_id']] = record
                        write(self.root / (model + '-reference.json'), records)
                        (self.root / (model + '-reference-' + case['case_id'] + '-answer.md')).write_text(answer['answer'] + '\n')
                        self.summary['requests_completed'] += 1
                        self.summary['models'][model] = {'generated': len(records)}
                        self.save()
                finally:
                    proc.terminate()
                    try:
                        proc.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait()
        self.summary['generation_completed'] = True
        self.save()

    def score(self):
        # The already authorized cloud endpoint sees only task evidence and answers.
        key = (Path.home() / '.secret_ai_key').read_text().strip()
        endpoint = self.judge.endpoint('https://api.xiaomimimo.com/v1', False)
        previous_summary = json.loads((self.board / 'ssm-quality-summary.json').read_text())
        for model in ('2B', '4B'):
            records = json.loads((self.root / (model + '-reference.json')).read_text())
            cases = json.loads((self.root / ('board-' + model + '-cases.json')).read_text())['cases']
            pairs = json.loads((self.root / ('board-' + model + '-pairs.json')).read_text())
            previous = {r['case_id']: r for r in previous_summary['models'][model]['comparisons']}
            grade_file = self.root / (model + '-judge.jsonl')
            grades = {r['case_id']: r for r in map(json.loads, grade_file.read_text().splitlines())} if grade_file.exists() else {}
            comparisons = []
            for case in cases:
                name = case['case_id']
                reference = records[name]
                row = {'case_id': name, 'text_identical': reference['text_identical_to_board_control'],
                       'reference_natural_stop': reference['audit']['complete'],
                       'board_useful': previous[name]['useful']['control'],
                       'reference_facts': reference['facts'], 'reference_code_test': reference['code_test']}
                absolute = (reference['audit']['complete'] and all(reference['facts']['facts'])
                            and all(reference['facts']['citations'])
                            and (case['kind'] != 'code' or reference['code_test'].get('pass') is True))
                item = {'case_id': model + '-' + name, 'question': case['question'],
                        'evidence': case['evidence'], 'required_facts': case['required_facts'],
                        'cold_answer': pairs[name]['control']['answer'], 'warm_answer': reference['answer']}
                write(self.root / (model + '-' + name + '-judge-input.json'), item)
                fingerprint = hashlib.sha256(json.dumps(item, sort_keys=True).encode()).hexdigest()
                if reference['audit']['complete']:
                    self.phase(model + ' judge ' + name)
                    rating = grades.get(item['case_id'])
                    if rating is None:
                        rating = self.judge.grade_case(item, endpoint, 'mimo-v2.6-flash', key, 120, 2, 4096, True)
                        with grade_file.open('a') as output:
                            output.write(json.dumps(rating, ensure_ascii=False) + '\n')
                    if rating['input_sha256'] != fingerprint or len(rating['passes']) != 2:
                        raise ValueError('local comparison judgment input differs')
                    row.update(reference_score=rating['warm_mean_score'],
                               board_rescored=rating['cold_mean_score'])
                else:
                    row.update(reference_score=None, board_rescored=None)
                row['reference_useful'] = bool(absolute and row['reference_score'] is not None and row['reference_score'] >= 4)
                comparisons.append(row)
                self.summary['models'][model].update(comparisons=comparisons,
                    reference_useful=sum(x['reference_useful'] for x in comparisons),
                    board_useful=sum(x['board_useful'] for x in comparisons),
                    identical_answers=sum(x['text_identical'] for x in comparisons))
                self.save()

    def run(self, score_only=False):
        try:
            if score_only:
                self.summary = json.loads((self.root / 'summary.json').read_text())
            else:
                self.phase('build generic reference and copy exact model files')
                self.save()
                with ThreadPoolExecutor(max_workers=2) as pool:
                    build = pool.submit(self.build)
                    models = pool.submit(self.copy_models)
                    server = build.result()
                    models = models.result()
                self.generate(server, models)
                (self.root / 'generation-exit-status').write_text('0\n')
            self.score()
            self.summary['status'] = 'completed'
            self.save()
            self.phase('completed')
        except BaseException as error:
            self.summary.update(status='failed', reason=type(error).__name__ + ': ' + str(error)[:300])
            self.save()
            self.phase('failed')
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_dir', type=Path)
    parser.add_argument('--score-only', action='store_true')
    args = parser.parse_args()
    Run(args.run_dir).run(args.score_only)
