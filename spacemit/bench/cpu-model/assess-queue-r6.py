#!/usr/bin/env python3
"""分阶段核验第六轮冻结预测、校准与后测。"""
import argparse
from collections import defaultdict
import math
from pathlib import Path
import statistics
from audit import receipts
from common import digest,read,write
import model


def groups(plan,data,stage):
    index=defaultdict(list)
    for row in plan['records']:
        if row['split']==stage:index[row['group']].append(row)
    result=[]
    for name,rows in sorted(index.items()):
        if len(rows)!=4:raise ValueError('后测组不完整。')
        versions=[]
        for packets in (8,16):
            arms=sorted([r for r in rows if r['packets']==packets],key=lambda r:r['arm'])
            if len(arms)!=2 or [r['arm'] for r in arms]!=[0,1]:raise ValueError('两臂不完整。')
            ids=[r['id'] for r in arms];actual=[data['cycles'][i] for i in ids]
            predicted=[r['predicted_cycles'] for r in arms];old=[r['old_predicted_cycles'] for r in arms]
            ratio=predicted[1]/predicted[0];truth=actual[1]/actual[0];old_ratio=old[1]/old[0]
            repeat=[data['slopes'][ids[1]][k]/v for k,v in data['slopes'][ids[0]].items()]
            score=max([abs(math.log(p/a)) for p,a in zip(predicted,actual)]+[abs(math.log(ratio/truth))])
            versions.append(dict(packets=packets,unroll=packets,ids=ids,predicted_cycles=predicted,old_predicted_cycles=old,observed_cycles=actual,
                predicted_ratio=ratio,old_predicted_ratio=old_ratio,observed_ratio=truth,maximum_absolute_log_error=score,
                ratio_error_factor=math.exp(abs(math.log(ratio/truth))),gain_error_percentage_points=100*abs(ratio-truth),old_gain_error_percentage_points=100*abs(old_ratio-truth),
                direction_sign_agreement=((ratio>1)-(ratio<1))==((truth>1)-(truth<1)),observed_gain_below_one_percent=abs(truth-1)<.01,
                paired_repeat_ratio_range=[min(repeat),max(repeat)],repeat_range_crosses_one=min(repeat)<=1<=max(repeat),retained=True))
        result.append(dict(group=name,family=rows[0]['family'],kinds=rows[0]['kinds'],chains=rows[0]['chains'],gap=rows[0]['gap'],variants=versions,
            maximum_absolute_log_error=max(v['maximum_absolute_log_error'] for v in versions),retained=True))
    return result


def main(a):
    plan=read(a.plan);frozen=read(a.model);receipts(a.run)
    if digest(a.model)!=plan['model_sha256']:raise ValueError('模型身份不同。')
    if digest(Path(__file__).with_name('state6.py'))!=frozen['engine_files']['state6.py']:raise ValueError('冻结状态引擎不同。')
    if a.stage!='training' and digest(a.run/'frozen-model.json')!=digest(a.model):raise ValueError('板端模型身份不同。')
    data=model.observations(plan,a.run,a.stage);dump_checks=0
    index=defaultdict(list)
    for row in plan['records']:
        if row['split']==a.stage:index[row['group'],row['packets']].append(row)
    for rows in index.values():
        if len(rows)!=2:continue
        for n in plan['dump_lengths']:
            outputs=[(a.run/'dumps'/f'{r["id"]}-{n}.bin').read_bytes() for r in rows]
            if outputs[0]!=outputs[1]:raise ValueError('重排完整输出不同。')
            dump_checks+=1
    result=dict(schema=6,stage=a.stage,model_sha256=digest(a.model),plan_sha256=digest(a.plan),observations=data,complete_reorder_dump_pairs=dump_checks)
    if a.stage=='training':
        result.update(used_to_fit=False,controls=[dict(id=r['id'],predicted_cycles=r['predicted_cycles'],observed_cycles=data['cycles'][r['id']]) for r in plan['records'] if r['split']=='training'])
    else:
        records=groups(plan,data,a.stage);result['groups']=records
        if a.stage=='calibration':
            rank=math.ceil((len(records)+1)*.95)
            if rank>len(records):raise ValueError('校准组不足。')
            bound=sorted(r['maximum_absolute_log_error'] for r in records)[rank-1]
            result.update(rank=rank,log_bound=bound,factor=math.exp(bound),nominal_group_coverage=.95,
                assumption='固定候选范围内的组可交换性；没有确认总体覆盖率。')
        else:
            calibration=read(a.calibration)
            if calibration['model_sha256']!=digest(a.model) or digest(a.run/'frozen-calibration.json')!=digest(a.calibration):raise ValueError('校准身份不同。')
            flat=[v for r in records for v in r['variants']]
            for r in records:
                r['covered']=r['maximum_absolute_log_error']<=calibration['log_bound']
                for v in r['variants']:
                    v['covered']=v['maximum_absolute_log_error']<=calibration['log_bound']
                    v['ratio_interval']=[v['predicted_ratio']/calibration['factor'],v['predicted_ratio']*calibration['factor']]
            discernible=[v for v in flat if not v['observed_gain_below_one_percent'] and not v['repeat_range_crosses_one']]
            ranked=sorted(flat,key=lambda v:(v['predicted_ratio'],v['ids']))
            result.update(calibration_sha256=digest(a.calibration),group_count=len(records),groups_covered=sum(r['covered'] for r in records),versions=len(flat),versions_covered=sum(v['covered'] for v in flat),
                direction_sign_agreement=sum(v['direction_sign_agreement'] for v in flat),observed_gain_below_one_percent=sum(v['observed_gain_below_one_percent'] for v in flat),repeat_range_crosses_one=sum(v['repeat_range_crosses_one'] for v in flat),
                discernible_versions=len(discernible),discernible_direction_agreement=sum(v['direction_sign_agreement'] for v in discernible),observed_faster=sum(v['observed_ratio']<.99 for v in flat),observed_slower=sum(v['observed_ratio']>1.01 for v in flat),
                median_gain_error_percentage_points=statistics.median(v['gain_error_percentage_points'] for v in flat),maximum_gain_error_percentage_points=max(v['gain_error_percentage_points'] for v in flat),
                median_old_gain_error_percentage_points=statistics.median(v['old_gain_error_percentage_points'] for v in flat),maximum_old_gain_error_percentage_points=max(v['old_gain_error_percentage_points'] for v in flat),
                median_ratio_error_factor=statistics.median(v['ratio_error_factor'] for v in flat),maximum_ratio_error_factor=max(v['ratio_error_factor'] for v in flat),
                predicted_first_three=[dict(ids=v['ids'],predicted_ratio=v['predicted_ratio'],observed_ratio=v['observed_ratio']) for v in ranked[:3]],
                mean_observed_ratio_first_three=statistics.mean(v['observed_ratio'] for v in ranked[:3]))
    result['limits']=['全部候选继续保留。','配对重复范围不是预测置信区间。','固定范围的名义覆盖不是任意新算法精度。','本轮新数据没有用于拟合。']
    write(a.output,result)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',choices=['training','calibration','test'])
    for name in ('plan','model','run','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--calibration',type=Path);main(p.parse_args())
