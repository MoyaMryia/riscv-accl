#!/usr/bin/env python3
"""Run qualified C model gates under the shared board lock."""
import argparse
import fcntl
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import traceback

import board
import prefill


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('screen', type=Path)
    parser.add_argument('--arms', choices=('C1', 'C2'), nargs='+', default=['C1', 'C2'])
    parser.add_argument('--reuse-model-gates', type=Path)
    parser.add_argument('--reuse-state', type=Path)
    args = parser.parse_args()
    root, screen = args.root.resolve(), args.screen.resolve()
    single_results = {arm: root/(arm+'-vs-C0/result.json') for arm in ('C1', 'C2')}
    summary = {'status': 'running', 'arms': {}, 'full_answers': 'pending'}
    expected = json.loads((screen/'expected-provenance.json').read_text())
    operators = json.loads((screen/'summary.json').read_text())
    libraries = json.loads((screen/'libraries.json').read_text())
    library = screen/'C/lib'
    binary = screen/'C/test-state'
    server = next(Path(p) for p in expected['artifacts_sha256'] if p.endswith('/llama-server'))
    lock_path = Path.home()/'Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock'
    os.environ['LD_LIBRARY_PATH'] = expected['runtime']['LD_LIBRARY_PATH']

    def save(phase):
        (root/'phase').write_text(phase+'\n')
        (root/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
        print(phase, flush=True)

    def verify():
        if json.loads((screen/'baseline-check.json').read_text()).get('unchanged') is not True:
            raise ValueError('baseline check is absent')
        if operators.get('status') != 'operator-screen-complete':
            raise ValueError('operator screen is incomplete')
        if board.digest(server) != expected['artifacts_sha256'][str(server)]:
            raise ValueError('server changed')
        for p, value in libraries.items():
            if '/C/lib/' in p and board.digest(p) != value:
                raise ValueError('candidate library changed')
        for p, value in json.loads((screen/'baseline-before.json').read_text()).items():
            if board.digest(p) != value:
                raise ValueError('baseline changed: '+p)

    def state(arm, mode):
        save('state '+arm)
        env = prefill.arm_env('C0', library)
        env['SPINE_K1_TRACE'] = '1'
        records = []
        for model, info in expected['models'].items():
            log = root/(arm+'-'+model+'-state.log')
            previous_log = args.reuse_state/(arm+'-'+model+'-state.log') if args.reuse_state else None
            reused = previous_log is not None and previous_log.is_file()
            if reused:
                shutil.copyfile(previous_log, log)
            else:
                with log.open('w') as output:
                    subprocess.run([str(binary), info['path'], str(mode)], stdout=output,
                                   stderr=subprocess.STDOUT, env=env, check=True, timeout=1800)
            text = log.read_text()
            rows = [json.loads(line) for line in text.splitlines() if line.startswith('{')]
            if len(rows) != 16 or any(row.get('bitwise_equal') is not True for row in rows):
                raise ValueError('state comparison count or output differs')
            if 'PASS: 16 full-vocabulary state comparisons;' not in text:
                raise ValueError('state probe is incomplete')
            markers = quality.MARKER.findall(text)
            requested = (0, 3) if mode in (1, 3) else (0,)
            activation = {}
            for request in requested:
                selected = ['K1_SSM_CONV mode=%s layout=%s rs=%s cpu_only=%s tokens=%s requested=%s' % row
                            for row in markers if int(row[-1]) == request]
                activation[str(request)] = quality.check_activation('\n'.join(selected), request)
            if any(int(row[0]) != 0 for row in markers if row[2] == '3'):
                raise ValueError('RS fallback activation differs')
            if mode in (2, 3) and 'SPINE_GDN_PREFILL: scalar-gate K1 RVV fusion enabled' not in text:
                raise ValueError('GDN activation is absent')
            records.append({'model': model, 'comparisons': rows, 'activation': activation,
                            'log_sha256': board.digest(log), 'reused': reused,
                            'source_log': str(previous_log) if reused else str(log)})
        return records

    def qualification(arm):
        identity = {'library_sha256': board.digest(library/'libggml-cpu.so'),
                    'model_library_sha256': board.digest(library/'libllama.so'),
                    'server_sha256': board.digest(server),
                    'models_sha256': {m: board.digest(v['path']) for m, v in expected['models'].items()}}
        if identity['models_sha256'] != {m: v['sha256'] for m, v in expected['models'].items()}:
            raise ValueError('model changed')
        data = {'identity': identity, 'qualified_arms': [arm], 'numeric_passed': True,
                'state_passed': True, 'operators_passed': True,
                'state_evidence': summary['arms'][arm]['state'],
                'operator_evidence': str(screen/'summary.json')}
        path = root/(arm+'-qualification.json')
        path.write_text(json.dumps(data, indent=2)+'\n')
        return path

    def compare(arm, lock, reference='C0', single_results=None):
        save('cold requests '+arm+' versus '+reference)
        arguments = argparse.Namespace(destination=root/(arm+'-vs-'+reference), candidate=arm,
            reference=reference, execute=True, lock=lock_path, library=library, server=server,
            model_2b=Path(expected['models']['2B']['path']), model_4b=Path(expected['models']['4B']['path']),
            qualification=qualification(arm), single_results=single_results or [])
        return prefill.compare(arguments, benchmark_lock=lock)

    save('wait for shared experiment lock')
    with lock_path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            quality = prefill.prepare.module('state_quality', prefill.prepare.HERE.parent/'k1-ssm-quality.py')
            verify()
            if args.reuse_model_gates:
                previous_root = args.reuse_model_gates.resolve()
                previous = json.loads((previous_root/'summary.json').read_text())
                if previous.get('status') != 'model-screen-complete':
                    raise ValueError('previous model screen is incomplete')
                for arm in ('C1', 'C2'):
                    if arm not in args.arms and arm in previous['arms']:
                        entry = previous['arms'][arm]
                        if entry.get('status') == 'eligible':
                            identity = entry['result']['identity']
                            if identity['library_sha256'] != board.digest(library/'libggml-cpu.so') or identity['model_library_sha256'] != board.digest(library/'libllama.so'):
                                raise ValueError('previous library identity differs')
                            if identity['server_sha256'] != board.digest(server) or identity['models_sha256'] != {m: info['sha256'] for m, info in expected['models'].items()}:
                                raise ValueError('previous server or model identity differs')
                        summary['arms'][arm] = entry
                        single_results[arm] = previous_root/(arm+'-vs-C0/result.json')
            for arm, mode in (('C1', 1), ('C2', 2)):
                if arm not in args.arms:
                    continue
                rows = operators['candidates']['C']['operators'][arm]
                required = [row for row in rows if row['tokens'] == 32]
                if len(required) != 2 or not all(row['advance'] for row in required) or any(row['clear_regression'] for row in rows):
                    summary['arms'][arm] = {'status': 'operator-not-qualified'}
                    continue
                summary['arms'][arm] = {'status': 'state-running'}
                try:
                    summary['arms'][arm]['state'] = state(arm, mode)
                    result = compare(arm, lock)
                    summary['arms'][arm].update(status=result['status'], result=result)
                except Exception as exc:
                    summary['arms'][arm].update(status='failed', error=str(exc))
                    (root/(arm+'-failure.txt')).write_text(traceback.format_exc())
                save(arm+' gates complete')
            if all(summary['arms'].get(arm, {}).get('status') == 'eligible' for arm in ('C1', 'C2')):
                summary['arms']['C3'] = {'status': 'state-running'}
                try:
                    summary['arms']['C3']['state'] = state('C3', 3)
                    receipts = [single_results[arm] for arm in ('C1', 'C2')]
                    result = compare('C3', lock, single_results=receipts)
                    summary['arms']['C3'].update(status=result['status'], result=result)
                    if result['status'] == 'eligible':
                        scores = {arm: sum(row['metrics']['ttft']['reduction_pct'] for row in summary['arms'][arm]['result']['comparisons'] if row['outputs'] == 1) for arm in ('C1', 'C2')}
                        best = max(scores, key=scores.get)
                        summary['arms']['C3']['versus_best'] = compare('C3', lock, best, receipts)
                except Exception as exc:
                    summary['arms']['C3'].update(status='failed', error=str(exc))
                    (root/'C3-failure.txt').write_text(traceback.format_exc())
            verify()
            summary['status'] = 'model-screen-complete'
            if not any(arm.get('status') == 'eligible' for arm in summary['arms'].values()):
                summary['full_answers'] = 'not-eligible'
            save('model screen complete')
        except Exception as exc:
            summary.update(status='failed', error=str(exc))
            save('model campaign failed')
            traceback.print_exc()
            return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
