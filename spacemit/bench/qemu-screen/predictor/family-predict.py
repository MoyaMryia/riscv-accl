#!/usr/bin/env python3
"""在其他机器上重放冻结的完整算子模型和误差界限。"""
import argparse
import importlib.util
from pathlib import Path
import time
from analyze import load,write,sha,seal
from priority import conformal

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('family_model',HERE/'family-model.py')
family=importlib.util.module_from_spec(spec);spec.loader.exec_module(family)


def main(a):
    if not .5<a.coverage<1:raise ValueError('覆盖率必须位于 0.5 与 1 之间。')
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    model=load(a.model);family.verify_model(model);features=load(a.features);plan=load(a.plan)
    calibration=load(a.calibration)
    if sha(a.plan)!=model['plan_sha256'] or features['plan_sha256']!=sha(a.plan):raise ValueError('预测计划身份不同。')
    if features['binary_sha256']!=model['binary_sha256'] or features['extractor_sha256']!=model['extractor_sha256']:
        raise ValueError('预测二进制或特征实现不同。')
    if features['feature_names']!=model['feature_names'] or features['domain']!=model['domain']:
        raise ValueError('预测特征范围不同。')
    if calibration['split']!='calibration':raise ValueError('误差校准分组不同。')
    expected={c['id'] for c in plan['cases'] if c['split']=='calibration'}
    if {r['group'] for r in calibration['records']}!=expected:raise ValueError('误差校准组不完整。')
    values={(r['id'],r['arm']):r['features'] for r in features['records']}
    if len(values)!=len(features['records']):raise ValueError('动态特征重复。')
    allowed={c['id'] for c in plan['cases'] if c['split']=='test'}
    groups=a.groups or sorted(allowed)
    if not set(groups)<=allowed:raise ValueError('当前预测示例只接受预留形状组。其他算法必须建立新的范围与误差校准。')
    start=time.perf_counter();records=[]
    for group in groups:
        control=family.estimate(model,values[group,0]);candidate=family.estimate(model,values[group,1]);ratio=candidate/control
        error,meta=conformal(calibration,model['model_sha256'],a.coverage,group,model['domain'])
        if error is None:raise ValueError('误差校准不能产生有限界限。')
        import math
        low=1-ratio*math.exp(error);high=1-ratio*math.exp(-error)
        records.append(dict(id=group,predicted_control_ms=control,predicted_candidate_ms=candidate,
            predicted_gain=1-ratio,gain_interval=[low,high],calibration=meta,
            direction='faster' if low>0 else 'slower' if high<0 else 'uncertain',automatic_action='none'))
    write(out/'prediction.json',dict(schema=3,kind='frozen-full-operator-domain-example',domain=model['domain'],
        model_sha256=model['model_sha256'],calibration_sha256=sha(a.calibration),records=records,
        calculation_seconds=time.perf_counter()-start,automatic_action='none',
        limits=model['limits']+['interval coverage assumes exchangeable groups within this fixed domain',
            'comparison across different workload shapes does not select a universal algorithm winner']))
    seal(out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('model',type=Path)
    p.add_argument('--features',type=Path,required=True);p.add_argument('--plan',type=Path,required=True)
    p.add_argument('--calibration',type=Path,required=True);p.add_argument('--coverage',type=float,default=.95)
    p.add_argument('--groups',nargs='+');p.add_argument('--output',type=Path,required=True);main(p.parse_args())
