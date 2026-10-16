#!/usr/bin/env python3
"""按训练机制记录冻结模型误差，不修改参数。"""
import argparse
from collections import defaultdict
import math
from pathlib import Path
import statistics
from common import digest,read,write


def main(a):
    plan=read(a.plan);frozen=read(a.model)
    if digest(a.plan)!=frozen['plan_sha256']:raise ValueError('计划与冻结模型不同。')
    groups=defaultdict(list);rows=[]
    for row in plan['records']:
        if row['split']!='training':continue
        predicted=frozen['predictions'][row['id']];observed=frozen['training']['cycles'][row['id']]
        error=abs(math.log(predicted/observed))
        record=dict(id=row['id'],group=row['group'],mode=row['mode'],kinds=row['kinds'],chains=row['chains'],unroll=row['unroll'],arm=row['arm'],
            operations=len(row['instructions']),predicted_cycles=predicted,observed_cycles=observed,absolute_log_error=error,
            error_factor=math.exp(error),predicted_relative_error=predicted/observed-1)
        rows.append(record);groups[row['mode']].append(record)
    summary={name:dict(functions=len(records),mean_squared_log_error=statistics.mean(r['absolute_log_error']**2 for r in records),
        median_error_factor=statistics.median(r['error_factor'] for r in records),maximum_error_factor=max(r['error_factor'] for r in records)) for name,records in groups.items()}
    write(a.output,dict(model_sha256=digest(a.model),summary=summary,rows=sorted(rows,key=lambda r:r['absolute_log_error'],reverse=True),
        limits=['训练误差不代表独立预测精度。','记录不修改模型、界限或候选状态。']))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan',type=Path,required=True);p.add_argument('--model',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    main(p.parse_args())
