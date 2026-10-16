#!/usr/bin/env python3
"""拟合第三轮状态模型，并冻结新组合的独立检查。"""
import argparse
from collections import defaultdict
import copy
import math
from pathlib import Path
import statistics
from common import digest,read,write
import model
import state3 as state
from audit import receipts

HERE=Path(__file__).resolve().parent
PAIR_KEYS=('add:mul','mul:add','add:load','load:add','mul:load','load:mul','vadd:ime','ime:vadd','ime:vload','vload:ime')


def engine_identity():
    return {name:digest(HERE/name) for name in ('fit-r3.py','state3.py','model.py','common.py','audit.py')}


def coordinates():
    for key in ('width','scalar_units','lsu_units'):
        yield key,(1,2)
    for key in ('shared_vector','waw','separate_multiply'):
        yield key,(False,True)
    yield 'multiply_units',(1,2)
    yield 'waw_policy',('pending','completion','scalar-completion')
    yield 'branch_boundary_gap',(0,1)
    yield 'arithmetic_queue_depth',(0,1,2,4,8,16)
    yield 'read_hold_ime',(0,1,2,3,4,5,6,8,10,12,16)
    for table,keys in [('latency',model.KINDS),('occupancy',model.KINDS),('bypass',('add:mul','mul:add','load:add','load:mul')),('vector_gap',('vadd:ime','ime:vadd','vload:ime','ime:vload','vload:vadd','vadd:vload'))]:
        for key in keys:
            yield (table,key),(1,2,3,4,5,6,8,10,12,16)
    for key in PAIR_KEYS:
        yield ('pair',key),(False,True)


def changed(p,key,value):
    result=copy.deepcopy(p)
    if isinstance(key,tuple):
        table,name=key
        if table=='pair':
            current=set(result['forbidden_pairs'])
            if value:current.add(name)
            else:current.discard(name)
            result['forbidden_pairs']=sorted(current)
        else:result[table][name]=value
    else:result[key]=value
    return result


def loss(programs,p):
    if p['read_hold_ime']>p['latency']['ime']:
        return math.inf
    prepared=state.prepare_parameters(p)
    errors=[math.log(state.steady(program,prepared)/actual) for program,actual in programs]
    return statistics.mean(error*error for error in errors)


def fit(plan,data,prior):
    rows=[r for r in plan['records'] if r['split']=='training']
    programs=[(state.compiled(r),data['cycles'][r['id']]) for r in rows]
    p=copy.deepcopy(prior['parameters'])
    p.setdefault('waw_policy','pending')
    p.setdefault('separate_multiply',False)
    p.setdefault('multiply_units',1)
    for key in ('vload:ime','ime:vload','vload:vadd','vadd:vload'):
        p['vector_gap'].setdefault(key,0)
    p.setdefault('branch_boundary_gap',1)
    p.setdefault('forbidden_pairs',[])
    p.setdefault('arithmetic_queue_depth',0)
    seed_scores=[]
    selected=copy.deepcopy(p)
    current=loss(programs,p)
    for separate in (False,True):
        for multiply_occupancy in (1,3,6):
            for policy in ('pending','completion','scalar-completion'):
                candidate=copy.deepcopy(p)
                candidate.update(separate_multiply=separate,waw_policy=policy,multiply_units=1)
                candidate['occupancy']['mul']=multiply_occupancy
                if policy=='completion':candidate['occupancy']['vload']=3
                value=loss(programs,candidate)
                seed_scores.append(dict(separate_multiply=separate,multiply_occupancy=multiply_occupancy,
                    waw_policy=policy,mean_squared_log_error=value))
                if value<current-1e-10:selected,current=candidate,value
    p=selected
    history=[]
    for pass_number in range(4):
        before=current
        for key,values in coordinates():
            best,current_p,best_value=current,None,None
            for value in values:
                candidate=changed(p,key,value)
                error=loss(programs,candidate)
                if error<best-1e-10:
                    best,current_p,best_value=error,candidate,value
            if current_p is not None:
                p=current_p;current=best
                history.append(dict(pass_number=pass_number,key=key,value=best_value,mean_squared_log_error=current))
        if before-current<1e-10:
            break
    prepared=state.prepare_parameters(p)
    predictions={r['id']:state.steady(state.compiled(r),prepared) for r in plan['records']}
    finite={r['id']:state.execute(state.compiled(r),prepared,384) for r in plan['records']}
    difference=max(abs(finite[k]/value-1) for k,value in predictions.items())
    equivalents=[]
    for key,values in coordinates():
        for value in values:
            candidate=changed(p,key,value)
            if candidate!=p and abs(loss(programs,candidate)-current)<1e-8:
                equivalents.append(dict(key=key,value=value,parameters=candidate))
    return dict(schema=2,parameters=p,predictions=predictions,training=data,
        training_mean_squared_log_error=current,fit_history=history,initial_seed_scores=seed_scores,
        training_equivalent_single_parameter_variants=equivalents,
        steady_period_vs_384_max_relative_difference=difference,
        fit_method='18 fixed joint seeds and four coordinate passes; exact model period; no global optimum claim',
        limits=['effective timing; hardware structure and parameter identity are not established',
                'no operand-value timing, cache miss, branch recovery or shared-memory model',
                'three-class holdout is not arbitrary-algorithm validation'])


