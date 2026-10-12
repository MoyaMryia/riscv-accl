#!/usr/bin/env python3
"""整理访存模式的有效载荷吞吐率，不推断 DDR 实际流量。"""
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import statistics
from analyze import load,write,sha,seal


def summarize(samples,plan_path,out):
    plan=load(plan_path);rows=[json.loads(x) for x in samples.read_text().splitlines()]
    expected={(m,t,s,r) for m in range(5) for t in plan['threads'] for s in plan['spans_bytes'] for r in range(plan['repetitions'])}
    actual=[(x['mode'],x['active_threads'],x['span_bytes_per_buffer'],x['repeat']) for x in rows]
    if set(actual)!=expected or len(actual)!=len(expected):raise ValueError('访存模式样本矩阵不完整。')
    groups=defaultdict(list);frequencies=set()
    for row in rows:
        if not row['valid'] or not math.isfinite(row['wall_ms']) or row['wall_ms']<=0 or row['passes']<=0:raise ValueError('访存样本无效。')
        n=row['active_threads'];mode=row['mode'];span=row['span_bytes_per_buffer']
        payload=span*row['passes']*n*(2 if mode==2 else 3 if mode==4 else 1)
        if row['payload_bytes']!=payload or len(row['threads'])!=n or {t['cpu'] for t in row['threads']}!=set(range(n)):
            raise ValueError('访存有效载荷或线程范围不同。')
        for t in row['threads']:
            if t['enabled']!=t['running'] or min(t['cycles'],t['instructions'],t['enabled'])<=0:raise ValueError('访存计数器无效。')
            frequencies.update((t['frequency_before_khz'],t['frequency_after_khz']))
        groups[mode,n,span].append(row)
    records=[]
    for (mode,n,span),values in sorted(groups.items()):
        rates=[x['payload_bytes']/x['wall_ms']/1e6 for x in values]
        records.append(dict(mode=mode,name=plan['modes'][str(mode)],threads=n,span_bytes_per_buffer=span,
            payload_gigabytes_per_second=statistics.median(rates),replicate_rates=rates,
            measurement_range=[min(rates),max(rates)],samples=len(values),
            effective_span_factor=4 if mode==3 else 6 if mode==4 else 2 if mode==2 else 1))
    result=dict(schema=3,records=records,samples=len(rows),configurations=len(records),
        samples_sha256=sha(samples),plan_sha256=sha(plan_path),frequency_snapshots_khz=sorted(frequencies),
        source_counter_scope=plan.get('counter',dict(type='PERF_TYPE_HARDWARE',scope='legacy generic cycle filter is not reliable')),
        estimate_scope='wall-time payload throughput for fixed patterns; arrays reset before each sample',
        limits=plan['limits']+['measurement ranges are not unseen-algorithm prediction confidence intervals',
            'large spans can use one pass; repeated passes do not establish a warm steady state',
            'the wall-time rates remain usable when legacy PMU privilege filtering is not reliable'])
    write(out/'memory-profile.json',result)
    lines=['# K1 访存模式实测','','吞吐率按架构有效载荷计算，不表示 DDR 实际流量。',
           '重复测量范围不是新算法的预测置信区间。','',
           '| 模式 | 线程数 | 基础跨度／字节 | 有效载荷吞吐率／GB/s | 测量范围／GB/s |',
           '| --- | ---: | ---: | ---: | --- |']
    for r in records:
        lo,hi=r['measurement_range'];lines.append(f'| {r["mode"]} | {r["threads"]} | {r["span_bytes_per_buffer"]} | {r["payload_gigabytes_per_second"]:.3f} | {lo:.3f} 至 {hi:.3f} |')
    lines+=['','模式 0 为连续向量读取。模式 1 为连续向量写入。',
        '模式 2 为连续向量复制。模式 3 为步长 16 的向量读取。',
        '模式 4 包含连续输入、步长 16 的权重、向量乘法和连续输出。',
        '模式 3 的数组跨度为基础跨度的 4 倍。',
        '模式 4 的全部数组跨度为基础跨度的 6 倍。',
        '每个工作线程使用独立数组。数据包含循环和栅栏成本。','']
    (out/'report.md').write_text('\n'.join(lines));seal(out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('samples',type=Path);p.add_argument('--plan',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    summarize(a.samples,a.plan,a.output)
