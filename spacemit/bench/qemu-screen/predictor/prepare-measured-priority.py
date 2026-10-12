#!/usr/bin/env python3
"""把板端配对区块转换为投入优先级输入，不设性能门槛。"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
from analyze import write,sha


def prepare(source,output):
    groups=defaultdict(dict)
    for sample in json.loads(source.read_text()):
        identity=(sample['candidate'],sample['shape'],sample['label'].split('-',1)[0])
        arms=groups[identity];arm=sample['arm'];block=sample['block']
        if block in arms.setdefault(arm,{}):raise ValueError('配对区块重复。')
        arms[arm][block]=sample['ms_per_call']
    records=[]
    for (name,shape,experiment),arms in groups.items():
        for arm in sorted(set(arms)-{0}):
            if set(arms[0])!=set(arms[arm]):raise ValueError('测量区块不完整。')
            blocks=sorted(arms[0]);workload=name+'-'+shape
            baseline='same-candidate-library-tile0' if name=='b2' else 'frozen-original-path'
            records.append(dict(id=workload+'-arm'+str(arm),workload=workload,baseline_id=baseline,
                kind='measured',control=[arms[0][b] for b in blocks],candidate=[arms[arm][b] for b in blocks],
                coverage=dict(gaps=['isolated fixture; no full-model speed claim'])))
    if not records:raise ValueError('没有完整测量对照。')
    write(output,dict(schema=2,source_sha256=sha(source),records=records,interval_coverage=.9))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('samples',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.samples,a.output)
