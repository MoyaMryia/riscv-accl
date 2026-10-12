#!/usr/bin/env python3
"""在 tmux 内持锁测量已冻结的原型。"""
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import traceback


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            value.update(chunk)
    return value.hexdigest()


def comparison(base, candidate):
    if len(base) != 6 or len(candidate) != 6:
        raise ValueError('必须各有六个样本。')
    if any(not math.isfinite(x) or x <= 0 for x in base + candidate):
        raise ValueError('样本必须为有限正数。')
    mean = math.fsum(base) / 6
    gain = (1 - math.fsum(candidate) / 6 / mean) * 100
    spread = (max(base) - min(base)) / mean * 100
    return dict(reduction_percent=gain, control_range_percent=spread,
                automatic_action='none',purpose='investment priority; retain every candidate')


def validate_sample(sample, candidate, shape, arm):
    if (sample.get('candidate'), sample.get('shape'), sample.get('arm')) != (candidate, shape, arm):
        raise ValueError('计时记录的目标身份不一致。')
    count = sample.get('iterations')
    elapsed = sample.get('wall_ms')
    value = sample.get('ms_per_call')
    if type(count) is not int or not 0 < count <= 16777216:
        raise ValueError('重复次数无效。')
    if any(type(x) not in (int, float) or not math.isfinite(x) or x <= 0 for x in (elapsed, value)):
        raise ValueError('计时值必须为有限正数。')
    if elapsed < 100 or not math.isclose(elapsed / count, value, abs_tol=1e-9, rel_tol=1e-7):
        raise ValueError('计时值与重复次数不一致。')


def main():
    if len(sys.argv) != 2 or not os.environ.get('TMUX'):
        raise ValueError('必须在 tmux 内提供冻结载荷目录。')
    payload = Path(sys.argv[1]).resolve()
    os.chdir(payload)
    out = payload / 'run'
    out.mkdir()
    status = 1
    lock = open('/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/document-quality-suite.lock', 'w')
    try:
        (out / 'phase').write_text('waiting-lock\n')
        fcntl.flock(lock, fcntl.LOCK_EX)
        (out / 'phase').write_text('running\n')
        (out / 'tmux.log').write_text(os.environ['TMUX'] + '\n')
        subprocess.run(['sha256sum', '-c', 'SHA256SUMS'], stdout=(out / 'input-check.log').open('w'), check=True)
        def snapshot():
            paths = list(Path('/sys/class/thermal').glob('thermal_zone*/temp'))
            paths += list(Path('/sys/devices/system/cpu').glob('cpu[0-3]/cpufreq/scaling_cur_freq'))
            return {str(p): p.read_text().strip() for p in sorted(paths)}
        commands = []
        def run(label, args, library=None):
            env = os.environ.copy()
            if library:
                env['LD_LIBRARY_PATH'] = str(payload / library) + ':' + str(payload / 'common')
            before = snapshot()
            with (out / (label + '.log')).open('w') as log:
                result = subprocess.run(args, stdout=log, stderr=subprocess.STDOUT, env=env, timeout=120)
            commands.append(dict(label=label, argv=args, library=library,
                                 before=before, after=snapshot(), exit_status=result.returncode))
            (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
            if result.returncode:
                raise RuntimeError('测试退出：' + label)
            return (out / (label + '.log')).read_text()
        run('identity', ['uname', '-a'])
        run('conv-numeric', ['taskset', '-c', '0-3', './conv'])
        run('b2-original-numeric', ['taskset', '-c', '0-3', './test-b2', '--dump', str(out / 'b2-original.bin')], 'original')
        run('b2-candidate-numeric', ['taskset', '-c', '0-3', './test-b2', '--dump', str(out / 'b2-candidate.bin')], 'b2')
        if digest(out / 'b2-original.bin') != digest(out / 'b2-candidate.bin'):
            raise RuntimeError('B2 完整输出不一致。')
        run('ime-numeric', ['taskset', '-c', '0', './ime-native', str(out / 'ime.bin')])
        groups = [('conv', c, t, 1) for c, t in [(6144, 32), (8192, 32), (6144, 8), (8192, 8)]]
        groups += [('b2', k, h, tile) for tile in (8, 16) for k, h in [(2048, 8), (2048, 16), (256, 8), (256, 16)]]
        groups += [('ime-load-wrapper', 0, 0, 1)]
        results = []
        samples = []
        for index, (name, a, b, candidate) in enumerate(groups):
            values = {0: [], candidate: []}
            for block in range(6):
                arms = (0, candidate) if block % 2 == 0 else (candidate, 0)
                for arm in arms:
                    label = f'{index:02d}-{name}-{a}-{b}-block{block}-arm{arm}'
                    if name == 'conv':
                        args, library = ['taskset', '-c', '0-3', './conv', '--bench', str(a), str(b), str(arm)], None
                    elif name == 'b2':
                        args, library = ['taskset', '-c', '0-3', './test-b2', '--bench', str(a), str(b), str(arm)], 'b2'
                    else:
                        args, library = ['taskset', '-c', '0', './ime-native', '--bench', str(arm)], None
                    text = run(label, args, library)
                    records = [json.loads(line) for line in text.splitlines() if line.startswith('{')]
                    if len(records) != 1:
                        raise ValueError('计时记录不完整。')
                    shape = f'C{a}-T{b}' if name == 'conv' else f'K{a}-H{b}' if name == 'b2' else 'hot-2048-byte-input'
                    validate_sample(records[0], name, shape, arm)
                    sample = dict(records[0], block=block, label=label)
                    samples.append(sample)
                    values[arm].append(sample['ms_per_call'])
                    (out / 'samples.json').write_text(json.dumps(samples, indent=2) + '\n')
            results.append(dict(candidate=name, a=a, b=b, arm=candidate,
                                control=values[0], candidate_samples=values[candidate],
                                comparison=comparison(values[0], values[candidate])))
            (out / 'result.json').write_text(json.dumps(dict(schema=2, results=results,
                frozen_payload_manifest_sha256=digest(payload / 'SHA256SUMS'),
                sample_count=len(samples),
                automatic_performance_rejection=False,
                scope='isolated native prototypes; no full-model speed claim'), indent=2) + '\n')
        status = 0
    except Exception:
        (out / 'error.log').write_text(traceback.format_exc())
        raise
    finally:
        (out / 'phase').write_text('complete\n' if status == 0 else 'stopped\n')
        (out / 'exit-status').write_text(str(status) + '\n')
        files = sorted(p for p in out.rglob('*') if p.is_file() and p.name != 'SHA256SUMS')
        (out / 'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.relative_to(payload)}\n' for p in files))
        lock.close()


if __name__ == '__main__':
    main()
