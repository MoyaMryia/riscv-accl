#!/usr/bin/env python3
"""检查训练等效参数对新组合预测的影响。"""
import argparse
from pathlib import Path
from common import digest,read,write
import state3 as state


def main(a):
    frozen=read(a.model);plan=read(a.plan)
    if digest(a.plan)!=frozen['plan_sha256'] or digest(Path(state.__file__))!=frozen['engine_files']['state3.py']:
        raise ValueError('计划或状态引擎身份不同。')
    variants=[]
    for row in frozen['training_equivalent_single_parameter_variants']:
        p=state.prepare_parameters(row['parameters'])
        predictions={r['id']:state.steady(state.compiled(r),p) for r in plan['records']}
        changes={identifier:predictions[identifier]/cycles-1 for identifier,cycles in frozen['predictions'].items()}
        variants.append(dict(key=row['key'],value=row['value'],maximum_absolute_relative_prediction_change=max(abs(v) for v in changes.values()),
            changes={k:v for k,v in changes.items() if v!=0}))
    write(a.output,dict(schema=1,model_sha256=digest(a.model),variants=variants,
        limits=['本范围表示模型假设敏感度，不是预测置信区间。','训练等效只按本轮拟合目标判断。','单参数变体不能覆盖全部等效模型。']))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model',type=Path,required=True)
    p.add_argument('--plan',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    main(p.parse_args())
