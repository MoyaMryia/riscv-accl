#!/usr/bin/env python3
"""用已公开机制数据比较标量等待队列假设。"""
import argparse
import copy
from itertools import combinations
import math
from pathlib import Path
import statistics
from common import digest,read,write
import state6

HERE=Path(__file__).resolve().parent


def main(a):
    prior=read(a.prior);old_plan=read(a.training_plan)
    rows=[(r,prior['training']['cycles'][r['id']]) for r in old_plan['records'] if r['split']=='training']
    inputs=[]
    for plan_path,assessment_path in zip(a.probe_plan,a.assessment):
        plan=read(plan_path);assessment=read(assessment_path)
        if digest(plan_path)!=assessment['plan_sha256']:raise ValueError('机制计划身份不同。')
        observed=assessment['observations']['cycles']
        rows += [(r,observed[r['id']]) for r in plan['records'] if r['family']!='reorder']
        inputs.append(dict(plan_sha256=digest(plan_path),assessment_sha256=digest(assessment_path)))
    programs=[(state6.compiled(r),actual) for r,actual in rows]
    candidates=[dict(depth=0,kinds=[],capture='execute',policy='completion',cross_gap=0)]
    for count in (1,2,3):
        for kinds in combinations(('add','mul','load'),count):
            for depth in (1,2,3,4,8,16):
                for policy in ('pending','completion'):
                    for capture in ('ready','execute'):
                        for cross_gap in (0,4,5,6):candidates.append(dict(depth=depth,kinds=list(kinds),capture=capture,policy=policy,cross_gap=cross_gap))
    scores=[];best=math.inf;selected=None
    for config in candidates:
        p=copy.deepcopy(prior['parameters']);p.update(scalar_queue_depth=config['depth'],scalar_queue_kinds=config['kinds'],scalar_capture=config['capture'],waw_policy=config['policy'])
        if config['cross_gap']:
            p['write_gap']={f'{a}:{b}':config['cross_gap'] if (a=='mul')!=(b=='mul') else 1 if a!='mul' else 0 for a in ('add','mul','load') for b in ('add','mul','load')}
        prepared=state6.prepare_parameters(p)
        try:
            predictions=[state6.steady(program,prepared) for program,actual in programs]
            loss=statistics.mean(math.log(pred/actual)**2 for pred,(_,actual) in zip(predictions,programs))
        except ValueError as exc:
            scores.append(dict(**config,status='no-steady-period',reason=str(exc)));continue
        scores.append(dict(**config,status='complete',mean_squared_log_error=loss))
        if loss<best-1e-10:best=loss;selected=p
    if selected is None:raise ValueError('所有假设均无法形成稳态。')
    write(a.output,dict(schema=6,parameters=selected,training_functions=len(rows),training_mean_squared_log_error=best,candidate_scores=scores,
        prior_model_sha256=digest(a.prior),training_plan_sha256=digest(a.training_plan),diagnostic_inputs=inputs,
        engine_files={name:digest(HERE/name) for name in ('state6.py','fit-queue-r6.py')},prediction_confidence=None,
        limits=['全部队列配置均保留。','有限假设搜索不能确定真实硬件结构。','旧重排后测不参与拟合。','旧校准界限不转用。']))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('prior','training-plan','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('probe-plan','assessment'):p.add_argument('--'+name,type=Path,action='append',required=True)
    main(p.parse_args())
