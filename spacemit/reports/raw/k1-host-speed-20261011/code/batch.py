#!/usr/bin/env python3
"""按固定计划执行数值检查与指令检查，不派发板端任务。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import time

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(plan_path, out):
    plan_path, out = plan_path.resolve(), out.resolve()
    plan = json.loads(plan_path.read_text())
    if plan['schema'] != 1 or not plan['cases']: raise ValueError('plan schema differs')
    out.mkdir(parents=True, exist_ok=False)
    result = {'schema': 1, 'plan_sha256': sha(plan_path), 'scope': plan['scope'],
        'host_affinity': sorted(os.sched_getaffinity(0)),
        'K1_performance': 'unverified', 'cases': [], 'status': 'running', 'commands': []}
    start = time.monotonic()

    def save():
        result['host_seconds'] = time.monotonic()-start
        (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')

    def execute(argv, label, timeout):
        argv = list(map(str, argv))
        log = out/(label+'.log')
        record = {'argv': argv, 'log': str(log.relative_to(out))}
        result['commands'].append(record); save()
        with log.open('w') as stream:
            try:
                status = subprocess.run(argv, stdout=stream, stderr=subprocess.STDOUT, timeout=timeout).returncode
            except subprocess.TimeoutExpired:
                status = 'timeout'
        record['returncode'] = status; save()
        return status

    try:
        for path, expected in plan['sources'].items():
            if sha(path) != expected: raise ValueError('source identity differs: '+path)
        plugin = out/'metrics.so'
        result['tool_sha256'] = {p: sha(p) for p in (plan['qemu'], plan['header'], plan['nm'], str(HERE/'metrics.c'))}
        if execute([plan['qemu'], '--version'], 'qemu-version', 10) != 0: raise RuntimeError('QEMU unavailable')
        flags = shlex.split(subprocess.check_output(['pkg-config', '--cflags', '--libs', 'glib-2.0'], text=True))
        if execute(['cc', '-std=c11', '-O2', '-shared', '-fPIC', '-fvisibility=hidden', '-Wall', '-Wextra', '-Werror',
            '-I'+str(Path(plan['header']).parent), HERE/'metrics.c', '-o', plugin, *flags], 'plugin-build', 30) != 0:
            raise RuntimeError('plugin build failed')
        result['plugin_sha256'] = sha(plugin)
        ids = set()
        for case in plan['cases']:
            name = case['id']
            if not re.fullmatch(r'[A-Za-z0-9_-]+', name) or name in ids: raise ValueError('case id invalid')
            ids.add(name)
            record = {'id': name, 'arms': {}, 'status': 'running'}
            result['cases'].append(record); save()
            for arm in ('control', 'candidate'):
                item = case[arm]
                elf = Path(item['elf'])
                if sha(elf) != item['sha256']: raise ValueError('ELF identity differs')
                symbols = subprocess.check_output([plan['nm'], '-S', '--defined-only', elf], text=True)
                matched = [line.split() for line in symbols.splitlines() if line.split()[-1] == item['symbol']]
                if len(matched) != 1: raise ValueError('ROI symbol is not unique')
                first, length = int(matched[0][0], 16), int(matched[0][1], 16)
                if not length: raise ValueError('empty ROI')
                dump = out/f'{name}-{arm}.bin'
                metrics = out/f'{name}-{arm}.json'
                args = [arg.replace('{dump}', str(dump)) for arg in item['args']]
                if not any('{dump}' in arg for arg in item['args']): raise ValueError('dump argument absent')
                option = f'{plugin},start={first:#x},end={first+length:#x},out={metrics}'
                code = execute([plan['qemu'], '-cpu', plan['cpu'], '-plugin', option, elf, *args],
                    f'{name}-{arm}', plan['timeout_seconds'])
                if code != 0:
                    record['status'] = 'control-execution-failed' if arm == 'control' else (
                        'unsupported-instruction' if code == -4 else 'candidate-execution-failed')
                    result['status'] = 'stopped'; save(); return
                if not dump.is_file() or not dump.stat().st_size: raise ValueError('complete dump absent')
                data = json.loads(metrics.read_text())
                if data['overflow'] or not data['cpus']: raise ValueError('metrics overflow or empty ROI')
                if len(data['cpus']) != case['roi_threads']: raise ValueError('ROI thread count differs')
                total = {key: sum(c[key] for c in data['cpus']) for key in data['cpus'][0] if key != 'cpu'}
                record['arms'][arm] = {'dump_sha256': sha(dump), 'dump_bytes': dump.stat().st_size,
                    'metrics': total, 'roi_threads': len(data['cpus']), 'pc_range': [first, first+length]}
                save()
            control, candidate = (record['arms'][key] for key in ('control', 'candidate'))
            if control['dump_sha256'] != candidate['dump_sha256']:
                record['status'] = 'rejected-numeric-difference'; result['status'] = 'stopped'; save(); return
            record['status'] = 'needs-board'
            record['interpretation'] = 'instruction and memory changes are signals; no K1 speed verdict'
            record['change_percent'] = {
                key: 100*(candidate['metrics'][key]/value-1) for key, value in control['metrics'].items() if value}
            save()
        result['status'] = 'screen-complete-needs-board'
    except Exception as error:
        result.update(status='fixture-failed', error=str(error))
        raise
    finally:
        save()
        (out/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(out.iterdir())
            if p.is_file() and p.name != 'SHA256SUMS'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    main(args.plan, args.output)
