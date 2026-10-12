#!/usr/bin/env python3
"""按宿主物理核心分组执行独立筛选用例，不估算 K1 耗时。"""
import argparse
from collections import defaultdict
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent


def cpu_list(text):
    cpus = set()
    for item in text.strip().split(','):
        if not item:
            continue
        limits = item.split('-')
        if len(limits) > 2:
            raise ValueError('CPU list has an invalid range')
        first, last = int(limits[0]), int(limits[-1])
        if first < 0 or last < first:
            raise ValueError('CPU list has an invalid range')
        cpus.update(range(first, last+1))
    return cpus


def topology():
    observed = {}

    def read(path, default=''):
        path = Path(path)
        value = path.read_text().strip() if path.is_file() else default
        observed[str(path)] = value
        return value

    performance = cpu_list(read('/sys/bus/event_source/devices/cpu_core/cpus'))
    efficiency = cpu_list(read('/sys/bus/event_source/devices/cpu_atom/cpus'))
    if performance & efficiency:
        raise ValueError('hybrid CPU classes overlap')
    allowed = set(os.sched_getaffinity(0))
    records = []
    for cpu in sorted(allowed):
        base = Path(f'/sys/devices/system/cpu/cpu{cpu}')
        nodes = sorted(int(p.name[4:]) for p in base.glob('node[0-9]*'))
        caches = []
        for index in sorted((base/'cache').glob('index*')):
            if read(index/'level') == '2' and read(index/'type') in ('Data', 'Unified'):
                caches.append(sorted(cpu_list(read(index/'shared_cpu_list'))))
        if len(caches) > 1:
            raise ValueError('L2 cache identity is ambiguous')
        records.append({'cpu': cpu, 'kind': 'P' if cpu in performance else 'E' if cpu in efficiency else 'unknown',
            'package': int(read(base/'topology/physical_package_id', '0')),
            'core': int(read(base/'topology/core_id', str(cpu))),
            'node': nodes[0] if len(nodes) == 1 else -1,
            'siblings': sorted(cpu_list(read(base/'topology/thread_siblings_list', str(cpu)))),
            'l2_shared': caches[0] if caches else [cpu]})
    return {'allowed_cpus': sorted(allowed), 'records': records, 'observations': observed,
        'cpuinfo': Path('/proc/cpuinfo').read_text(),
        'class_source': 'Linux hybrid PMU CPU sets; unknown when absent',
        'memory_note': 'core groups still share package memory and can share last-level cache'}


