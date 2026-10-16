#!/usr/bin/env python3
"""仅用已公开训练与机制数据拟合标量重复写入间隔。"""
import argparse
import copy
import math
from pathlib import Path
import statistics
from common import digest,read,write
import state5

HERE=Path(__file__).resolve().parent


def score(programs,p):
    prepared=state5.prepare_parameters(p)
    errors=[math.log(state5.steady(program,prepared)/actual) for program,actual in programs]
    return statistics.mean(e*e for e in errors)


def main(a):
    prior=read(a.prior);old_plan=read(a.training_plan);probes=read(a.probe_plan)
    diagnostic=read(a.assessment)
    if diagnostic['plan_sha256']!=digest(a.probe_plan):raise ValueError('诊断计划身份不同。')
    if diagnostic['prior_model_sha256']!=digest(a.prior):raise ValueError('诊断模型身份不同。')
    rows=[(r,prior['training']['cycles'][r['id']]) for r in old_plan['records'] if r['split']=='training']
    rows += [(r,diagnostic['observations']['cycles'][r['id']]) for r in probes['records'] if r['role']=='mechanism-probe']
    programs=[(state5.compiled(r),actual) for r,actual in rows]
    p=copy.deepcopy(prior['parameters']);p['write_gap']={f'{a}:{b}':0 for a in ('add','mul','load') for b in ('add','mul','load')}
    initial=score(programs,p);current=initial;history=[]
    for round_number in range(3):
        before=current
        for key in sorted(p['write_gap']):
            best=current;selected=None
            for value in (0,1,2,3,4,5,6,8,10):
                candidate=copy.deepcopy(p);candidate['write_gap'][key]=value
                loss=score(programs,candidate)
                if loss<best-1e-10:best=loss;selected=candidate
            if selected is not None:
                p=selected;current=best;history.append(dict(round=round_number,key=key,value=p['write_gap'][key],loss=current))
        if before-current<1e-10:break
    predictions=[dict(group=r['group'],id=r['id'],cycles=state5.steady(state5.compiled(r),state5.prepare_parameters(p)),observed_cycles=actual) for r,actual in rows]
    write(a.output,dict(schema=5,parameters=p,prior_model_sha256=digest(a.prior),training_plan_sha256=digest(a.training_plan),probe_plan_sha256=digest(a.probe_plan),assessment_sha256=digest(a.assessment),
        training_functions=len(rows),initial_mean_squared_log_error=initial,training_mean_squared_log_error=current,fit_history=history,training_predictions=predictions,
        engine_files={name:digest(HERE/name) for name in ('state5.py','fit-write-r5.py')},prediction_confidence=None,
        limits=['仅修改标量重复写入间隔。','公开的第四轮重排检查不参与拟合。','未宣称全局最优或真实硬件结构。','没有新算法预测置信区间。']))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('prior','training-plan','probe-plan','assessment','output'):p.add_argument('--'+name,type=Path,required=True)
    main(p.parse_args())
