#!/usr/bin/env python3
"""重放 IME 混合循环的冻结点预测与宽误差界限。"""
import argparse
import importlib.util
from pathlib import Path
from analyze import load, write, sha, seal
from k1cost import parameters, model_identity

HERE=Path(__file__).resolve().parent


def main(output):
    example=HERE/'examples/ime-mix-v7'
    plan=load(example/'plan.json');model=load(example/'model.json')
    manifest=load(example/'manifest.json');points=load(example/'points.json')
    for name,value in manifest['files_sha256'].items():
        if sha(example/name)!=value:raise ValueError('便携 IME 证据文件不同。')
    spec=importlib.util.spec_from_file_location('ime_mix_audit',HERE/'ime-mix-evaluate.py')
    audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
    if audit.implementation()!=model['implementation_sha256']:
        raise ValueError('冻结 IME 误差实现不同。')
    paths=[HERE/'profiles/k1-cpu0-umode-20261012'/name for name in
        ('components.json','ime.json','reductions.json','scalar.json','gaps.json')]
    _,profiles=parameters(paths);identity,_=model_identity(profiles)
    if identity!=model['model_sha256'] or sha(example/'plan.json')!=model['plan_sha256']:
        raise ValueError('冻结模型或适用计划不同。')
    bound=load(example/'calibration.json')
    audit.verify_bound(bound,plan,sha(example/'plan.json'),manifest['actual_predictions_sha256'])
    import math
    factor=math.exp(bound['maximum_group_log_error'])
    indexed={(r['group'],r['arm'],r['unroll']):r['cycles_per_loop'] for r in points['records']}
    expected={(r['group'],r['arm'],r['operations']) for r in plan['records']}
    if len(indexed)!=len(points['records']) or set(indexed)!=expected:
        raise ValueError('冻结点预测矩阵不同。')
    records=[]
    for group in plan['groups']:
        if group['split']!='test':continue
        variants=[]
        for unroll in (8,32,128):
            control=indexed[group['id'],0,unroll];candidate=indexed[group['id'],1,unroll]
            ratio=candidate/control
            variants.append(dict(unroll=unroll,predicted_control_cycles=control,
                predicted_candidate_cycles=candidate,predicted_ratio=ratio,predicted_gain=1-ratio,
                gain_interval=[1-ratio*factor,1-ratio/factor]))
        records.append(dict(group=group['id'],variants=variants))
    output.mkdir(parents=True,exist_ok=False)
    write(output/'prediction.json',dict(schema=7,model_sha256=identity,
        calibration_sha256=bound['calibration_sha256'],records=records,automatic_action='none',
        limits=bound['limits']+['wide calibrated bounds do not make incorrect point directions useful']))
    (output/'report.md').write_text('''# IME 混合循环失败检查

全部候选均保留。
冻结区间观测覆盖为 9/9 组和 27/27 个展开版本。
原始点预测的方向符号一致性仅为 9/27。
部分单链配置的实测差异接近零，方向符号不代表有统计依据的变化。
比值误差因子约为 2.12，区间不能确认多数投入顺序。
宽区间不能修复点预测的方向错误。
该模型需要补充组合时序，不能用于任意新 IME 算法的高置信判断。
本次观测不能确认总体 95% 覆盖率。
''')
    seal(output)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    main(p.parse_args().output.resolve())
