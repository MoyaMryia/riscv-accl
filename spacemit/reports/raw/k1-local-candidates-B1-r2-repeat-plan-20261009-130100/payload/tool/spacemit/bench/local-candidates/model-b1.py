#!/usr/bin/env python3
"""Run the fixed B1-r2 state gate and cold model screen."""
import fcntl
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import traceback

import board
import prefill

HERE = Path(__file__).resolve().parent
PATH = re.compile(r'K1_FA path=([\w-]+) heads=(\d+) kv_heads=(\d+) history=(\d+) chunk=(\d+):(\d+) worker=(\d+) workers=(\d+)')


def activation(text, arm, heads, require_shared, require_fallback=False):
    rows = PATH.findall(text)
    if any(int(row[-1]) != 4 for row in rows):
        raise ValueError('attention worker count differs')
    shared = [row for row in rows if row[0] == 'B1']
    if not arm and shared:
        raise ValueError('control activates B1')
    if require_shared:
        if {int(row[-2]) for row in shared if int(row[1]) == heads and int(row[3]) >= 512} != {0, 1, 2, 3}:
            raise ValueError('long-history B1 activation is absent')
        if 'K1_FA group=4 stack_bytes=5184 shared=K,V' not in text:
            raise ValueError('group scratch evidence is absent')
    if arm and heads == 8 and require_fallback:
        if {int(row[-2]) for row in rows if row[0] == 'reference-underfilled-groups' and int(row[3]) < 512} != {0, 1, 2, 3}:
            raise ValueError('short-history fallback evidence is absent')
    if any(row[0] == 'B1' and int(row[2]) < 4 and int(row[3]) < 512 for row in rows):
        raise ValueError('underfilled group activates B1')
    if 'K1_GEMM_ROUTE mode=3' not in text or 'SPINE_FA_WIDE_TILE: RVV tiled attention enabled for 256-dim heads' not in text:
        raise ValueError('fixed route or attention evidence is absent')
    return {'path_markers': len(rows), 'shared_markers': len(shared), 'workers': 4}


