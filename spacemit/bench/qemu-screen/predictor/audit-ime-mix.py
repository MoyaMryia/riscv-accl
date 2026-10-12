#!/usr/bin/env python3
"""核验 IME 混合轨迹的实际工作量、向量配置与原生数值散列。"""
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
from analyze import load, write, sha


def audit(payload, traces, result, receipt):
    plan = load(payload/'plan.json')
    if result['status'] != 'complete' or result['plan_sha256'] != sha(payload/'plan.json'):
        raise ValueError('实际轨迹尚未完成或计划身份不同。')
    native = {Path(line[66:]).stem: line[:64] for line in receipt.read_text().splitlines() if line.endswith('.bin')}
    expected = {r['id'] for r in plan['records']}
    if set(native) != expected:
        raise ValueError('原生数值转储矩阵不同。')
    checked = []
    for row in result['records']:
        definition = next(r for r in plan['records'] if r['id']==row['id'])
        root = traces/row['id']/str(row['loops'])/'program'
        meta = load(root/'program.json')
        if not meta['complete'] or sha(root/'operations.json') != meta['operations_sha256']:
            raise ValueError('实际成本程序不完整或操作身份不同。')
        operations = load(root/'operations.json')
        counts = Counter()
        for thread in meta['threads']:
            path = root/thread['file']
            if sha(path) != thread['sha256']:
                raise ValueError('实际压缩轨迹身份不同。')
            with gzip.open(path, 'rt') as stream:
                for line in stream:
                    event = json.loads(line)
                    op = operations[event[0]]
                    word = int(op['encoding'],16)
                    if op['family']=='ime-known-encoding':
                        counts['dots'] += 1
                        c = op['context']
                        if (c['sew'],c['lmul'],c['vl']) != (8,'1',32) or op['gaps']:
                            raise ValueError('IME 实际向量配置或语义不同。')
                    if op['name']=='vle8.v':
                        counts['loads'] += 1
                        if sum(m[1] for m in event[2]) != 32 or any(m[2] for m in event[2]):
                            raise ValueError('实际字节加载流量不同。')
                    if word == 0x00138393:
                        counts['gaps'] += 1
        required = row['loops']*definition['operations']
        if (counts['dots'],counts['loads'],counts['gaps']) != (required,2*required,definition['gap']*required):
            raise ValueError('实际混合工作量与计划不同。')
        if row['loops']==2 and row['dump_sha256'] != native[row['id']]:
            raise ValueError('原生与 QEMU 完整数值转储不同。')
        checked.append(dict(id=row['id'],loops=row['loops'],**counts))
    expected_traces = {(r['id'],n) for r in plan['records'] for n in plan['trace_lengths']}
    if len(checked) != len(expected_traces) or {(r['id'],r['loops']) for r in checked} != expected_traces:
        raise ValueError('实际轨迹矩阵不完整。')
    return dict(schema=7,status='verified',native_numeric_dumps=len(native),actual_traces=len(checked),
        plan_sha256=sha(payload/'plan.json'),records=checked,all_numeric_equal=True)


if __name__=='__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--payload',type=Path,required=True)
    p.add_argument('--traces',type=Path,required=True)
    p.add_argument('--native-receipt',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():p.error('输出文件必须不存在。')
    write(a.output,audit(a.payload,a.traces,load(a.traces/'results.json'),a.native_receipt))