def groups(plan,frozen,data,split):
    index=defaultdict(list)
    for row in plan['records']:
        if row['split']==split:
            index[row['group']].append(row)
    result=[]
    for name,rows in sorted(index.items()):
        if len(rows)!=4:
            raise ValueError('组必须包含两个展开版本与两个操作顺序。')
        variants=[]
        for unroll in (2,3):
            arms=sorted([r for r in rows if r['unroll']==unroll],key=lambda r:r['arm'])
            if [r['arm'] for r in arms]!=[0,1]:
                raise ValueError('展开版本的两臂不完整。')
            identifiers=[r['id'] for r in arms]
            predicted=[frozen['predictions'][k] for k in identifiers]
            actual=[data['cycles'][k] for k in identifiers]
            ratio,truth=predicted[1]/predicted[0],actual[1]/actual[0]
            score=max([abs(math.log(p/a)) for p,a in zip(predicted,actual)]+[abs(math.log(ratio/truth))])
            repeated=[data['slopes'][identifiers[1]][k]/v for k,v in data['slopes'][identifiers[0]].items()]
            variants.append(dict(unroll=unroll,ids=identifiers,predicted_cycles=predicted,observed_cycles=actual,
                predicted_ratio=ratio,observed_ratio=truth,maximum_absolute_log_error=score,
                ratio_error_factor=math.exp(abs(math.log(ratio/truth))),gain_error_percentage_points=100*abs(ratio-truth),
                predicted_direction='faster' if ratio<1 else 'slower' if ratio>1 else 'neutral',
                direction_sign_agreement=((ratio>1)-(ratio<1))==((truth>1)-(truth<1)),
                observed_gain_below_one_percent=abs(truth-1)<.01,
                paired_repeat_ratio_range=[min(repeated),max(repeated)],repeat_range_crosses_one=min(repeated)<=1<=max(repeated)))
        result.append(dict(group=name,kinds=rows[0]['kinds'],chains=rows[0]['chains'],variants=variants,
            maximum_absolute_log_error=max(r['maximum_absolute_log_error'] for r in variants)))
    return result


