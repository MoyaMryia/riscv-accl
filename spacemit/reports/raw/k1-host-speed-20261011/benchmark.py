#!/usr/bin/env python3
"""测量固定筛选批次的宿主耗时，不测量 K1 耗时。"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import socket
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
WORK = Path(__file__).resolve().parent
OUT = WORK/('run-'+sys.argv[1])
OUT.mkdir(exist_ok=False)
plan = WORK/'plan.json'
result = {'status': 'running', 'hostname': socket.gethostname(), 'started_utc':
    datetime.datetime.now(datetime.timezone.utc).isoformat(), 'cases_per_batch': 40,
    'runs': [], 'plan_sha256': hashlib.sha256(plan.read_bytes()).hexdigest(),
    'parallel_sha256': hashlib.sha256((ROOT/'spacemit/bench/qemu-screen/parallel.py').read_bytes()).hexdigest(),
    'batch_sha256': hashlib.sha256((ROOT/'spacemit/bench/qemu-screen/batch.py').read_bytes()).hexdigest(),
    'cpuinfo': Path('/proc/cpuinfo').read_text(), 'load_before': os.getloadavg(),
    'K1_performance': 'unverified'}

def save():
    (OUT/'result.json').write_text(json.dumps(result, indent=2)+'\n')

def run(name, jobs):
    target = OUT/name
    command = [sys.executable, str(ROOT/'spacemit/bench/qemu-screen/parallel.py'), str(target),
        '--plan', str(plan), '--cores-per-job', '4', '--max-jobs', str(jobs)]
    started = time.monotonic()
    subprocess.run(command, check=True, timeout=300)
    elapsed = time.monotonic()-started
    child = json.loads((target/'result.json').read_text())
    if child['status'] != 'screen-complete-needs-board' or len(child['cases']) != 40:
        raise RuntimeError('screen status differs')
    return {'name': name, 'jobs_requested': jobs, 'maximum_active_jobs': child['maximum_active_jobs'],
        'wall_seconds': elapsed, 'cases_per_second': 40/elapsed}

try:
    for mode, jobs in [('warm-serial', 1), ('warm-parallel', 5)]:
        result.setdefault('warmup', []).append(run(mode, jobs))
        save()
    for repeat in range(3):
        order = [('serial', 1), ('parallel', 5)]
        if repeat % 2:
            order.reverse()
        for mode, jobs in order:
            result['runs'].append(run(f'{mode}-{repeat+1}', jobs))
            save()
    result['median_seconds'] = {mode: statistics.median(r['wall_seconds'] for r in result['runs']
        if r['name'].startswith(mode+'-')) for mode in ('serial', 'parallel')}
    result['parallel_speedup'] = result['median_seconds']['serial']/result['median_seconds']['parallel']
    result['load_after'] = os.getloadavg()
    result['status'] = 'complete'
finally:
    save()
    files = sorted(p for p in OUT.rglob('*') if p.is_file() and not p.is_symlink()
        and p.name != 'BENCHMARK-SHA256SUMS')
    (OUT/'BENCHMARK-SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+
        str(p.relative_to(OUT))+'\n' for p in files))
print(json.dumps({key: value for key, value in result.items() if key != 'cpuinfo'}, indent=2))
