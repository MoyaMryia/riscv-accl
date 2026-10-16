#!/usr/bin/env python3
"""拟合顺序发射状态模型，并冻结组合循环预测。"""
import argparse
from collections import defaultdict
import copy
import math
from pathlib import Path
import statistics
from common import digest, read, write

KINDS = ('add','mul','load','vadd','ime','vload')
INITIAL = dict(width=2,scalar_units=2,lsu_units=2,shared_vector=False,waw=True,
               latency=dict(add=1,mul=5,load=3,vadd=4,ime=4,vload=4),
               occupancy=dict(add=1,mul=1,load=1,vadd=1,ime=1,vload=1),
               read_hold_ime=0,vector_gap={'vadd:ime':1,'ime:vadd':1},
               bypass={'add:mul':1,'mul:add':5,'load:add':3,'load:mul':3})


def predict(record, parameters, loops=32):
    """重复循环并分离初始状态；不模拟缓存或错误路径。"""
    if loops < 8 or loops % 2:
        raise ValueError('循环数量必须为不小于 8 的偶数。')
    p = parameters
    ready = defaultdict(int)
    writers = {}
    read_until = defaultdict(int)
    last_vector = None
    resources = dict(scalar=[0]*p['scalar_units'],lsu=[0]*p['lsu_units'],vector=[0],ime=[0])
    clock = used = 0
    halfway = None
    ops = record['instructions'] + [dict(kind='add',reads=['ctr'],writes=['ctr']),dict(kind='branch',reads=['ctr'],writes=[])]
    for iteration in range(loops):
        if iteration == loops//2:
            halfway = clock
        for op in ops:
            kind = op['kind']
            resource = 'scalar' if kind in ('add','mul','branch') else 'lsu' if kind in ('load','vload') else 'vector' if kind=='vadd' or p['shared_vector'] else 'ime'
            pool = resources[resource]
            pool.sort()
            count = len(pool) if kind=='vload' else 1
            dependencies = []
            for r in op['reads']:
                if r in writers:
                    issued, producer = writers[r]
                    delay = p['bypass'].get(producer+':'+kind,p['latency'].get(producer,1))
                    dependencies.append(issued+delay)
            if p['waw']:
                dependencies.extend(ready[r] for r in op['writes'])
            dependencies.extend(read_until[r] for r in op['writes'])
            if kind in ('vadd','ime','vload') and last_vector:
                previous, issued = last_vector
                dependencies.append(issued+p['vector_gap'].get(previous+':'+kind,0))
            available = max([clock,pool[count-1]]+dependencies)
            if used == p['width'] and available == clock:
                available += 1
            if available != clock:
                used = 0
                clock = available
            latency = 1 if kind=='branch' else p['latency'][kind]
            occupancy = 1 if kind=='branch' else p['occupancy'][kind]
            for i in range(count):
                pool[i] = clock+occupancy
            for register in op['writes']:
                ready[register] = clock+latency
                writers[register] = clock,kind
            if kind=='ime':
                for register in op['reads']:
                    read_until[register]=max(read_until[register],clock+p['read_hold_ime'])
            if kind in ('vadd','ime','vload'):
                last_vector=kind,clock
            used += 1
            if kind=='branch':
                clock += 1
                used = 0
    return (clock-halfway)/(loops//2)


def observations(plan, run, split):
    run=Path(run)
    if (run/'exit-status').read_text().strip()!='0' or (run/'phase').read_text().strip()!='complete':
        raise ValueError('测量阶段没有完整结束。')
    for line in (run/'SHA256SUMS').read_text().splitlines():
        expected_hash,name=line.split('  ',1)
        path=run.parent/name
        if not path.resolve().is_relative_to(run.resolve()) or digest(path)!=expected_hash:
            raise ValueError('测量证据收据不符。')
    expected = {r['id'] for r in plan['records'] if r['split']==split}
    values = defaultdict(dict)
    switches = 0
    rows = 0
    frequencies = set()
    for session in (0,1):
        path = Path(run)/f'samples-{session}.jsonl'
        for line in path.read_text().splitlines():
            import json
            row = json.loads(line)
            rows += 1
            if not row['valid'] or row['id'] not in expected or row['cpu']!=plan['cpu'] or row['enabled']!=row['running']:
                raise ValueError('样本身份或计数器范围不符。')
            key = (row['id'],session,row['repeat'])
            if row['iterations'] in values[key]:
                raise ValueError('重复样本。')
            values[key][row['iterations']] = row['cycles']
            switches += row['involuntary_switches']+row['voluntary_switches']
            frequencies.update((row['frequency_before_khz'],row['frequency_after_khz']))
    slopes = defaultdict(list)
    detailed = defaultdict(dict)
    for identifier in sorted(expected):
        for session in (0,1):
            for repetition in range(plan['repetitions']):
                points = values[identifier,session,repetition]
                if set(points)!=set(plan['lengths']):
                    raise ValueError('循环长度或重复次数不完整。')
                xs,ys = list(points),list(points.values())
                xm,ym = statistics.mean(xs),statistics.mean(ys)
                slope = sum((x-xm)*(y-ym) for x,y in zip(xs,ys))/sum((x-xm)**2 for x in xs)
                if slope<=0:
                    raise ValueError('出现非正周期斜率。')
                slopes[identifier].append(slope)
                detailed[identifier][f'{session}-{repetition}'] = slope
    if rows!=len(expected)*2*plan['repetitions']*len(plan['lengths']):
        raise ValueError('样本数量不符。')
    return dict(cycles={k:statistics.median(v) for k,v in slopes.items()},slopes=dict(detailed),
                samples=rows,scheduling_switches=switches,frequency_snapshots_khz=sorted(frequencies))


def score(records, observed, parameters):
    errors = [math.log(predict(row,parameters)/observed[row['id']]) for row in records]
    return statistics.mean(e*e for e in errors)


def alternatives(parameters):
    for key in ('width','scalar_units','lsu_units'):
        for value in (1,2):
            candidate = copy.deepcopy(parameters)
            candidate[key] = value
            yield f'{key}={value}',candidate
    for key in ('shared_vector','waw'):
        for value in (False,True):
            candidate = copy.deepcopy(parameters)
            candidate[key] = value
            yield f'{key}={value}',candidate
    for value in (0,1,2,3,4,5,6,8):
        candidate=copy.deepcopy(parameters)
        candidate['read_hold_ime']=value
        yield f'read_hold_ime={value}',candidate
    for table in ('latency','occupancy','vector_gap','bypass'):
        for kind in parameters[table]:
            for value in (1,2,3,4,5,6,8,10,12,16):
                candidate = copy.deepcopy(parameters)
                candidate[table][kind] = value
                yield f'{table}.{kind}={value}',candidate


def fit(plan, data):
    records = [r for r in plan['records'] if r['split']=='training']
    p = copy.deepcopy(INITIAL)
    history = []
    current = score(records,data['cycles'],p)
    for round_number in range(24):
        best = current
        best_parameter = None
        best_name = None
        for name,candidate in alternatives(p):
            error = score(records,data['cycles'],candidate)
            if error < best-1e-10:
                best,best_parameter,best_name = error,candidate,name
        if best_parameter is None:
            break
        p = best_parameter
        history.append(dict(round=round_number,change=best_name,mean_squared_log_error=best))
        current = best
    convergence = max(abs(predict(row,p,128)/predict(row,p,32)-1) for row in plan['records'])
    if convergence>0.005:
        raise ValueError('循环状态尚未稳定。')
    equivalents=[]
    for name,candidate in alternatives(p):
        if candidate!=p and abs(score(records,data['cycles'],candidate)-current)<1e-8:
            equivalents.append(dict(change=name,parameters=candidate))
    return dict(schema=1,parameters=p,training_equivalent_single_parameter_variants=equivalents,training_mean_squared_log_error=current,fit_history=history,
        steady_state_32_vs_128_max_relative_difference=convergence,
        predictions={row['id']:predict(row,p,128) for row in plan['records']},
        training=data,limits=['effective parameters; hardware topology is not identified',
          'greedy discrete search; no global optimum claim',
          'whole-register dependencies; no lane-level timing model',
          'fixed hot loop and fixed input; no cache miss, branch recovery or wall-time prediction',
          'triple-operation holdout is not independent arbitrary-algorithm validation'])


def group_scores(plan,model,data,split):
    groups = defaultdict(list)
    for row in plan['records']:
        if row['split']==split:
            groups[row['group']].append(row)
    result=[]
    for name,arms in sorted(groups.items()):
        arms.sort(key=lambda r:r['arm'])
        if [r['arm'] for r in arms]!=[0,1]:
            raise ValueError('组合组缺少配对。')
        identifiers=[r['id'] for r in arms]
        pred=[model['predictions'][k] for k in identifiers]
        actual=[data['cycles'][k] for k in identifiers]
        ratio,truth=pred[1]/pred[0],actual[1]/actual[0]
        error=max([abs(math.log(p/a)) for p,a in zip(pred,actual)]+[abs(math.log(ratio/truth))])
        repeated=[data['slopes'][identifiers[1]][k]/value for k,value in data['slopes'][identifiers[0]].items()]
        result.append(dict(group=name,ids=identifiers,kinds=arms[0]['kinds'],chains=arms[0]['chains'],
            predicted_cycles=pred,observed_cycles=actual,predicted_ratio=ratio,observed_ratio=truth,
            maximum_absolute_log_error=error,ratio_error_factor=math.exp(abs(math.log(ratio/truth))),
            gain_error_percentage_points=100*abs(ratio-truth),
            direction_sign_agreement=((ratio>1)-(ratio<1))==((truth>1)-(truth<1)),
            predicted_direction='faster' if ratio<1 else 'slower' if ratio>1 else 'neutral',
            paired_repeat_ratio_range=[min(repeated),max(repeated)],
            repeat_range_crosses_one=min(repeated)<=1<=max(repeated)))
    return result


def calibrate(plan,model,data):
    groups=group_scores(plan,model,data,'calibration')
    rank=math.ceil((len(groups)+1)*0.95)
    if rank>len(groups):
        raise ValueError('校准组数量不足以形成有限界限。')
    bound=sorted(r['maximum_absolute_log_error'] for r in groups)[rank-1]
    return dict(schema=1,nominal_group_coverage=.95,groups=groups,rank=rank,
                log_bound=bound,factor=math.exp(bound),calibration=data,
                assumption='exchangeable configuration groups in the fixed declared scope; not verified population coverage')


def evaluate(plan,model,calibration,data):
    groups=group_scores(plan,model,data,'test')
    bound=calibration['log_bound']
    for row in groups:
        row['covered']=row['maximum_absolute_log_error']<=bound
        row['ratio_interval']=[row['predicted_ratio']*math.exp(-bound),row['predicted_ratio']*math.exp(bound)]
    return dict(schema=1,groups=groups,test=data,group_count=len(groups),
        groups_covered=sum(r['covered'] for r in groups),
        direction_sign_agreement=sum(r['direction_sign_agreement'] for r in groups),
        repeat_ranges_crossing_one=sum(r['repeat_range_crosses_one'] for r in groups),
        median_ratio_error_factor=statistics.median(r['ratio_error_factor'] for r in groups),
        maximum_ratio_error_factor=max(r['ratio_error_factor'] for r in groups),
        median_gain_error_percentage_points=statistics.median(r['gain_error_percentage_points'] for r in groups),
        maximum_gain_error_percentage_points=max(r['gain_error_percentage_points'] for r in groups))


def main(a):
    plan=read(a.plan)
    if a.stage!='training':
        frozen=read(a.model)
        if frozen['plan_sha256']!=digest(a.plan) or frozen['binary_sha256']!=plan['binary_sha256'] or frozen['engine_sha256']!=digest(__file__):
            raise ValueError('冻结模型、引擎或实验计划身份不同。')
    data=observations(plan,a.run,a.stage)
    if a.stage=='training':
        result=fit(plan,data)
    elif a.stage=='calibration':
        result=calibrate(plan,read(a.model),data)
        result['model_sha256']=digest(a.model)
    else:
        calibration=read(a.calibration)
        if calibration['model_sha256']!=digest(a.model):
            raise ValueError('模型与校准身份不同。')
        result=evaluate(plan,read(a.model),calibration,data)
        result['model_sha256']=digest(a.model)
        result['calibration_sha256']=digest(a.calibration)
    if a.stage!='training' and digest(Path(a.run)/'frozen-model.json')!=digest(a.model):
        raise ValueError('板端冻结模型身份不同。')
    if a.stage=='test' and digest(Path(a.run)/'frozen-calibration.json')!=digest(a.calibration):
        raise ValueError('板端冻结界限身份不同。')
    result['plan_sha256']=digest(a.plan)
    result['binary_sha256']=plan['binary_sha256']
    result['engine_sha256']=digest(__file__)
    write(a.output,result)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=['training','calibration','test'])
    p.add_argument('--plan',type=Path,required=True)
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--model',type=Path)
    p.add_argument('--calibration',type=Path)
    p.add_argument('--output',type=Path,required=True)
    main(p.parse_args())
