#!/usr/bin/env python3
"""仅用固定训练观测拟合完整调用时序，保留全部搜索候选。"""
import argparse
import copy
import importlib.util
import json
import math
from pathlib import Path
import time
from common import digest,read,write

HERE=Path(__file__).resolve().parent


def load(name):
    spec=importlib.util.spec_from_file_location(name.replace('-','_'),HERE/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


state=load('fragment-state');invocation=load('fragment-invocation');checker=load('fragment-check')


def programs(payload,short,long,selection):
    payload,short,long=map(Path,(payload,short,long))
    for root in (payload,short,long):checker.receipts(root)
    plan=read(payload/'input-plan.json');a=read(short/'result.json');b=read(long/'result.json')
    if a['binary_sha256']!=digest(payload/'fragment') or b['binary_sha256']!=a['binary_sha256']:
        raise ValueError('调用差值的二进制身份不同。')
    counts=[a['trace_calls'],b['trace_calls']]
    if not 0<counts[0]<counts[1]:raise ValueError('调用差值次数无效。')
    kernels={row['id']:row for row in plan['kernels']};result=[]
    for case,kernel in selection:
        pair=[]
        entry,_=invocation.binary.function(payload/'fragment',kernels[kernel]['symbol'])
        for folder,count in zip((short,long),counts):
            name=case+'-'+kernel
            audit,rows=invocation.audit(folder/(name+'-cpu0.jsonl'),payload/'fragment','fragment_repeat')
            if sum(row['pc']==entry for row in rows)!=count:
                raise ValueError('实际目标函数进入次数不同。')
            pair.append(state.compile_trace(rows))
        result.append(dict(case=case,kernel=kernel,short=pair[0],long=pair[1],counts=counts))
    return result


def estimate(programs,parameters):
    return [state.slope(row['short'],row['long'],row['counts'],parameters)['cycles_per_call'] for row in programs]


def fit(payload,short,long,prior,grid,training,freeze,output):
    output=Path(output)
    if output.exists():raise ValueError('冻结模型输出已经存在。')
    frozen=read(freeze);prior_data=read(prior);grid_data=read(grid);view=read(training)
    if digest(prior)!=frozen['prior_model_sha256'] or digest(grid)!=frozen['parameter_grid_sha256']:
        raise ValueError('原模型或搜索网格身份不同。')
    if digest(HERE/'fragment-fit.py')!=frozen['fit_tool_sha256']:
        raise ValueError('预先固定的拟合程序不同。')
    for name in ('fragment-state.py','fragment-invocation.py'):
        if digest(HERE/name)!=frozen['tools'][name]:raise ValueError('预先固定的时序或解码工具不同。')
    plan=read(Path(payload)/'input-plan.json')
    if digest(Path(payload)/'input-plan.json')!=frozen['plan_sha256'] or digest(Path(payload)/'fragment')!=frozen['binary_sha256']:
        raise ValueError('预先固定的输入计划或 ELF 不同。')
    if view['plan_sha256']!=frozen['plan_sha256'] or view['binary_sha256']!=frozen['binary_sha256']:
        raise ValueError('训练观测不属于当前输入计划。')
    expected={(c['id'],k['id']) for c in plan['cases'] if c['split']=='training' for k in plan['kernels']}
    selected=[(r['case'],r['kernel']) for r in view['records']]
    if len(selected)!=len(expected) or set(selected)!=expected or view['split']!='training':
        raise ValueError('训练视图包含未声明或缺失的单元。')
    actual=[r['cycles_per_call'] for r in view['records']]
    if any(not math.isfinite(value) or value<=0 for value in actual):raise ValueError('训练周期必须为正数。')
    started=time.perf_counter();compiled=programs(payload,short,long,selected);compile_seconds=time.perf_counter()-started
    p=state.initial_parameters(prior_data['parameters']);cache={};history=[]
    def score(parameters):
        key=json.dumps(parameters,sort_keys=True)
        if key not in cache:
            values=estimate(compiled,parameters)
            loss=math.fsum(math.log(predicted/observed)**2 for predicted,observed in zip(values,actual))/len(actual)
            cache[key]=loss,values
        return cache[key]
    initial,initial_predictions=score(p);best=initial;started=time.perf_counter()
    for round_number in range(grid_data['maximum_rounds']):
        before=best
        for key,values in grid_data['parameters']:
            choice=p;current=best
            for value in values:
                candidate=copy.deepcopy(p);candidate[key]=value
                loss,_=score(candidate)
                history.append(dict(round=round_number,parameter=key,value=value,loss=loss,retained=True))
                if loss<current-1e-12:choice=candidate;current=loss
            p=choice;best=current
        write(output.with_suffix(f'.progress-round{round_number}.json'),dict(round=round_number,training_loss=best,candidates=len(history)))
        if before-best<1e-12:break
    final,predictions=score(p)
    result=dict(schema=1,status='finite-call-model-frozen',parameters=p,
        prior_model_sha256=digest(prior),pre_native_freeze_sha256=digest(freeze),
        training_view_sha256=digest(training),parameter_grid_sha256=digest(grid),
        binary_sha256=digest(Path(payload)/'fragment'),training_cells=len(selected),
        engine_sha256=digest(HERE/'fragment-state.py'),fit_tool_sha256=digest(HERE/'fragment-fit.py'),
        trace_receipts=[digest(Path(root)/'SHA256SUMS') for root in (short,long)],
        initial_training_loss=initial,training_loss=final,history=history,
        training_predictions=[dict(case=row['case'],kernel=row['kernel'],observed_cycles=observed,
            initial_cycles=old,cycles=predicted) for row,observed,old,predicted in zip(compiled,actual,initial_predictions,predictions)],
        compile_seconds=compile_seconds,fit_seconds=time.perf_counter()-started,
        prediction_confidence=None,automatic_performance_rejection=False,
        limits=['仅使用固定机制训练单元。','旧模型界限不转移到完整调用模型。',
                '本轮没有总体覆盖保证或新算法族精度证明。','有效时序参数不证明真实硬件结构。'])
    write(output,result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('payload','short','long','prior','grid','training','freeze','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args();result=fit(a.payload,a.short,a.long,a.prior,a.grid,a.training,a.freeze,a.output)
    print(json.dumps(dict(status=result['status'],training_cells=result['training_cells'],loss=result['training_loss'])))
