#!/usr/bin/env python3
"""Run two declared C repeats, then collect complete paired answers."""
import fcntl
import json
import os
from pathlib import Path
import hashlib
import signal
import sys
import traceback

import board
import prefill
import complete_answers


def main():
    root, screen, initial = (Path(p).resolve() for p in sys.argv[1:4])
    candidate = sys.argv[4]
    if candidate not in ('C1', 'C2', 'C3'):
        raise ValueError('unknown C arm')
    summary = {'candidate': candidate, 'status': 'running', 'repeats': [], 'full_answers': 'pending'}
    expected = json.loads((screen/'expected-provenance.json').read_text())
    library = screen/'C/lib'
    server = next(Path(p) for p in expected['artifacts_sha256'] if p.endswith('/llama-server'))
    lock_path = Path.home()/'Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock'
    os.environ['LD_LIBRARY_PATH'] = expected['runtime']['LD_LIBRARY_PATH']
    references = ['C0']

    def save(phase):
        (root/'phase').write_text(phase+'\n')
        (root/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
        print(phase, flush=True)

    def verify():
        for p, digest in json.loads((screen/'baseline-before.json').read_text()).items():
            if board.digest(p) != digest:
                raise ValueError('baseline changed: '+p)
        qualified = json.loads((initial/(candidate+'-qualification.json')).read_text())
        identity = {'library_sha256': board.digest(library/'libggml-cpu.so'),
                    'model_library_sha256': board.digest(library/'libllama.so'),
                    'server_sha256': board.digest(server),
                    'models_sha256': {model: board.digest(info['path']) for model, info in expected['models'].items()}}
        pilot = json.loads((initial/(candidate+'-vs-C0/result.json')).read_text())
        if qualified.get('identity') != identity or pilot.get('identity') != identity:
            raise ValueError('identity differs from the initial experiment')
        if pilot.get('status') != 'eligible' or len(pilot.get('comparisons', [])) != 8:
            raise ValueError('initial candidate gate is incomplete')
        if not all(row['passed'] for row in pilot['comparisons']):
            raise ValueError('initial candidate gate fails')
        if candidate == 'C3':
            initial_summary = json.loads((initial/'summary.json').read_text())
            best = initial_summary['arms']['C3']['versus_best']
            if best.get('reference') != references[1] or best.get('status') != 'eligible':
                raise ValueError('C3 did not pass the best single-arm gate')
            receipt = json.loads((initial/('C3-vs-'+references[1])/'result.json').read_text())
            if (receipt.get('identity') != identity or receipt.get('status') != 'eligible'
                    or len(receipt.get('comparisons', [])) != 8
                    or not all(row['passed'] for row in receipt['comparisons'])):
                raise ValueError('C3 best single-arm receipt is incomplete')
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
            if plan['repeats'] != 2 or plan['order_per_cell'] != ['C0', candidate, candidate, 'C0'] or plan['candidate'] != candidate:
                raise ValueError('repeat protocol differs')
            if candidate == 'C3':
                references = plan['references']
                if len(references) != 2 or references[0] != 'C0' or references[1] not in ('C1', 'C2'):
                    raise ValueError('C3 repeat references differ')
            for name, key in (('repeat-protocol.md', 'protocol_sha256'),
                              ('tool/spacemit/bench/local-candidates/repeat-c.py', 'driver_sha256'),
                              ('tool/spacemit/bench/local-candidates/complete_answers.py', 'collector_sha256')):
                if hashlib.sha256((root/name).read_bytes()).hexdigest() != plan[key]:
                    raise ValueError('frozen protocol file differs: '+name)
            summary['identity'] = verify()
            for repeat in (1, 2):
                for reference in references:
                    save('independent repeat '+str(repeat)+' versus '+reference)
                    name = 'repeat-'+str(repeat)+('-vs-'+reference if candidate == 'C3' else '')
                    args = type('Arguments', (), dict(destination=root/name,
                        candidate=candidate, reference=reference, execute=True, lock=lock_path,
                        library=library, server=server,
                        model_2b=Path(expected['models']['2B']['path']),
                        model_4b=Path(expected['models']['4B']['path']),
                        qualification=initial/(candidate+'-qualification.json'),
                        single_results=[initial/(arm+'-vs-C0/result.json') for arm in ('C1', 'C2')] if candidate == 'C3' else []))()
                    result = prefill.compare(args, benchmark_lock=lock)
                    summary['repeats'].append(dict(result, independent_repeat=repeat))
                    if result['status'] != 'eligible':
                        summary.update(status='repeat-gate-stopped', full_answers='not-eligible')
                        verify()
                        save('repeat gate stopped; preserve the result')
                        return 0
            verify()
            save('complete paired answers')
            def expired(signum, frame):
                raise TimeoutError('complete-answer request budget expired')

            signal.signal(signal.SIGALRM, expired)
            signal.signal(signal.SIGTERM, expired)
            complete_answers.collect(root/'complete-answers', server.parents[2], server,
                                     expected, library, candidate)
            verify()
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
