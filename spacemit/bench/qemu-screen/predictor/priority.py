"""比较收益倾向、区间和证据强度，不执行性能淘汰。"""
import math
import random
import statistics
from collections import defaultdict
from analyze import load, sha, write


def positive(value):
    if type(value) not in (int,float) or not math.isfinite(value) or value<=0:
        raise ValueError('耗时或周期必须为有限正数。')
    return value


def quantile(values, probability):
    values=sorted(values);index=(len(values)-1)*probability
    lo=int(index);hi=min(lo+1,len(values)-1)
    return values[lo]*(hi-index)+values[hi]*(index-lo) if hi!=lo else values[lo]


def conformal(validation, model_sha256, confidence, query_group, domain):
    if validation is None:return None,dict(status='no-independent-calibration',groups=0)
    if validation['model_sha256']!=model_sha256:raise ValueError('误差样本属于另一模型。')
    if validation['domain']!=domain:raise ValueError('误差样本属于另一适用范围。')
    training=set(validation['training_groups']);scores=defaultdict(list)
    if query_group in training:raise ValueError('待预测组与训练集重叠。')
    for row in validation['records']:
        if row['group'] in training:raise ValueError('误差校准集与训练集重叠。')
        if row['group']==query_group:raise ValueError('待预测组与误差校准集重叠。')
        if not row.get('scope_matched',False):continue
        predicted=positive(row['predicted_ratio']);actual=positive(row['measured_ratio'])
        scores[row['group']].append(abs(math.log(actual/predicted)))
    values=sorted(max(v) for v in scores.values())
    rank=math.ceil((len(values)+1)*confidence)
    meta=dict(groups=len(values),nominal_coverage=confidence,order_statistic=rank,
              target='future paired fixture measurement; no noiseless hardware-mean coverage claim',
              assumption='independent exchangeable workload groups; domain and model identity must match',
              observed_max_log_ratio_error=max(values) if values else None)
    if not values or rank>len(values):return None,dict(meta,status='too-few-independent-groups')
    return values[rank-1],dict(meta,status='finite-calibrated-error-bound')