def groups(records, size, reserve):
    physical = {}
    for item in sorted(records, key=lambda x: x['cpu']):
        key = (item['package'], item['core'])
        if item['cpu'] not in reserve and not (set(item['siblings']) & reserve):
            physical.setdefault(key, item)
    pools = defaultdict(list)
    for item in physical.values():
        cache = tuple(item['l2_shared']) if item['kind'] == 'E' else ()
        pools[(item['kind'], item['package'], item['node'], cache)].append(item)
    result = []
    order = {'P': 0, 'E': 1, 'unknown': 2}
    for key in sorted(pools, key=lambda k: (order[k[0]], k[1:])):
        items = sorted(pools[key], key=lambda x: x['cpu'])
        for first in range(0, len(items)-size+1, size):
            chunk = items[first:first+size]
            result.append({'id': len(result), 'kind': key[0], 'package': key[1], 'node': key[2],
                'cpus': [x['cpu'] for x in chunk],
                'physical_cores': [[x['package'], x['core']] for x in chunk],
                'l2_groups': sorted({tuple(x['l2_shared']) for x in chunk})})
    return result


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(args):
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    host = topology()
    slots = groups(host['records'], args.cores_per_job, cpu_list(args.reserve_cpus))
    if args.max_jobs:
        slots = slots[:args.max_jobs]
    host['groups'] = slots
    host['unassigned_cpus'] = sorted(set(host['allowed_cpus'])-set(c for s in slots for c in s['cpus']))
    (out/'topology.json').write_text(json.dumps(host, indent=2)+'\n')
    result = {'schema': 1, 'status': 'topology-only', 'cases': [], 'maximum_active_jobs': 0,
        'K1_performance': 'unverified', 'host_timing_comparison': 'P and E results are not interchangeable',
        'source_sha256': sha(__file__), 'batch_sha256': sha(HERE/'batch.py')}
    active = {}
    start = time.monotonic()

    def save():
        result['host_seconds'] = time.monotonic()-start
        (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')

    def cancel():
        for proc, record, stream in active.values():
            if proc.poll() is None:
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
        for proc, record, stream in active.values():
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                proc.wait()
            stream.close()
            record.update(status='cancelled-after-stop', returncode=proc.returncode,
                host_seconds=time.monotonic()-record.pop('_start'))
        active.clear()

    def interrupted(signum, frame):
        raise InterruptedError('parallel controller received signal '+str(signum))

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        if not args.plan:
            save()
            return
        if not slots:
            raise ValueError('no complete physical core group is available')
        plan = json.loads(args.plan.read_text())
        if plan['schema'] != 1 or not plan['cases']:
            raise ValueError('plan schema differs')
        ids = [case['id'] for case in plan['cases']]
        if len(set(ids)) != len(ids) or any(not re.fullmatch(r'[A-Za-z0-9_-]+', name) for name in ids):
            raise ValueError('case identity is invalid')
        if any(case['roi_threads'] > args.cores_per_job for case in plan['cases']):
            raise ValueError('guest workers exceed the host core group size')
        pending = list(plan['cases'])
        result.update(status='running', plan_sha256=sha(args.plan), total_cases=len(pending))
        while pending or active:
            failed = False
            for slot_id, (proc, record, stream) in list(active.items()):
                code = proc.poll()
                if code is None:
                    continue
                stream.close()
                child_path = out/record['id']/'result.json'
                child = json.loads(child_path.read_text()) if child_path.is_file() else {}
                record.update(returncode=code, child_status=child.get('status'),
                    actual_affinity=child.get('host_affinity'), host_seconds=time.monotonic()-record.pop('_start'))
                ok = code == 0 and child.get('status') == 'screen-complete-needs-board'
                ok = ok and child.get('host_affinity') == record['group']['cpus']
                record['status'] = 'needs-board' if ok else 'stopped'
                del active[slot_id]
                if not ok:
                    failed = True
                    result['first_stop_case'] = result.get('first_stop_case', record['id'])
            if failed:
                result.update(status='stopped', unstarted_cases=[case['id'] for case in pending])
                cancel()
                save()
                return
            for slot in slots:
                if not pending or slot['id'] in active:
                    continue
                case = pending.pop(0)
                child_plan = copy.deepcopy(plan)
                child_plan['cases'] = [case]
                path = out/(case['id']+'-plan.json')
                path.write_text(json.dumps(child_plan, indent=2)+'\n')
                command = ['taskset', '-c', ','.join(map(str, slot['cpus'])), sys.executable,
                    str(HERE/'batch.py'), str(path), str(out/case['id'])]
                record = {'id': case['id'], 'group': slot, 'command': command, 'status': 'running',
                    '_start': time.monotonic()}
                result['cases'].append(record)
                stream = (out/(case['id']+'-driver.log')).open('w')
                try:
                    proc = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
                except Exception:
                    stream.close()
                    raise
                active[slot['id']] = (proc, record, stream)
            result['maximum_active_jobs'] = max(result['maximum_active_jobs'], len(active))
            save()
            time.sleep(0.05)
        result['status'] = 'screen-complete-needs-board'
    except BaseException as error:
        result.update(status='controller-failed', error=str(error))
        cancel()
        raise
    finally:
        save()
        files = sorted(p for p in out.rglob('*') if p.is_file() and not p.is_symlink() and p.name != 'PARALLEL-SHA256SUMS')
        (out/'PARALLEL-SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(out))+'\n' for p in files))
    print(out/'result.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--cores-per-job', type=int, default=4)
    parser.add_argument('--max-jobs', type=int)
    parser.add_argument('--reserve-cpus', default='')
    args = parser.parse_args()
    if args.cores_per_job < 1 or args.max_jobs is not None and args.max_jobs < 1:
        parser.error('core and job counts must be positive')
    main(args)
