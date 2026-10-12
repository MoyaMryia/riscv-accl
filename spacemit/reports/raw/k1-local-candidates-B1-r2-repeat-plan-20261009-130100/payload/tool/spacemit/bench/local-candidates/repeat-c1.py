#!/usr/bin/env python3
"""Run two declared C1 repeats, then collect complete paired answers."""
import fcntl
import json
import os
from pathlib import Path
import shutil
import signal
import sys
import traceback

import board
import prefill


def main():
    root, screen, initial = (Path(p).resolve() for p in sys.argv[1:4])
    summary = {'status': 'running', 'repeats': [], 'full_answers': 'pending'}
    expected = json.loads((screen/'expected-provenance.json').read_text())
    library = screen/'C/lib'
    server = next(Path(p) for p in expected['artifacts_sha256'] if p.endswith('/llama-server'))
    lock_path = Path.home()/'Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock'
    os.environ['LD_LIBRARY_PATH'] = expected['runtime']['LD_LIBRARY_PATH']

    def save(phase):
        (root/'phase').write_text(phase+'\n')
        (root/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
        print(phase, flush=True)

    def verify():
        for p, digest in json.loads((screen/'baseline-before.json').read_text()).items():
            if board.digest(p) != digest:
                raise ValueError('baseline changed: '+p)
        qualified = json.loads((initial/'C1-qualification.json').read_text())
        identity = {'library_sha256': board.digest(library/'libggml-cpu.so'),
                    'model_library_sha256': board.digest(library/'libllama.so'),
                    'server_sha256': board.digest(server),
                    'models_sha256': {model: board.digest(info['path']) for model, info in expected['models'].items()}}
        pilot = json.loads((initial/'C1-vs-C0/result.json').read_text())
        if qualified.get('identity') != identity or pilot.get('identity') != identity:
            raise ValueError('identity differs from the initial experiment')
        if pilot.get('status') != 'eligible' or len(pilot.get('comparisons', [])) != 8:
            raise ValueError('initial C1 gate is incomplete')
        if not all(row['passed'] for row in pilot['comparisons']):
            raise ValueError('initial C1 gate fails')
        if identity['models_sha256'] != {model: info['sha256'] for model, info in expected['models'].items()}:
            raise ValueError('model identity differs')
        return identity

    save('wait for shared experiment lock')
    with lock_path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            save('verify repeat prerequisites')
            quality = prefill.prepare.module('repeat_quality', prefill.prepare.HERE.parent/'k1-ssm-quality.py')
            plan = json.loads((root/'repeat-protocol.json').read_text())
            if plan['repeats'] != 2 or plan['order_per_cell'] != ['C0', 'C1', 'C1', 'C0']:
                raise ValueError('repeat protocol differs')
            summary['identity'] = verify()
            for repeat in (1, 2):
                save('independent repeat '+str(repeat))
                args = type('Arguments', (), dict(destination=root/('repeat-'+str(repeat)),
                    candidate='C1', reference='C0', execute=True, lock=lock_path,
                    library=library, server=server,
                    model_2b=Path(expected['models']['2B']['path']),
                    model_4b=Path(expected['models']['4B']['path']),
                    qualification=initial/'C1-qualification.json', single_results=[]))()
                result = prefill.compare(args, benchmark_lock=lock)
                summary['repeats'].append(result)
                if result['status'] != 'eligible':
                    summary.update(status='repeat-gate-stopped', full_answers='not-eligible')
                    verify()
                    save('repeat gate stopped; preserve the result')
                    return 0
            verify()
            save('complete paired answers')
            answer_root = root/'complete-answers'
            answer_root.mkdir()
            shutil.copyfile(screen/'expected-provenance.json', answer_root/'expected-provenance.json')
            task = quality.Run(answer_root)
            task.server = server
            task.source = server.parents[2]
            task.build = task.source/'build'
            task.env = prefill.arm_env('C0', library)
            task.baseline_hashes = json.loads((screen/'baseline-before.json').read_text())
            task.summary.update(models={}, requests_completed=0, planned_requests=24,
                protocol={'candidate_mode': 3, 'threshold_per_sequence_tokens': 32, 'route': 3,
                    'mtp': False, 'threads': 4, 'batch': 32, 'ubatch': 32, 'context': 6144,
                    'document_budget': 2048, 'natural_stop': True, 'facts_output_guard': 512,
                    'code_prose_output_guard': 2048, 'requests_per_case_arm': 1,
                    'tasks': ['routes', 'trace', 'aggregation', 'free_windows', 'unicode_runs', 'chinese_policy'],
                    'order': {'2B': ['control', 'hybrid'], '4B': ['hybrid', 'control']},
                    'request_budget_s': 1800},
                limitations='One pair per task and model. Report absolute errors and candidate regressions separately.')

            def expired(signum, frame):
                raise TimeoutError('complete-answer request budget expired')

            signal.signal(signal.SIGALRM, expired)
            signal.signal(signal.SIGTERM, expired)
            try:
                for model in ('2B', '4B'):
                    save('complete paired answers '+model)
                    task.complete_model(model)
                verify()
                task.summary.update(status='generation completed; review pending', baseline_preserved=True)
                task.save()
            except BaseException as exc:
                task.summary.update(status='failed', reason=str(exc))
                task.save()
                raise
            summary.update(status='complete-answers-generated; review-pending',
                           full_answers='review-pending', baseline_preserved=True)
            save('complete paired answers generated; review pending')
        except BaseException as exc:
            summary.update(status='failed', error=str(exc))
            (root/'failure.txt').write_text(traceback.format_exc())
            save('repeat campaign failed')
            raise
    return 0


if __name__ == '__main__':
    sys.exit(main())
