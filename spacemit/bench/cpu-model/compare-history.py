#!/usr/bin/env python3
"""用冻结引擎检查已公开的正收益循环，保留全部退步。"""
import argparse
from collections import defaultdict
import importlib.util
from pathlib import Path
import statistics
from common import digest,read,write

HERE=Path(__file__).resolve().parent


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


def main(a):
    frozen=read(a.model)
    if frozen['engine_files'].get(a.engine.name)!=digest(a.engine):raise ValueError('冻结引擎身份不同。')
    engine=module('history_engine',a.engine);binary=module('history_binary',HERE/'binary-input.py')
    parameters=engine.prepare_parameters(frozen['parameters']);records=[]
    for root in a.batch:
        plan=read(root/'payload/plan.json');assessment=read(root/'assessment.json')
        if assessment['plan_sha256']!=digest(root/'payload/plan.json'):raise ValueError('历史计划身份不同。')
        if digest(root/'payload/measure')!=plan['binary_sha256']:raise ValueError('历史二进制身份不同。')
        observed=assessment['observations']['cycles'];groups=defaultdict(list)
        for row in plan['records']:
            if row['family']=='reorder':groups[row['group']].append(row)
        for name,rows in sorted(groups.items()):
            rows.sort(key=lambda r:r['arm'])
            if len(rows)!=2 or [r['arm'] for r in rows]!=[0,1]:raise ValueError('历史配对不完整。')
            costs=[engine.steady(engine.compiled(binary.loop(root/'payload/measure',r['id'])),parameters) for r in rows]
            ratio=costs[1]/costs[0];actual=observed[rows[1]['id']]/observed[rows[0]['id']]
            records.append(dict(batch=root.name,group=name,predicted_ratio=ratio,observed_ratio=actual,
                direction_agreement=((ratio>1)-(ratio<1))==((actual>1)-(actual<1)),gain_error_percentage_points=100*abs(ratio-actual),retained=True))
    write(a.output,dict(model_sha256=digest(a.model),groups=len(records),direction_agreement=sum(r['direction_agreement'] for r in records),
        median_gain_error_percentage_points=statistics.median(r['gain_error_percentage_points'] for r in records),maximum_gain_error_percentage_points=max(r['gain_error_percentage_points'] for r in records),
        records=records,limits=['历史正收益数据已经公开。','本检查不是新的独立后测。','本检查不修改冻结模型。']))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('model','engine','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--batch',type=Path,action='append',required=True);main(p.parse_args())