def check_equivalence(plan,run,qemu_dumps):
    # 原生与 QEMU 的同名文件比较由 audit.py 完成。
    index=defaultdict(list)
    for row in plan['records']:
        index[row['group'],row['unroll']].append(row)
    count=0
    for rows in index.values():
        arms=sorted(rows,key=lambda row:row['arm'])
        if len(arms)<2:continue
        for n in plan['dump_lengths']:
            names=[f'{row["id"]}-{n}.bin' for row in arms]
            native=[Path(run)/'dumps'/name for name in names]
            if all(path.exists() for path in native):
                if any(path.read_bytes()!=native[0].read_bytes() for path in native[1:]):
                    raise ValueError('原生同组完整输出不同。')
                count+=len(native)-1
            if qemu_dumps:
                qemu=[Path(qemu_dumps)/name for name in names]
                if any(path.read_bytes()!=qemu[0].read_bytes() for path in qemu[1:]):
                    raise ValueError('QEMU 同组完整输出不同。')
    return count



def main(a):
    plan=read(a.plan)
    receipts(a.run)
    data=model.observations(plan,a.run,a.stage)
    equivalents=check_equivalence(plan,a.run,a.qemu_dumps)
    if a.stage=='training':
        result=fit(plan,data,read(a.prior))
        result['prior_model_sha256']=digest(a.prior)
    else:
        frozen=read(a.model)
        if frozen['engine_files']!=engine_identity() or frozen['plan_sha256']!=digest(a.plan):
            raise ValueError('冻结引擎或计划身份不同。')
        if digest(Path(a.run)/'frozen-model.json')!=digest(a.model):
            raise ValueError('板端冻结模型身份不同。')
        records=groups(plan,frozen,data,a.stage)
        if a.stage=='calibration':
            rank=math.ceil((len(records)+1)*.95)
            if rank>len(records):raise ValueError('校准组不足。')
            bound=sorted(r['maximum_absolute_log_error'] for r in records)[rank-1]
            result=dict(schema=2,groups=records,calibration=data,nominal_group_coverage=.95,rank=rank,
                log_bound=bound,factor=math.exp(bound),
                assumption='exchangeable fixed-scope groups; population coverage is not established')
        else:
            calibration=read(a.calibration)
            if calibration['model_sha256']!=digest(a.model) or digest(Path(a.run)/'frozen-calibration.json')!=digest(a.calibration):
                raise ValueError('校准身份不同。')
            for row in records:
                row['covered']=row['maximum_absolute_log_error']<=calibration['log_bound']
                for variant in row['variants']:
                    variant['covered']=variant['maximum_absolute_log_error']<=calibration['log_bound']
                    variant['ratio_interval']=[variant['predicted_ratio']/calibration['factor'],variant['predicted_ratio']*calibration['factor']]
            flat=[v for row in records for v in row['variants']]
            result=dict(schema=2,groups=records,test=data,group_count=len(records),groups_covered=sum(r['covered'] for r in records),
                versions=len(flat),versions_covered=sum(v['covered'] for v in flat),direction_sign_agreement=sum(v['direction_sign_agreement'] for v in flat),
                observed_gain_below_one_percent=sum(v['observed_gain_below_one_percent'] for v in flat),
                median_ratio_error_factor=statistics.median(v['ratio_error_factor'] for v in flat),maximum_ratio_error_factor=max(v['ratio_error_factor'] for v in flat),
                median_gain_error_percentage_points=statistics.median(v['gain_error_percentage_points'] for v in flat),maximum_gain_error_percentage_points=max(v['gain_error_percentage_points'] for v in flat),
                calibration_sha256=digest(a.calibration))
        result['model_sha256']=digest(a.model)
    result.update(plan_sha256=digest(a.plan),binary_sha256=plan['binary_sha256'],engine_files=engine_identity(),native_equivalent_dump_pairs=equivalents)
    write(a.output,result)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=['training','calibration','test'])
    p.add_argument('--plan',type=Path,required=True)
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--prior',type=Path)
    p.add_argument('--model',type=Path)
    p.add_argument('--calibration',type=Path)
    p.add_argument('--qemu-dumps',type=Path)
    p.add_argument('--output',type=Path,required=True)
    main(p.parse_args())
