"""对六个固定开关组合执行两轮交错冷请求。"""
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import combined_common as common

ORDER = ['C0', 'H', 'L', 'P', 'B', 'F', 'F', 'B', 'P', 'L', 'H', 'C0']


def rules(metrics, candidate, reference, tokens, outputs):
    if (candidate, reference) in [('P', 'C0'), ('P', 'H')]:
        return (metrics['prefill']['advance'] and metrics['ttft']['advance']) if outputs == 1 else not metrics['decode']['clear_regression']
    if (candidate, reference) == ('P', 'L'):
        return all(not value['clear_regression'] for value in metrics.values())
    if (candidate, reference) == ('F', 'C0'):
        return (metrics['prefill']['advance'] and metrics['ttft']['advance']) if outputs == 1 else (
            metrics['decode']['advance'] if tokens == 2048 else not metrics['decode']['clear_regression'])
    if (candidate, reference) == ('F', 'P'):
        return (metrics['decode']['advance'] if tokens == 2048 and outputs == 65 else
                all(not value['clear_regression'] for value in metrics.values()))
    if (candidate, reference) == ('F', 'B'):
        return (metrics['prefill']['advance'] and metrics['ttft']['advance']) if outputs == 1 else not metrics['decode']['clear_regression']
    raise ValueError('unknown comparison')


def thread_snapshot(controller, server):
    pending, seen, output = [controller], set(), []
    while pending:
        pid = pending.pop()
        if pid in seen:
            continue
        seen.add(pid)
        base = Path('/proc')/str(pid)
        try:
            pending.extend(int(value) for value in (base/'task'/str(pid)/'children').read_text().split())
            if (base/'exe').resolve() != server.resolve():
                continue
            tasks = {p.name: (p/'status').read_text() for p in (base/'task').iterdir()}
            output.append({'pid': pid, 'status': (base/'status').read_text(), 'threads': tasks})
        except (OSError, ValueError):
            continue
    return output


def run_request(command, destination, label, env, server):
    snapshots = []
    start = time.monotonic()
    with (destination/(label+'.driver.log')).open('w') as stream:
        proc = subprocess.Popen(list(map(str, command)), stdout=stream, stderr=subprocess.STDOUT,
                                env=env, start_new_session=True)
        try:
            while proc.poll() is None:
                if time.monotonic()-start > 700:
                    raise TimeoutError('cold request budget expired')
                if not snapshots:
                    snapshots = thread_snapshot(proc.pid, server)
                    if snapshots:
                        (destination/(label+'.threads.json')).write_text(json.dumps(snapshots, indent=2)+'\n')
                time.sleep(1)
            if proc.returncode:
                raise subprocess.CalledProcessError(proc.returncode, command)
        finally:
            if proc.poll() is None or proc.returncode:
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait()
    if not snapshots:
        raise ValueError('cold server thread snapshot is absent')


def compare_round(root, number, run, identity):
    destination = root/('cold-round-'+str(number))
    destination.mkdir()
    result = {'round': number, 'status': 'running', 'order': ORDER,
              'identity': identity, 'comparisons': [], 'completed_requests': 0}

    def save():
        (destination/'result.json').write_text(json.dumps(result, indent=2)+'\n')

    for tokens in (512, 2048):
        for model in ('2B', '4B'):
            for outputs in (1, 65):
                records, labels = [], []
                for index, arm in enumerate(ORDER):
                    label = f'{model}-p{tokens}-n{outputs}-{arm}-{index}'
                    run.phase(f'cold round {number} {label}')
                    labels.append(label)
                    log = destination/(label+'.server.log')
                    data = destination/(label+'.jsonl')
                    argv = [sys.executable, common.prepare.HERE.parent/'bench-lifecycle.py',
                        '--server', run.server, '--model', run.expected['models'][model]['path'],
                        '--label', label, '--mode', 'plain', '--contexts', str(tokens),
                        '--n-predict', str(outputs), '--ignore-eos', '--verify-cold', '--capture-token-ids',
                        '--threads', '4', '--batch-size', '32', '--ubatch-size', '32', '--gpu-layers', '0',
                        '--ctx-size', '4096', '--cache-type-k', 'f16', '--cache-type-v', 'f16',
                        '--timeout', '600', '--output', data, '--log', log]
                    env = common.arm_env(arm, run.root/'C/lib', run.expected['runtime'])
                    config = {'argv': list(map(str, argv)), 'runtime': {k: v for k, v in env.items()
                              if k.startswith('SPINE_') or k == 'LD_LIBRARY_PATH'}}
                    (destination/(label+'.config.json')).write_text(json.dumps(config, indent=2)+'\n')
                    run_request(argv, destination, label, env, run.server)
                    common.activation(log.read_text(), arm, require_both=outputs == 65,
                        require_shared=outputs == 65 and arm in ('B', 'F'))
                    records.extend(json.loads(line) for line in data.read_text().splitlines())
                    result['completed_requests'] += 1
                    save()
                try:
                    requests = common.FAST.check_model_records(records, labels, tokens, outputs)
                except ValueError as exc:
                    if str(exc) == 'output or input tokens differ across arms':
                        raise common.NumericalStop(str(exc)) from exc
                    raise
                values = {arm: [r['results'][0] for r in requests if '-'+arm+'-' in r['label']] for arm in common.ARMS if arm != 'G'}
                if any(len(rows) != 2 for rows in values.values()):
                    raise ValueError('cold arm count differs')
                for candidate, reference in [('P', 'C0'), ('P', 'H'), ('P', 'L'), ('F', 'C0'), ('F', 'P'), ('F', 'B')]:
                    metrics = {}
                    for metric, key in [('prefill', 'prompt_ms'), ('ttft', None), ('decode', 'predicted_ms')]:
                        if metric == 'decode' and outputs == 1:
                            continue
                        times = {arm: [row['timings'][key] if key else row['ttft_ms'] for row in values[arm]] for arm in (reference, candidate)}
                        if any(not math.isfinite(value) or value <= 0 for rows in times.values() for value in rows):
                            raise ValueError('invalid phase time')
                        metrics[metric] = common.FAST.gate(times[reference], times[candidate])
                    passed = rules(metrics, candidate, reference, tokens, outputs)
                    result['comparisons'].append({'model': model, 'tokens': tokens, 'outputs': outputs,
                        'candidate': candidate, 'reference': reference, 'metrics': metrics, 'passed': passed})
                    if not passed:
                        result['status'] = 'performance-gate-stopped'
                        save()
                        return result
                save()
    result['status'] = 'eligible'
    save()
    return result
