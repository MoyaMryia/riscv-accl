#!/usr/bin/env python3
"""列出全部重排对照的投入顺序，并保留误差范围。"""
import argparse
from itertools import combinations
from pathlib import Path
import statistics
from common import digest,read,write


def main(a):
    model=read(a.model);calibration=read(a.calibration);evaluation=read(a.evaluation)
    identity=digest(a.model)
    if calibration['model_sha256']!=identity or evaluation['model_sha256']!=identity or evaluation['calibration_sha256']!=digest(a.calibration):
        raise ValueError('模型、界限与后测身份不同。')
    rows=[]
    for group in evaluation['groups']:
        for version in group['variants']:
            low,high=version['ratio_interval']
            action='优先在板端验证预计改进' if high<1 else '保留对照，优先定位预计成本来源' if low>1 else '优先补测能区分机制的实验'
            rows.append(dict(group=group['group'],unroll=version['unroll'],kinds=group['kinds'],chains=group['chains'],
                predicted_ratio=version['predicted_ratio'],ratio_interval=version['ratio_interval'],
                observed_ratio=version['observed_ratio'],retained=True,next_action=action))
    predicted=sorted(rows,key=lambda r:(r['predicted_ratio'],r['group'],r['unroll']))
    actual=sorted(rows,key=lambda r:(r['observed_ratio'],r['group'],r['unroll']))
    for rank,row in enumerate(predicted,1):row['predicted_priority']=rank
    for rank,row in enumerate(actual,1):row['observed_priority']=rank
    concordant=discordant=ties=0
    for left,right in combinations(rows,2):
        p=left['predicted_ratio']-right['predicted_ratio']
        t=left['observed_ratio']-right['observed_ratio']
        if p==0 or t==0:ties+=1
        elif p*t>0:concordant+=1
        else:discordant+=1
    result=dict(schema=1,model_sha256=identity,rows=predicted,ranking=dict(concordant_pairs=concordant,discordant_pairs=discordant,tied_pairs=ties),
        fixed_budget_example=dict(versions=3,predicted_first_three=[dict(group=r['group'],unroll=r['unroll'],observed_ratio=r['observed_ratio']) for r in predicted[:3]],
            mean_observed_ratio_of_predicted_first_three=statistics.mean(r['observed_ratio'] for r in predicted[:3]),
            mean_observed_ratio_of_observed_first_three=statistics.mean(r['observed_ratio'] for r in actual[:3])),
        limits=['后测排序是本次受控循环的描述结果。','同组展开版本相关，不能称为独立算法样本。','等权版本比值不表示真实任务收益。','误差界限依赖原校准范围与分组假设。','全部对照保留。'])
    write(a.output,result)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model',type=Path,required=True)
    p.add_argument('--calibration',type=Path,required=True)
    p.add_argument('--evaluation',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    main(p.parse_args())
