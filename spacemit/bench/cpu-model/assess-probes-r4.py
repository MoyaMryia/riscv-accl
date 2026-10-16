#!/usr/bin/env python3
"""核对冻结探针预测与原生结果，并保留全部模型假设。"""
import argparse
from collections import defaultdict
import math
from pathlib import Path
import statistics
from audit import receipts
from common import digest,read,write
import model


def direction(value):
    return (value>1)-(value<1)


def main(a):
    plan=read(a.plan);prior=read(a.model)
    if digest(a.model)!=plan['prior_model_sha256']:raise ValueError('冻结模型身份不同。')
    receipts(a.run);observed=model.observations(plan,a.run,'training');probe_rows=[];pairs=defaultdict(list)
    for row in plan['records']:
        actual=observed['cycles'][row['id']]
        if row['role']=='mechanism-probe':
            low,high=row['hypothesis_range']
            probe_rows.append(dict(id=row['id'],candidate_id=row['candidate_id'],family=row['family'],type_order=row['type_order'],
                chains=row['chains'],gap=row['gap'],observed_cycles=actual,predicted_cycles=row['prior_cycles'],
                prior_error_factor=math.exp(abs(math.log(row['prior_cycles']/actual))),hypothesis_range=row['hypothesis_range'],
                outside_hypothesis_range=not low<=actual<=high,hypothesis_cycles=row['hypothesis_cycles']))
        else:pairs[row['group']].append(row)
    summary={}
    for family in ('WAW','WAR','RAW','vector-gap'):
        rows=[r for r in probe_rows if r['family']==family]
        summary[family]=dict(probes=len(rows),median_prior_error_factor=statistics.median(r['prior_error_factor'] for r in rows),
            maximum_prior_error_factor=max(r['prior_error_factor'] for r in rows),observations_outside_hypothesis_range=sum(r['outside_hypothesis_range'] for r in rows))
    variants=[dict(key='frozen',value=None)]+[dict(key=r['key'],value=r['value']) for r in prior['training_equivalent_single_parameter_variants']]
    hypothesis_scores=[]
    for index,variant in enumerate(variants):
        errors=[math.log(row['hypothesis_cycles'][index]/row['observed_cycles']) for row in probe_rows]
        hypothesis_scores.append(dict(index=index,**variant,retained=True,mean_squared_log_error=statistics.mean(e*e for e in errors),
            maximum_error_factor=math.exp(max(abs(e) for e in errors))))
    validation=[];dumps=0
    for name,rows in sorted(pairs.items()):
        rows=sorted(rows,key=lambda r:r['arm'])
        if len(rows)!=2 or [r['arm'] for r in rows]!=[0,1]:raise ValueError('冻结重排组不完整。')
        ids=[r['id'] for r in rows]
        for n in plan['dump_lengths']:
            paths=[a.run/'dumps'/f'{identifier}-{n}.bin' for identifier in ids]
            if paths[0].read_bytes()!=paths[1].read_bytes():raise ValueError('重排完整输出不同。')
            dumps+=1
        predicted=rows[1]['prior_cycles']/rows[0]['prior_cycles'];actual=observed['cycles'][ids[1]]/observed['cycles'][ids[0]]
        repeat=[observed['slopes'][ids[1]][key]/value for key,value in observed['slopes'][ids[0]].items()]
        validation.append(dict(group=name,kinds=rows[0]['kinds'],chains=rows[0]['chains'],packets=rows[0]['packets'],ids=ids,retained=True,
            predicted_cycles=[r['prior_cycles'] for r in rows],observed_cycles=[observed['cycles'][i] for i in ids],predicted_ratio=predicted,
            observed_ratio=actual,direction_sign_agreement=direction(predicted)==direction(actual),observed_gain_below_one_percent=abs(actual-1)<.01,
            paired_repeat_ratio_range=[min(repeat),max(repeat)],gain_error_percentage_points=100*abs(predicted-actual),
            ratio_error_factor=math.exp(abs(math.log(predicted/actual)))))
    budget=sorted(validation,key=lambda r:(r['predicted_ratio'],r['group']))[:3]
    write(a.output,dict(schema=1,plan_sha256=digest(a.plan),prior_model_sha256=digest(a.model),observations=observed,probe_summary=summary,
        probe_results=probe_rows,hypothesis_scores=sorted(hypothesis_scores,key=lambda r:r['mean_squared_log_error']),
        validation=validation,validation_summary=dict(groups=len(validation),direction_sign_agreement=sum(r['direction_sign_agreement'] for r in validation),
            observed_gain_below_one_percent=sum(r['observed_gain_below_one_percent'] for r in validation),observed_faster=sum(r['observed_ratio']<.99 for r in validation),
            median_gain_error_percentage_points=statistics.median(r['gain_error_percentage_points'] for r in validation),maximum_gain_error_percentage_points=max(r['gain_error_percentage_points'] for r in validation),
            median_ratio_error_factor=statistics.median(r['ratio_error_factor'] for r in validation),complete_reorder_dump_pairs=dumps,
            predicted_first_three=[dict(group=r['group'],observed_ratio=r['observed_ratio']) for r in budget],
            mean_observed_ratio_of_predicted_first_three=statistics.mean(r['observed_ratio'] for r in budget)),
        prediction_confidence=None,limits=['假设分歧范围不是预测置信区间。','主动选测的探针不能代表全部程序的误差分布。',
            '本批数据不重新拟合第三轮模型。','固定标量重排不是任意真实算法的独立验证。','旧校准界限没有转用于本批。','全部假设与算法候选保留。']))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan',type=Path,required=True);p.add_argument('--run',type=Path,required=True)
    p.add_argument('--model',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    main(p.parse_args())
