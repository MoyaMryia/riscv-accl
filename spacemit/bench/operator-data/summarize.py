#!/usr/bin/env python3
"""保留全部观测，汇总配对差值与执行长度斜率。"""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
import statistics


def file_hash(path):
    value=hashlib.sha256()
    with open(path,'rb') as handle:
        for block in iter(lambda:handle.read(1048576),b''):
            value.update(block)
    return value.hexdigest()


def slope(samples):
    xs = [s['calls'] for s in samples]
    ys = [s['wall_ms'] for s in samples]
    xbar, ybar = statistics.mean(xs), statistics.mean(ys)
    rate = math.fsum((x-xbar)*(y-ybar) for x,y in zip(xs,ys))/math.fsum((x-xbar)**2 for x in xs)
    return rate, ybar-rate*xbar


def summarize(root):
    state = json.loads((root/'state.json').read_text())
    if state['status']!='complete': raise ValueError('batch is not complete')
    files = json.loads((root/'sha256.json').read_text())
    for name, expected in files.items():
        if file_hash(root/name)!=expected: raise ValueError(f'file hash: {name}')
    frozen = json.loads((root/'frozen-artifacts.json').read_text())
    for name, expected in frozen.items():
        if file_hash(root/name)!=expected: raise ValueError(f'frozen artifact: {name}')
    identity = hashlib.sha256((root/'frozen-artifacts.json').read_bytes()).hexdigest()
    receipts = json.loads((root/'numeric-receipts.json').read_text())
    numeric = {r['case']['id']:r for r in receipts}
    for case_id, receipt in numeric.items():
        for arm in receipt['arms']:
            if file_hash(root/'numeric'/f'{case_id}-a{arm}.bin')!=receipt['sha256']: raise ValueError('numeric pair')
    plan = json.loads((root/'plan.json').read_text())
    split = state.get('split', 'train')
    if split not in ('train', 'calibration', 'test'): raise ValueError('split')
    groups = {g['id']:g for g in plan['groups']}
    cases = json.loads((root/('training-cases.json' if split=='train' else 'cases.json')).read_text())
    expected_cases = {f'{g["id"]}-t{t}':dict(g,id=f'{g["id"]}-t{t}',thread_count=t)
                      for g in plan['groups'] if g['split']==split for t in g['threads']}
    if len(cases)!=len(expected_cases) or {c['id']:c for c in cases}!=expected_cases: raise ValueError('planned cases')
    if len(receipts)!=len(cases) or set(numeric)!=set(expected_cases): raise ValueError('numeric coverage')
    data = collections.defaultdict(list)
    for line in (root/'observations.jsonl').read_text().splitlines():
        value = json.loads(line)
        case = value['case']
        if value['artifact_sha256']!=identity: raise ValueError('artifact identity')
        if value['numeric_sha256']!=numeric[case['id']]['sha256']: raise ValueError('numeric identity')
        if case!=expected_cases.get(case['id']): raise ValueError('observation case')
        if case['split']!=split: raise ValueError('split observation')
        group = groups[case['id'].rsplit('-t',1)[0]]
        if group['split']!=split or group['shape']!=case['shape']: raise ValueError('group identity')
        data[case['id']].append(value)
    if set(data)!={c['id'] for c in cases}: raise ValueError('case coverage')
    summary=[]
    worker_count=0
    for case in cases:
        values=data[case['id']]
        arms = [0,1] if case['family']=='ime' else [0,2]
        expected={(r,l,a) for r in range(7) for l in range(3) for a in arms}
        if len(values)!=42 or {(v['repeat'],v['length'],v['arm']) for v in values}!=expected: raise ValueError('row coverage')
        gains=[]
        for r in range(7):
            for l in range(3):
                pair={v['arm']:v for v in values if v['repeat']==r and v['length']==l}
                if pair[0]['calls']!=pair[arms[1]]['calls']: raise ValueError('paired call count')
                gains.append(100*(1-pair[arms[1]]['wall_ms']/pair[0]['wall_ms']))
        fits={}
        for arm in arms:
            rates=[]
            offsets=[]
            for r in range(7):
                rate,offset=slope([v for v in values if v['arm']==arm and v['repeat']==r])
                rates.append(rate)
                offsets.append(offset)
            fits[str(arm)]={'slope_ms_per_call':rates,'intercept_ms':offsets,
                'median_slope_ms_per_call':statistics.median(rates)}
        workers=[w for v in values for w in v['threads']] if case['family']=='ime' else []
        worker_count+=len(workers)
        for worker in workers:
            if worker['running']!=worker['enabled'] or worker['enabled']<=0: raise ValueError('counter coverage')
            if worker['cycles']<=0 or worker['instructions']<=0: raise ValueError('counter values')
        if case['family']=='ime':
            for value in values:
                if {w['cpu'] for w in value['threads']}!=set(range(case['thread_count'])): raise ValueError('worker identity')
        summary.append({'case':case,'rows':len(values),'paired_gain_percent_median':statistics.median(gains),
            'paired_gain_percent_min':min(gains),'paired_gain_percent_max':max(gains),
            'fits':fits,'involuntary_switches':sum(w['involuntary_switches'] for w in workers),
            'nonpositive_slope':any(x<=0 for f in fits.values() for x in f['slope_ms_per_call'])})
    result = {'schema':1,'status':'verified','measurement_scope':'hot-repeated-input',
        'prediction_confidence':None,'rows':sum(len(v) for v in data.values()),
        'cases':len(cases),'worker_samples':worker_count,'file_hashes_verified':len(files),
        'frozen_artifact_hashes_verified':len(frozen),'numeric_pairs_verified':len(receipts),
        'held_out_measured':split=='test','results':summary}
    if split!='train': result['split']=split
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('root',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    args.output.write_text(json.dumps(summarize(args.root),indent=2)+'\n')
