#!/usr/bin/env python3
"""Run the C2-r2 state gate, screen, repeats and complete answers."""
import fcntl
import json
import os
from pathlib import Path
import re
import signal
import shutil
import subprocess
import sys
import traceback

import board
import prefill_c2_r2 as prefill
import complete_answers_c2_r2 as complete_answers

HERE = Path(__file__).resolve().parent


def main():
    root, screen = (Path(p).resolve() for p in sys.argv[1:3])
    plan = json.loads((root/'model-protocol.json').read_text())
    expected = json.loads((screen/'expected-provenance.json').read_text())
    server = next(Path(p) for p in expected['artifacts_sha256'] if p.endswith('/llama-server'))
    source, library = server.parents[2], root/'lib'
    lock_path = Path.home()/'Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock'
    summary = {'revision': 'C2-r2', 'status': 'running', 'state': {}, 'comparisons': [],
               'repeats': [], 'full_answers': 'pending'}
    commands = []

    def save(phase):
        (root/'phase').write_text(phase+'\n')
        (root/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
        print(phase, flush=True)

    def verify():
        if plan['repeats'] != 2 or plan['order'] != ['C0', 'C2', 'C2', 'C0']:
            raise ValueError('C2-r2 model protocol differs')
        for path, value in plan['fixed_files_sha256'].items():
            if board.digest(path) != value:
                raise ValueError('fixed file changed: '+path)
        for path, value in json.loads((screen/'baseline-before.json').read_text()).items():
            if board.digest(path) != value:
                raise ValueError('baseline changed: '+path)
        operators = json.loads((screen/'summary.json').read_text())
        if operators.get('revision') != 'C2-r2' or not operators.get('strict_operator_gate', {}).get('eligible'):
            raise ValueError('C2-r2 strict operator gate is absent')
        if not json.loads((screen/'baseline-check.json').read_text())['unchanged']:
            raise ValueError('baseline check fails')
        rows = operators['candidates']['C']['operators']['C2']
        if {(r['heads'], r['tokens']) for r in rows} != {(h, t) for h in [16, 32] for t in [8, 32]}:
            raise ValueError('operator shapes differ')
        if any(r['clear_regression'] for r in rows) or not all(r['advance'] for r in rows if r['tokens'] == 32):
            raise ValueError('operator gate fails')
        libraries = json.loads((screen/'libraries.json').read_text())
        for path, value in libraries.items():
            if '/C/lib/' in path and board.digest(path) != value:
                raise ValueError('candidate library changed')
        for name, info in expected['models'].items():
            if board.digest(info['path']) != info['sha256']:
                raise ValueError('model changed: '+name)
        if 'identity' in summary:
            identity = summary['identity']
            if board.digest(library/'libggml-cpu.so') != identity['library_sha256']:
                raise ValueError('model CPU library changed')
            if board.digest(library/'libllama.so') != identity['model_library_sha256']:
                raise ValueError('model library changed')
            if board.digest(server) != identity['server_sha256']:
                raise ValueError('server changed')

    def run(command, label, arm=0, original=False, timeout=1800):
        environment = prefill.arm_env('C2' if arm else 'C0', library)
        environment.update(SPINE_K1_TRACE='1', SPINE_K1_FA_GQA='0', SPINE_K1_FA_DECODE='0',
                           SPINE_K1_CONV_SILU='0', SPINE_K1_SSM_CONV='0')
        if original:
            environment['LD_LIBRARY_PATH'] = expected['runtime']['LD_LIBRARY_PATH']
        commands.append({'argv': list(map(str, command)), 'label': label, 'original': original,
                         'runtime': {k: v for k, v in environment.items()
                                     if k.startswith('SPINE_') or k == 'LD_LIBRARY_PATH'}})
        (root/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
        with (root/(label+'.log')).open('w') as output:
            subprocess.run(list(map(str, command)), env=environment, stdout=output,
                           stderr=subprocess.STDOUT, timeout=timeout, check=True)
        return (root/(label+'.log')).read_text()

    def revision_activation(text):
        if 'SPINE_GDN_PREFILL_R2: retained two state segments; S=128; VLEN=256' not in text:
            raise ValueError('C2-r2 activation is absent')
        workers = set(re.findall(r'K1_GDN_R2 worker=(\d+) workers=4 state=128', text))
        if workers != {'0', '1', '2', '3'}:
            raise ValueError('C2-r2 worker evidence is incomplete')

    def compare(destination, lock):
        try:
            result = prefill.compare(type('Arguments', (), dict(destination=destination,
                candidate='C2', reference='C0', execute=True, lock=lock_path, library=library, server=server,
                model_2b=Path(expected['models']['2B']['path']), model_4b=Path(expected['models']['4B']['path']),
                qualification=root/'C2-qualification.json', single_results=[]))(), benchmark_lock=lock)
        except ValueError as exc:
            if str(exc) != 'output or input tokens differ across arms':
                raise
            result = {'status': 'cold-token-difference', 'error': str(exc)}
            (destination/'token-failure.json').write_text(json.dumps(result, indent=2)+'\n')
        for path in destination.glob('*-C2-*.server.log'):
            revision_activation(path.read_text())
        return result

    save('wait for shared experiment lock')
    with lock_path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            os.environ['LD_LIBRARY_PATH'] = expected['runtime']['LD_LIBRARY_PATH']
            save('verify C2-r2 model prerequisites')
            verify()
            library.mkdir()
            for name, version in [('ggml-cpu', '0.16.0'), ('llama', '0.0.7')]:
                shutil.copyfile(screen/'C/lib'/('lib'+name+'.so'), library/('lib'+name+'.so.'+version))
                for suffix in ['.so', '.so.0']:
                    (library/('lib'+name+suffix)).symlink_to('lib'+name+'.so.'+version)
            summary['identity'] = {'library_sha256': board.digest(library/'libggml-cpu.so'),
                'model_library_sha256': board.digest(library/'libllama.so'), 'server_sha256': board.digest(server),
                'models_sha256': {m: info['sha256'] for m, info in expected['models'].items()}}
            binary = root/'test-c2-r2-state'
            save('compile isolated C2-r2 state probe')
            run([Path.home()/'Projects/llm-bench/.toolchain/gcc14/usr/bin/g++-14', '-O3', '-std=c++17',
                 '-march=rv64gcv_zfh_zvfh_zicbop_zihintpause_zba', '-mabi=lp64d',
                 '-I'+str(source/'include'), '-I'+str(source/'ggml/include'), HERE/'test-c2-r2-state.cpp',
                 '-L'+str(library), '-L'+str(server.parent), '-lllama', '-lggml', '-lggml-cpu',
                 '-lggml-base', '-pthread', '-o', binary], 'state-build', timeout=600)
            summary['probe_sha256'] = board.digest(binary)
            for name, info in expected['models'].items():
                saved = {}
                for label, arm, original in [('original', 0, True), ('C0', 0, False), ('C2', 1, False)]:
                    save('state '+name+' '+label)
                    stem = name+'-'+label+'-state'; dump = root/(stem+'.bin')
                    try:
                        text = run([binary, info['path'], str(arm), dump], stem, arm, original)
                    except subprocess.CalledProcessError:
                        text = (root/(stem+'.log')).read_text()
                        if 'FAIL: candidate logits differ' not in text and 'FAIL: nonfinite logits' not in text:
                            raise
                        summary.update(status='state-numeric-stopped', full_answers='not-eligible',
                                       numeric_failure_log=stem+'.log')
                        verify(); save('state numerical gate stopped; preserve the result')
                        return 0
                    rows = [json.loads(line) for line in text.splitlines() if line.startswith('{')]
                    keys = [(rs, reset, p) for rs in [0, 3] for reset in [0, 1] for p in [32, 33, 64, 96]]
                    if [(r['rs'], r['reset'], r['prefix']) for r in rows] != keys or not all(r['bitwise_equal'] and r['max_abs'] == 0 for r in rows):
                        raise ValueError('state records differ')
                    if 'PASS: 16 full-vocabulary records;' not in text:
                        raise ValueError('state probe is incomplete')
                    if dump.stat().st_size != sum(r['vocab']*4 for r in rows):
                        raise ValueError('full vocabulary dump size differs')
                    threads = re.findall(r'C2_STATE threads=(\d+) batch_threads=(\d+) rs=(\d+)', text)
                    if len(threads) != (4 if arm else 2) or any(a != '4' or b != '4' for a, b, _ in threads):
                        raise ValueError('state thread evidence differs')
                    if arm:
                        revision_activation(text)
                        prefill.activation(text, 'C2')
                        quality = prefill.prepare.module('c2_state_quality', HERE.parent/'k1-ssm-quality.py')
                        quality.check_activation(text, 0)
                        spans = re.findall(r'C2_STATE begin arm=(\d)[^\n]*\n(.*?)C2_STATE end arm=\1', text, re.S)
                        if len(spans) != 32:
                            raise ValueError('state arm spans are incomplete')
                        for active, span in spans:
                            if ('K1_GDN_R2 worker=' in span or 'SPINE_GDN_PREFILL_R2:' in span) and active != '1':
                                raise ValueError('state control activates C2-r2')
                    elif 'SPINE_GDN_PREFILL_R2:' in text:
                        raise ValueError('control activates C2-r2')
                    saved[label] = {'rows': rows, 'dump_sha256': board.digest(dump),
                                    'log_sha256': board.digest(root/(stem+'.log'))}
                summary['state'][name] = saved
                if len({value['dump_sha256'] for value in saved.values()}) != 1:
                    summary.update(status='original-state-difference', full_answers='not-eligible')
                    verify(); save('original state comparison differs; preserve the result')
                    return 0
                save('fresh RS=3 fallback '+name)
                fallback_dump = root/(name+'-C2-rs3-fallback.bin')
                try:
                    text = run([binary, info['path'], '1', fallback_dump, 'rs3'], name+'-C2-rs3-fallback', 1)
                except subprocess.CalledProcessError:
                    text = (root/(name+'-C2-rs3-fallback.log')).read_text()
                    if 'FAIL: candidate logits differ' not in text and 'FAIL: nonfinite logits' not in text:
                        raise
                    summary.update(status='rs3-state-numeric-stopped', full_answers='not-eligible')
                    verify(); save('RS=3 numerical gate stopped; preserve the result')
                    return 0
                fallback_rows = [json.loads(line) for line in text.splitlines() if line.startswith('{')]
                expected_rows = [r for r in saved['C2']['rows'] if r['rs'] == 3]
                if fallback_rows != expected_rows:
                    raise ValueError('fresh RS=3 state records differ')
                if 'PASS: 8 full-vocabulary records;' not in text:
                    raise ValueError('fresh RS=3 state probe is incomplete')
                threads = re.findall(r'C2_STATE threads=(\d+) batch_threads=(\d+) rs=(\d+)', text)
                if threads != [('4', '4', '3'), ('4', '4', '3')]:
                    raise ValueError('fresh RS=3 thread evidence differs')
                for marker in ('SPINE_GDN_PREFILL_R2:', 'K1_GDN_R2 worker=',
                               'SPINE_GDN_PREFILL: scalar-gate K1 RVV fusion enabled'):
                    if marker in text:
                        raise ValueError('RS=3 activates the GDN candidate')
                original_dump = (root/(name+'-C2-state.bin')).read_bytes()
                if fallback_dump.read_bytes() != original_dump[len(original_dump)//2:]:
                    summary.update(status='rs3-state-numeric-stopped', full_answers='not-eligible')
                    verify(); save('RS=3 state differs; preserve the result')
                    return 0
                quality = prefill.prepare.module('c2_fallback_quality', HERE.parent/'k1-ssm-quality.py')
                quality.check_activation(text, 0, require_both=False)
                if not quality.MARKER.findall(text) or any(row[2] != '3' for row in quality.MARKER.findall(text)):
                    raise ValueError('RS=3 graph evidence differs')
                summary['state'][name]['fresh_rs3_fallback'] = {'rows': fallback_rows,
                    'dump_sha256': board.digest(fallback_dump),
                    'log_sha256': board.digest(root/(name+'-C2-rs3-fallback.log'))}
                save('state '+name+' passed')
            verify()
            qualification = {'identity': summary['identity'], 'qualified_arms': ['C2'],
                'numeric_passed': True, 'state_passed': True, 'operators_passed': True,
                'state_evidence': summary['state'], 'operator_evidence': str(screen/'summary.json')}
            (root/'C2-qualification.json').write_text(json.dumps(qualification, indent=2)+'\n')
            for phase, destination in [('initial', 'C2-vs-C0'), ('repeat-1', 'repeat-1'), ('repeat-2', 'repeat-2')]:
                save(phase+' cold requests')
                result = compare(root/destination, lock)
                if phase == 'initial':
                    summary['initial'] = result
                else:
                    summary['repeats'].append(dict(result, independent_repeat=int(phase[-1])))
                if result['status'] != 'eligible':
                    summary.update(status=phase+'-gate-stopped', full_answers='not-eligible')
                    verify(); save(phase+' gate stopped; preserve the result')
                    return 0
                verify(); save(phase+' passed')
            def expired(signum, frame):
                raise TimeoutError('complete-answer request budget expired')

            signal.signal(signal.SIGALRM, expired)
            signal.signal(signal.SIGTERM, expired)
            save('complete paired answers')
            complete_answers.collect(root/'complete-answers', source, server, expected, library, 'C2')
            for name in expected['models']:
                revision_activation((root/'complete-answers'/(name+'-C2.server.log')).read_text())
            verify()
            summary.update(status='complete-answers-generated; review-pending',
                           full_answers='review-pending', baseline_preserved=True)
            save('complete paired answers generated; review pending')
        except BaseException as exc:
            summary.update(status='failed', error=str(exc))
            (root/'failure.txt').write_text(traceback.format_exc())
            save('C2-r2 model campaign failed')
            raise
    return 0


if __name__ == '__main__':
    sys.exit(main())
