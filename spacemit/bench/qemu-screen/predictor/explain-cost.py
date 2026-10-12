#!/usr/bin/env python3
"""归因声明调度器的等待，并检查依赖假设敏感性。"""
import argparse
from collections import Counter, defaultdict
import gzip
import json
import math
from pathlib import Path
from analyze import load, write, sha, seal
from k1cost import component, parameters, model_identity


def replay(path, operations, table, waw=True, memory_order=True):
    ready = {}
    ports = {}
    memory_ready = {}
    front = finished = 0.0
    slots = 0
    last_segment = None
    memo = {}
    charged = Counter()
    sites = defaultdict(Counter)
    count = 0
    for line in gzip.open(path, 'rt'):
        index, segment, memory = json.loads(line)
        op = operations[index]
        count += 1
        stride = memory[1][0]-memory[0][0] if op['name'] == 'vlse32.v' and len(memory)>1 else 0
        key = (index, stride, len(memory))
        if key not in memo:
            memo[key] = component(table, op, memory, 'central')
        latency, occupancy, port, source, gaps, parameter = memo[key]
        if segment != last_segment:
            if last_segment is not None:
                delta = max(front, finished)-front
                charged['segment-boundary'] += delta
                sites[index]['segment-boundary'] += delta
                front += delta
            ready = {}
            last_segment = segment
        accessed = {}
        memory_wait = 0.0
        if memory_order:
            for address, size, store in memory:
                for address_line in range(address//64, (address+size-1)//64+1):
                    read, written = memory_ready.get(address_line, (0.0, 0.0))
                    memory_wait = max(memory_wait, written, read if store else 0.0)
                    accessed[address_line] = accessed.get(address_line, False) or store
        choices = [(front, 'front'), (ports.get(port, 0.0), 'resource:'+port),
            (memory_wait, 'memory-order')]
        choices += [(ready.get(r, 0.0), 'register-RAW') for r in op['read']]
        if waw:
            choices += [(ready.get(r, 0.0), 'register-WAW') for r in op['write']]
        candidate, reason = max(choices, key=lambda item:item[0])
        if candidate > front:
            delta = candidate-front
            charged[reason] += delta
            sites[index][reason] += delta
            front = candidate
            slots = 0
        if slots >= 2:
            front += 1.0
            charged['issue-width'] += 1.0
            sites[index]['issue-width'] += 1.0
            slots = 0
        slots += 1
        complete = front+latency
        ports[port] = front+occupancy
        for r in op['write']:
            ready[r] = complete
        for address_line, store in accessed.items():
            read, written = memory_ready.get(address_line, (0.0, 0.0))
            memory_ready[address_line] = (read, complete) if store else (max(read, complete), written)
        finished = max(finished, complete)
    charged['completion-tail'] += finished-front
    if not math.isclose(sum(charged.values()), finished, rel_tol=1e-10, abs_tol=1e-6):
        raise ValueError('声明等待归因的周期总和不同。')
    rows = [dict(operation=i, pc=operations[i]['pc'], name=operations[i]['name'],
        charged_cycles=sum(values.values()), reasons=dict(values)) for i, values in sites.items()]
    return dict(instructions=count, estimated_component_cycles=finished, charged_cycles=dict(charged),
        sites=sorted(rows, key=lambda r:(-r['charged_cycles'], r['pc'])))


def explain(program, profiles):
    meta = load(program/'program.json')
    if not meta['complete'] or sha(program/'operations.json') != meta['operations_sha256']:
        raise ValueError('成本程序不完整或操作身份不同。')
    operations = load(program/'operations.json')
    table, identities = parameters(profiles)
    identity, definition = model_identity(identities)
    modes = [('default', True, True), ('hypothetical-no-WAW', False, True),
        ('hypothetical-no-memory-order', True, False), ('hypothetical-neither', False, False)]
    for thread in meta['threads']:
        if sha(program/thread['file']) != thread['sha256']:
            raise ValueError('轨迹身份不同。')
    records = []
    for name, waw, memory_order in modes:
        threads = {}
        for thread in meta['threads']:
            row = replay(program/thread['file'], operations, table, waw, memory_order)
            if row['instructions'] != thread['instructions']:
                raise ValueError('实际轨迹计数不同。')
            threads[thread['file']] = row
        values = [r['estimated_component_cycles'] for r in threads.values()]
        records.append(dict(name=name, cohort_cycles=max(values), serial_cycles=sum(values), threads=threads))
    return dict(schema=4, kind='declared-scheduler-wait-diagnosis', records=records,
        base_model_sha256=identity, base_model_definition=definition,
        implementation_sha256=sha(Path(__file__)), program_sha256=sha(program/'program.json'),
        limits=['wait charges partition the declared scheduler; they are not measured hardware stalls',
            'ties use a fixed order; charges do not establish causal hardware costs',
            'hypothetical modes remove constraints and do not describe verified K1 hardware',
            'memory order uses conservative virtual cache lines',
            'all modes omit capacity penalties, synchronization and external callees',
            'no new-algorithm prediction confidence or K1 wall-time claim'],
        automatic_action='none')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('program', type=Path)
    p.add_argument('--profiles', type=Path, nargs='+', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    write(a.output/'explanation.json', explain(a.program, a.profiles))
    seal(a.output)
