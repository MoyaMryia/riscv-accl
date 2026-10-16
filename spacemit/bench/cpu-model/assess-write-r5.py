#!/usr/bin/env python3
"""检查冻结重复写入模型，并保留全部机制误差。"""
import argparse
from collections import defaultdict
import math
from pathlib import Path
import statistics
from audit import receipts
from common import digest,read,write
import model


def error(predicted,actual):return math.exp(abs(math.log(predicted/actual)))


def main(a):
    plan=read(a.plan);receipts(a.run)
    observed=model.observations(plan,a.run,'training')
    rows=[];groups=defaultdict(list)
    for row in plan['records']:
        actual=observed['cycles'][row['id']]
        rows.append(dict(id=row['id'],group=row['group'],family=row['family'],chains=row['chains'],gap=row.get('gap'),operand_position=row.get('operand_position'),
            observed_cycles=actual,predicted_cycles=row['predicted_cycles'],old_predicted_cycles=row['old_predicted_cycles'],
            new_error_factor=error(row['predicted_cycles'],actual),old_error_factor=error(row['old_predicted_cycles'],actual),retained=True))
        groups[row['group']].append(row)
    summary={}
    for family in ('RAW','WAR','WAW','reorder'):
        subset=[r for r in rows if r['family']==family]
        summary[family]=dict(functions=len(subset),median_new_error_factor=statistics.median(r['new_error_factor'] for r in subset),maximum_new_error_factor=max(r['new_error_factor'] for r in subset),
            median_old_error_factor=statistics.median(r['old_error_factor'] for r in subset),maximum_old_error_factor=max(r['old_error_factor'] for r in subset))
    pairs=[];dumps=0
    for name,records in sorted(groups.items()):
        if len(records)==1:continue
        records=sorted(records,key=lambda r:r['arm'])
        if len(records)!=2 or [r['arm'] for r in records]!=[0,1]:raise ValueError('配对组不完整。')
        ids=[r['id'] for r in records]
        for n in plan['dump_lengths']:
            outputs=[(a.run/'dumps'/f'{i}-{n}.bin').read_bytes() for i in ids]
            if outputs[0]!=outputs[1]:raise ValueError('配对完整输出不同。')
            dumps+=1
        actual=observed['cycles'][ids[1]]/observed['cycles'][ids[0]]
        predicted=records[1]['predicted_cycles']/records[0]['predicted_cycles']
        old=records[1]['old_predicted_cycles']/records[0]['old_predicted_cycles']
        repeat=[observed['slopes'][ids[1]][k]/v for k,v in observed['slopes'][ids[0]].items()]
        pairs.append(dict(group=name,family=records[0]['family'],type_order=records[0].get('type_order'),chains=records[0]['chains'],gap=records[0].get('gap'),ids=ids,
            observed_ratio=actual,predicted_ratio=predicted,old_predicted_ratio=old,paired_repeat_ratio_range=[min(repeat),max(repeat)],repeat_range_crosses_one=min(repeat)<=1<=max(repeat),
            observed_change_below_one_percent=abs(actual-1)<.01,direction_agreement=((predicted>1)-(predicted<1))==((actual>1)-(actual<1)),
            new_gain_error_percentage_points=100*abs(predicted-actual),old_gain_error_percentage_points=100*abs(old-actual),retained=True))
    reorder=[r for r in pairs if r['family']=='reorder'];swaps=[r for r in pairs if r['family']!='reorder']
    write(a.output,dict(schema=5,plan_sha256=digest(a.plan),model_sha256=plan['model_sha256'],prior_model_sha256=plan['prior_model_sha256'],observations=observed,
        functions=rows,mechanism_summary=summary,pairs=pairs,complete_pair_dump_checks=dumps,
        source_swap_summary=dict(pairs=len(swaps),changes_below_one_percent=sum(r['observed_change_below_one_percent'] for r in swaps),
            minimum_observed_ratio=min(r['observed_ratio'] for r in swaps),maximum_observed_ratio=max(r['observed_ratio'] for r in swaps),
            maximum_absolute_change_percentage_points=100*max(abs(r['observed_ratio']-1) for r in swaps)),
        reorder_summary=dict(groups=len(reorder),observed_faster=sum(r['observed_ratio']<.99 for r in reorder),direction_agreement=sum(r['direction_agreement'] for r in reorder),
            median_new_gain_error_percentage_points=statistics.median(r['new_gain_error_percentage_points'] for r in reorder),maximum_new_gain_error_percentage_points=max(r['new_gain_error_percentage_points'] for r in reorder),
            median_old_gain_error_percentage_points=statistics.median(r['old_gain_error_percentage_points'] for r in reorder),maximum_old_gain_error_percentage_points=max(r['old_gain_error_percentage_points'] for r in reorder)),
        prediction_confidence=None,limits=['第五轮观测没有用于本轮拟合。','本批不是独立真实算法族。','操作数交换没有差异不能排除其他读取机制。','配对重复范围不是预测置信区间。','全部候选保留。']))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('plan','run','output'):p.add_argument('--'+name,type=Path,required=True)
    main(p.parse_args())
