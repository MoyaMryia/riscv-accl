#!/usr/bin/env python3
"""核验周期事件的计数范围，不把属性请求等同于硬件能力。"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import statistics
from analyze import sha,write,seal
from importlib.util import spec_from_file_location,module_from_spec

HERE=Path(__file__).resolve().parent
spec=spec_from_file_location('fit',HERE/'fit-k1-profile.py');fit=module_from_spec(spec);spec.loader.exec_module(fit)


def main(a):
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    rows=[json.loads(x) for x in a.samples.read_text().splitlines()];groups=defaultdict(list)
    expected={(exclude,kind,rep,n) for exclude in (False,True) for kind in (0,1) for rep in range(7) for n in (128,512,2048)}
    actual=[(r['exclude_kernel_requested'],r['kind'],r['repeat'],r['iterations']) for r in rows]
    if set(actual)!=expected or len(actual)!=len(expected):raise ValueError('特权级核验样本矩阵不完整。')
    if any(not r['valid'] or r['enabled']!=r['running'] or r['enabled']<=0 for r in rows):raise ValueError('计数器核验样本无效。')
    for r in rows:groups[r['exclude_kernel_requested'],r['kind']].append(r)
    records=[]
    for (exclude,kind),samples in groups.items():
        slopes={}
        for field in ('instructions','cycles','user_cycles','supervisor_cycles','machine_cycles'):
            values=[fit.linear([(s['iterations'],s[field]) for s in samples if s['repeat']==rep])['slope'] for rep in range(7)]
            slopes[field]=dict(median=statistics.median(values),replicates=values)
        records.append(dict(exclude_kernel_requested=exclude,kind=kind,slopes=slopes))
    index={(r['exclude_kernel_requested'],r['kind']):r['slopes'] for r in records}
    syscall=index[True,1];user=index[True,0];all_modes=index[False,1]
    med=lambda d,key:d[key]['median']
    generic_filter=abs(med(syscall,'instructions')-3)<.1
    partition=sum(med(all_modes,k) for k in ('user_cycles','supervisor_cycles','machine_cycles'))
    partition_error=abs(partition/med(all_modes,'cycles')-1)
    raw_valid=(med(user,'user_cycles')>0 and med(syscall,'user_cycles')/med(syscall,'cycles')<.1
        and med(all_modes,'supervisor_cycles')/med(all_modes,'cycles')>.8 and partition_error<.01)
    result=dict(schema=3,source_sha256=sha(a.samples),records=records,
        generic_user_instruction_filter_verified=generic_filter,
        raw_user_cycle_scope_verified=raw_valid,raw_user_cycle_event=dict(type='PERF_TYPE_RAW',config='0x22'),
        raw_partition_relative_error=partition_error,
        scope='CPU 0; current K1 board, kernel and firmware; known user loop and gettid loop',
        limits=['event labels originate from a frozen external event table',
                'the local privilege-mode test verifies the selected cycle scope only',
                'this audit does not verify all raw event names or a different board configuration',
                'generic cycles and instructions require separate scope labels',
                'keep old evidence unchanged; do not relabel old samples as raw U-mode cycles'])
    if not raw_valid:raise ValueError('原始用户态周期事件没有通过本机范围核验。')
    write(out/'audit.json',result);seal(out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('samples',type=Path)
    p.add_argument('--output',type=Path,required=True);main(p.parse_args())