def rank(plan_path,out):
    plan=load(plan_path);confidence=plan.get('interval_coverage',.90)
    if not .5<confidence<1:raise ValueError('区间覆盖率必须位于 0.5 与 1 之间。')
    validation=load(plan['validation']) if plan.get('validation') else None
    records=[];identities=set();rng=random.Random(plan.get('seed',42))
    for source in plan['records']:
        identity=source['id']
        if identity in identities:raise ValueError('候选标识重复。')
        identities.add(identity)
        coverage=source['coverage'];gaps=coverage.get('gaps',[])
        baseline=source['baseline_id']
        if not isinstance(baseline,str) or not baseline:raise ValueError('必须声明基准标识。')
        fraction=coverage.get('calibrated_instruction_fraction',0)
        if type(fraction) not in (int,float) or not math.isfinite(fraction) or not 0<=fraction<=1:
            raise ValueError('标定覆盖率必须位于 0 与 1 之间。')
        record=dict(id=identity,workload=source['workload'],kind=source['kind'],coverage=coverage,
                    baseline_id=baseline,automatic_action='none',interval_coverage_requested=confidence)
        if source['kind']=='measured':
            a=source['control'];b=source['candidate']
            if len(a)!=len(b) or len(a)<2:raise ValueError('测量必须包含至少两个完整配对区块。')
            ratios=[math.log(positive(y)/positive(x)) for x,y in zip(a,b)]
            center=statistics.mean(ratios)
            draws=sorted(statistics.mean(rng.choices(ratios,k=len(ratios))) for _ in range(4096))
            alpha=(1-confidence)/2
            low,high=quantile(draws,alpha),quantile(draws,1-alpha)
            record.update(expected_gain=1-math.exp(center),gain_interval=[1-math.exp(high),1-math.exp(low)],
                interval_kind='paired-block-bootstrap-measurement-interval',sample_blocks=len(a),
                evidence_level='measured-this-fixture',
                confidence_limits=['few blocks may understate drift','does not validate a host prediction model'],
                estimator='geometric mean of paired time ratios')
        elif source['kind']=='predicted':
            scenarios=source['scenarios']
            if not scenarios:raise ValueError('预测必须包含至少一个声明的场景。')
            names=[s['name'] for s in scenarios]
            if len(set(names))!=len(names):raise ValueError('预测场景标识重复。')
            ratios=[positive(s['candidate_cycles'])/positive(s['control_cycles']) for s in scenarios]
            center=statistics.median(math.log(r) for r in ratios)
            error,meta=conformal(validation,source['model_sha256'],confidence,source['group'],source['domain'])
            complete=(coverage.get('trace_complete') is True and coverage.get('scope_matched') is True
                      and coverage.get('calibrated_instruction_fraction',0)>=.98 and not gaps)
            bounds=[min(ratios),max(ratios)]
            if error is not None and complete:
                bounds=[bounds[0]*math.exp(-error),bounds[1]*math.exp(error)]
                kind='calibrated-prediction-interval-under-declared-assumptions';level='calibrated-in-domain'
            else:
                kind='declared-scenario-sensitivity-range';level='exploratory'
            record.update(expected_gain=1-math.exp(center),gain_interval=[1-bounds[1],1-bounds[0]],
                interval_kind=kind,evidence_level=level,validation=meta,
                faster_scenario_fraction=sum(r<1 for r in ratios)/len(ratios),
                scenario_fraction_limit='scenario fraction is not a probability of real speedup',
                scenario_names=names,confidence_limits=gaps or ['domain and residual exchangeability remain assumptions'])
        else:raise ValueError('未知证据类型。')
        lo,hi=record['gain_interval']
        record['direction']='faster' if lo>0 else 'slower' if hi<0 else 'uncertain'
        records.append(record)
    groups=defaultdict(list)
    for record in records:groups[(record['workload'],record['baseline_id'])].append(record)
    comparisons=[]
    for group,items in groups.items():
        items.sort(key=lambda r:r['expected_gain'],reverse=True)
        for position,r in enumerate(items,1):r['priority_rank_within_workload']=position
        for i,a in enumerate(items):
            for b in items[i+1:]:
                comparisons.append(dict(workload=group[0],baseline_id=group[1],a=a['id'],b=b['id'],
                    separated_intervals=a['gain_interval'][0]>b['gain_interval'][1],
                    limit='interval separation alone is not a simultaneous statistical test'))
    result=dict(schema=2,purpose='investment priority with uncertainty; no performance elimination',
        plan_sha256=sha(plan_path),validation_sha256=sha(plan['validation']) if validation else None,
        records=records,comparisons=comparisons,automatic_action='none',
        ranking_scope='compare only the same workload and declared baseline scope')
    write(out/'priority.json',result)
    lines=['# K1 算法投入优先级','','所有候选均保留。排序只用于安排投入和补测。',
           '排序只比较同一负载与基准范围，不能把独立收益相加。','',
           '| 负载 | 候选 | 组内顺序 | 中心收益 | 区间 | 区间类型 | 证据类型 |',
           '| --- | --- | ---: | ---: | --- | --- | --- |']
    for r in sorted(records,key=lambda r:(r['workload'],r['priority_rank_within_workload'])):
        lo,hi=r['gain_interval']
        lines.append(f'| {r["workload"]} | {r["id"]} | {r["priority_rank_within_workload"]} | {100*r["expected_gain"]:.3f}% | '
                     f'{100*lo:.3f}% 至 {100*hi:.3f}% | {r["interval_kind"]} | {r["evidence_level"]} |')
    lines+=['','声明场景的范围不具有统计置信度。',
            '模型误差区间需要同一模型、同一范围和独立工作负载组。',
            '测量区间只适用于当前夹具，不证明跨算法预测精度。',
            '区间重叠时，中心收益顺序仍可参考，但证据不能确认两者的先后关系。','']
    (out/'report.md').write_text('\n'.join(lines))
    return result