def main():
    root, screen = (Path(p).resolve() for p in sys.argv[1:3])
    plan = json.loads((root/'model-protocol.json').read_text())
    expected = json.loads((screen/'expected-provenance.json').read_text())
    server = next(Path(p) for p in expected['artifacts_sha256'] if p.endswith('/llama-server'))
    source = server.parents[2]
    summary = {'status': 'running', 'revision': 'B1-r2', 'state': {}, 'comparisons': [], 'full_answers': 'pending'}
    commands = []
    library = root/'lib'
    lock_path = Path.home()/'Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock'

    def save(phase):
        (root/'phase').write_text(phase+'\n')
        (root/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
        print(phase, flush=True)

    def verify():
        for path, value in plan['fixed_files_sha256'].items():
            if board.digest(path) != value:
                raise ValueError('fixed file changed: '+path)
        for path, value in json.loads((screen/'baseline-before.json').read_text()).items():
            if board.digest(path) != value:
                raise ValueError('baseline changed: '+path)
        for model, info in expected['models'].items():
            if board.digest(info['path']) != info['sha256']:
                raise ValueError('model changed: '+model)
        cpu = screen/'B1/lib/libggml-cpu.so'
        manifest = json.loads((screen/'libraries.json').read_text())
        if board.digest(cpu) != manifest[str(cpu.resolve())]:
            raise ValueError('candidate library changed')
        result = json.loads((screen/'summary.json').read_text())
        rows = result['candidates']['B1']['operators']['B1']
        if len(rows) != 4 or any(row['clear_regression'] for row in rows):
            raise ValueError('operator gate is incomplete')
        if not all(row['advance'] for row in rows if (row['history'], row['heads']) != (256, 8)):
            raise ValueError('shared operator gate fails')
        if not json.loads((screen/'baseline-check.json').read_text())['unchanged']:
            raise ValueError('baseline check fails')
        if 'identity' in summary:
            if board.digest(library/'libggml-cpu.so') != summary['identity']['candidate_cpu_sha256']:
                raise ValueError('model CPU library changed')
            if board.digest(library/'libllama.so') != summary['identity']['model_library_sha256']:
                raise ValueError('model library changed')

    def env(arm, original=False):
        value = {k: v for k, v in os.environ.items() if not k.startswith(('SPINE_', 'SPACEMIT_'))}
        value.update(SPINE_FA_WIDE_TILE='1', SPINE_FA_K1_LAYOUT='0', SPINE_K1_GEMM_ROUTE='3',
                     SPINE_K1_FA_GQA=str(arm), SPINE_K1_FA_DECODE='0', SPINE_GDN_PREFILL='0',
                     SPINE_K1_SSM_CONV='0', SPINE_K1_TRACE='1')
        value['LD_LIBRARY_PATH'] = expected['runtime']['LD_LIBRARY_PATH']
        if not original:
            value['LD_LIBRARY_PATH'] = str(library)+':'+value['LD_LIBRARY_PATH']
        return value

    def run(command, label, arm=0, original=False, timeout=3600):
        environment = env(arm, original)
        commands.append({'argv': list(map(str, command)), 'label': label, 'original': original,
                         'runtime': {k: v for k, v in environment.items()
                                     if k.startswith('SPINE_') or k == 'LD_LIBRARY_PATH'}})
        (root/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
        with (root/(label+'.log')).open('w') as output:
            subprocess.run(list(map(str, command)), env=environment, stdout=output,
                           stderr=subprocess.STDOUT, timeout=timeout, check=True)
        return (root/(label+'.log')).read_text()

    save('wait for shared experiment lock')
    with lock_path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            verify()
            library.mkdir()
            shutil.copyfile(screen/'B1/lib/libggml-cpu.so', library/'libggml-cpu.so.0.16.0')
            shutil.copyfile(server.parent/'libllama.so', library/'libllama.so.0.0.7')
            for name, version in [('ggml-cpu', '0.16.0'), ('llama', '0.0.7')]:
                for suffix in ['.so', '.so.0']:
                    (library/('lib'+name+suffix)).symlink_to('lib'+name+'.so.'+version)
            summary['identity'] = {'candidate_cpu_sha256': board.digest(library/'libggml-cpu.so'),
                'original_cpu_sha256': board.digest(server.parent/'libggml-cpu.so'),
                'model_library_sha256': board.digest(library/'libllama.so'),
                'server_sha256': board.digest(server), 'models': expected['models']}
            save('compile isolated state probe')
            binary = root/'test-b1-state'
            run([Path.home()/'Projects/llm-bench/.toolchain/gcc14/usr/bin/g++-14', '-O3', '-std=c++17',
                 '-march=rv64gcv_zfh_zvfh_zicbop_zihintpause_zba', '-mabi=lp64d',
                 '-I'+str(source/'include'), '-I'+str(source/'ggml/include'), HERE/'test-b1-state.cpp',
                 '-L'+str(library), '-L'+str(server.parent), '-lllama', '-lggml', '-lggml-cpu',
                 '-lggml-base', '-pthread', '-o', binary], 'state-build', timeout=600)
            summary['probe_sha256'] = board.digest(binary)
            for model, info in expected['models'].items():
                saved = {}
                for label, arm, original in [('original', 0, True), ('B0', 0, False), ('B1', 1, False)]:
                    save('state '+model+' '+label)
                    name = model+'-'+label+'-state'
                    dump = root/(name+'.bin')
                    try:
                        text = run([binary, info['path'], str(arm), dump], name, arm, original)
                    except subprocess.CalledProcessError:
                        text = (root/(name+'.log')).read_text()
                        if 'FAIL: candidate logits differ' not in text and 'FAIL: nonfinite logits' not in text:
                            raise
                        summary.update(status='state-numeric-stopped', full_answers='not-eligible',
                                       numeric_failure_log=name+'.log')
                        verify(); save('state numerical gate stopped; preserve the result')
                        return 0
                    rows = [json.loads(line) for line in text.splitlines() if line.startswith('{')]
                    expected_rows = [(rs, reset, prefix) for rs in [0, 3] for reset in [0, 1]
                                     for prefix in [32, 33, 64, 96, 255, 256, 511, 512, 2047, 2048]]
                    if [(r['rs'], r['reset'], r['prefix']) for r in rows] != expected_rows or not all(r['bitwise_equal'] for r in rows):
                        raise ValueError('state records differ')
                    if dump.stat().st_size != sum(r['vocab']*4 for r in rows):
                        raise ValueError('full vocabulary dump size differs')
                    thread_rows = re.findall(r'B1_STATE threads=(\d+) batch_threads=(\d+) rs=(\d+)', text)
                    if len(thread_rows) != (4 if arm else 2) or any(a != '4' or b != '4' for a, b, _ in thread_rows):
                        raise ValueError('state context thread evidence differs')
                    if arm:
                        activation(text, arm, info['shape']['heads'], True, True)
                        spans = re.findall(r'B1_STATE begin arm=(\d)[^\n]*\n(.*?)B1_STATE end arm=\1', text, re.S)
                        if len(spans) != 80:
                            raise ValueError('state arm spans are incomplete')
                        for active, span in spans:
                            if 'K1_FA path=B1 ' in span and active != '1':
                                raise ValueError('state control activates B1')
                    saved[label] = {'rows': rows, 'dump_sha256': board.digest(dump), 'log_sha256': board.digest(root/(name+'.log'))}
                summary['state'][model] = saved
                if len({value['dump_sha256'] for value in saved.values()}) != 1:
                    summary.update(status='original-state-difference', full_answers='not-eligible')
                    verify(); save('original state comparison differs; preserve the result')
                    return 0
                save('state '+model+' passed')
            verify()
            save('cold ABBA model screen')
            cold = root/'cold'; cold.mkdir()
            for tokens in [512, 2048]:
                for model, info in expected['models'].items():
                    for outputs in [1, 65]:
                        records, labels = [], []
                        for index, arm in enumerate([0, 1, 1, 0]):
                            label = f'{model}-p{tokens}-n{outputs}-B{arm}-{index}'
                            labels.append(label)
                            save('cold '+label)
                            data, log = cold/(label+'.jsonl'), cold/(label+'.server.log')
                            command = [sys.executable, HERE.parent/'bench-lifecycle.py', '--server', server,
                                '--model', info['path'], '--label', label, '--mode', 'plain', '--contexts', str(tokens),
                                '--n-predict', str(outputs), '--ignore-eos', '--verify-cold', '--capture-token-ids',
                                '--threads', '4', '--batch-size', '32', '--ubatch-size', '32', '--gpu-layers', '0',
                                '--ctx-size', '4096', '--cache-type-k', 'f16', '--cache-type-v', 'f16',
                                '--timeout', '600', '--output', data, '--log', log]
                            run(command, label, arm, timeout=700)
                            activation(log.read_text(), arm, info['shape']['heads'], arm == 1 and outputs == 65)
                            records.extend(json.loads(line) for line in data.read_text().splitlines())
                        try:
                            requests = prefill.FAST.check_model_records(records, labels, tokens, outputs)
                        except ValueError as exc:
                            if str(exc) != 'output or input tokens differ across arms':
                                raise
                            summary.update(status='cold-token-difference', full_answers='not-eligible',
                                           token_failure={'model': model, 'tokens': tokens, 'outputs': outputs})
                            verify(); save('cold tokens differ; preserve the result')
                            return 0
                        metrics = {}
                        for metric, key in [('prefill', 'prompt_ms'), ('decode', 'predicted_ms'), ('ttft', None)]:
                            if metric == 'decode' and outputs == 1:
                                continue
                            times = [[r['results'][0]['timings'][key] if key else r['results'][0]['ttft_ms']
                                      for r in requests if f'-B{arm}-' in r['label']] for arm in [0, 1]]
                            if any(not math.isfinite(t) or t <= 0 for group in times for t in group):
                                raise ValueError('invalid phase time')
                            metrics[metric] = prefill.FAST.gate(*times)
                        passed = not any(v['clear_regression'] for v in metrics.values())
                        if tokens == 2048 and outputs == 65:
                            passed = passed and metrics['decode']['advance']
                        summary['comparisons'].append({'model': model, 'tokens': tokens, 'outputs': outputs,
                                                       'metrics': metrics, 'passed': passed})
                        if not passed:
                            summary.update(status='model-gate-stopped', full_answers='not-eligible')
                            verify(); save('model gate stopped; preserve the result')
                            return 0
            verify()
            summary.update(status='model-screen-eligible', full_answers='independent repeats required', baseline_preserved=True)
            save('initial model screen passed; independent repeats pending')
        except BaseException as exc:
            summary.update(status='failed', error=str(exc))
            (root/'failure.txt').write_text(traceback.format_exc())
            save('B1-r2 model campaign failed')
            raise
    return 0


if __name__ == '__main__':
    sys.exit(main())
