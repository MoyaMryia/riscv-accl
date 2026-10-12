#!/usr/bin/env python3
"""Run two fixed B1-r2 repeats and collect complete paired answers."""
import fcntl
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import traceback

import board
import prefill

HERE = Path(__file__).resolve().parent
model = prefill.prepare.module('repeat_b1_model', HERE/'model-b1.py')
answers = prefill.prepare.module('repeat_b1_answers', HERE/'complete_answers_b1.py')


def main():
    root, initial, screen = (Path(p).resolve() for p in sys.argv[1:4])
    plan = json.loads((root/'repeat-protocol.json').read_text())
    expected = json.loads((screen/'expected-provenance.json').read_text())
    pilot = json.loads((initial/'summary.json').read_text())
    library = initial/'lib'
    server = next(Path(p) for p in expected['artifacts_sha256'] if p.endswith('/llama-server'))
    lock_path = Path.home()/'Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock'
    summary = {'revision': 'B1-r2', 'status': 'running', 'repeats': [], 'full_answers': 'pending',
               'identity': pilot['identity']}
    commands = []

    def save(phase):
        (root/'phase').write_text(phase+'\n')
        (root/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
        print(phase, flush=True)

    def verify():
        if plan['repeats'] != 2 or plan['order'] != ['B0', 'B1', 'B1', 'B0']:
            raise ValueError('repeat protocol differs')
        for path, value in plan['fixed_files_sha256'].items():
            if board.digest(path) != value:
                raise ValueError('fixed file changed: '+path)
        if pilot['status'] != 'model-screen-eligible' or len(pilot['comparisons']) != 8:
            raise ValueError('initial model gate is incomplete')
        if not all(row['passed'] for row in pilot['comparisons']):
            raise ValueError('initial model gate fails')
        for path, value in json.loads((screen/'baseline-before.json').read_text()).items():
            if board.digest(path) != value:
                raise ValueError('baseline changed: '+path)
        identity = pilot['identity']
        for path, key in [(library/'libggml-cpu.so', 'candidate_cpu_sha256'),
                          (library/'libllama.so', 'model_library_sha256'),
                          (server, 'server_sha256'), (server.parent/'libggml-cpu.so', 'original_cpu_sha256')]:
            if board.digest(path) != identity[key]:
                raise ValueError('binary identity differs: '+str(path))
        for name, info in expected['models'].items():
            if board.digest(info['path']) != info['sha256'] or identity['models'][name] != info:
                raise ValueError('model identity differs')
            saved = pilot['state'][name]
            if len(saved) != 3 or len({v['dump_sha256'] for v in saved.values()}) != 1:
                raise ValueError('initial state paths differ')
            for arm, receipt in saved.items():
                if len(receipt['rows']) != 40 or not all(r['bitwise_equal'] for r in receipt['rows']):
                    raise ValueError('initial state gate is incomplete')
                for suffix, key in [('.bin', 'dump_sha256'), ('.log', 'log_sha256')]:
                    if board.digest(initial/(name+'-'+arm+'-state'+suffix)) != receipt[key]:
                        raise ValueError('initial state evidence changed')

    def run(command, label, arm):
        environment = answers.environment(arm, library)
        commands.append({'argv': list(map(str, command)), 'label': label,
                         'runtime': {k: v for k, v in environment.items()
                                     if k.startswith('SPINE_') or k == 'LD_LIBRARY_PATH'}})
        (root/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
        with (root/(label+'.log')).open('w') as output:
            subprocess.run(list(map(str, command)), env=environment, stdout=output,
                           stderr=subprocess.STDOUT, timeout=700, check=True)

    save('wait for shared experiment lock')
    with lock_path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            os.environ['LD_LIBRARY_PATH'] = expected['runtime']['LD_LIBRARY_PATH']
            verify()
            for repeat in (1, 2):
                cold = root/('repeat-'+str(repeat)); cold.mkdir()
                result = {'independent_repeat': repeat, 'status': 'running', 'comparisons': []}
                summary['repeats'].append(result)
                for tokens in [512, 2048]:
                    for name, info in expected['models'].items():
                        for outputs in [1, 65]:
                            records, labels = [], []
                            for index, arm in enumerate([0, 1, 1, 0]):
                                label = f'{name}-p{tokens}-n{outputs}-B{arm}-{index}'
                                labels.append(label)
                                save('repeat '+str(repeat)+' '+label)
                                data, log = cold/(label+'.jsonl'), cold/(label+'.server.log')
                                command = [sys.executable, HERE.parent/'bench-lifecycle.py', '--server', server,
                                    '--model', info['path'], '--label', label, '--mode', 'plain', '--contexts', str(tokens),
                                    '--n-predict', str(outputs), '--ignore-eos', '--verify-cold', '--capture-token-ids',
                                    '--threads', '4', '--batch-size', '32', '--ubatch-size', '32', '--gpu-layers', '0',
                                    '--ctx-size', '4096', '--cache-type-k', 'f16', '--cache-type-v', 'f16',
                                    '--timeout', '600', '--output', data, '--log', log]
                                run(command, 'r'+str(repeat)+'-'+label, arm)
                                model.activation(log.read_text(), arm, info['shape']['heads'], arm == 1 and outputs == 65)
                                records.extend(json.loads(line) for line in data.read_text().splitlines())
                            try:
                                requests = prefill.FAST.check_model_records(records, labels, tokens, outputs)
                            except ValueError as exc:
                                if str(exc) != 'output or input tokens differ across arms':
                                    raise
                                result['status'] = 'cold-token-difference'
                                summary.update(status='cold-token-difference', full_answers='not-eligible')
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
                            result['comparisons'].append({'model': name, 'tokens': tokens, 'outputs': outputs,
                                                          'metrics': metrics, 'passed': passed})
                            (cold/'result.json').write_text(json.dumps(result, indent=2)+'\n')
                            if not passed:
                                result['status'] = 'model-gate-stopped'
                                (cold/'result.json').write_text(json.dumps(result, indent=2)+'\n')
                                summary.update(status='repeat-gate-stopped', full_answers='not-eligible')
                                verify(); save('repeat gate stopped; preserve the result')
                                return 0
                result['status'] = 'eligible'
                (cold/'result.json').write_text(json.dumps(result, indent=2)+'\n')
                verify(); save('repeat '+str(repeat)+' passed')
            def expired(signum, frame):
                raise TimeoutError('complete-answer request budget expired')

            signal.signal(signal.SIGALRM, expired)
            signal.signal(signal.SIGTERM, expired)
            save('complete paired answers')
            answers.collect(root/'complete-answers', server.parents[2], server, expected, library, 'B1')
            verify()
            summary.update(status='complete-answers-generated; review-pending',
                           full_answers='review-pending', baseline_preserved=True)
            save('complete paired answers generated; review pending')
        except BaseException as exc:
            summary.update(status='failed', error=str(exc))
            (root/'failure.txt').write_text(traceback.format_exc())
            save('B1-r2 repeat campaign failed')
            raise
    return 0


if __name__ == '__main__':
    sys.exit(main())
