#!/usr/bin/env python3
"""使用已冻结的有限调用参数给出点估计，不生成旧界限或淘汰结论。"""
import argparse
import importlib.util
import json
from pathlib import Path
import time
from common import digest,read,write

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('fragment_fit',HERE/'fragment-fit.py')
fit=importlib.util.module_from_spec(spec);spec.loader.exec_module(fit)
spec=importlib.util.spec_from_file_location('fragment_input_audit',HERE/'fragment-input-audit.py')
input_audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(input_audit)


def predict(model,payload,short,long,output,freeze=None):
    if Path(output).exists():raise ValueError('预测输出已经存在。')
    frozen=read(model)
    if frozen['engine_sha256']!=digest(HERE/'fragment-state.py'):
        raise ValueError('有限时序引擎与冻结模型不同。')
    input_audit.validate(model,payload,short,long,freeze)
    plan=read(Path(payload)/'input-plan.json')
    selected=[(c['id'],k['id']) for c in plan['cases'] for k in plan['kernels']]
    started=time.perf_counter();compiled=fit.programs(payload,short,long,selected)
    compile_seconds=time.perf_counter()-started;started=time.perf_counter()
    values=fit.estimate(compiled,frozen['parameters']);model_seconds=time.perf_counter()-started
    records=[dict(case=case,kernel=kernel,cycles_per_call=value) for (case,kernel),value in zip(selected,values)]
    by_id={(row['case'],row['kernel']):row['cycles_per_call'] for row in records}
    comparisons=[dict(case=case['id'],candidate=k['id'],candidate_over_baseline=by_id[(case['id'],k['id'])]/by_id[(case['id'],plan['baseline'])],retained=True)
                 for case in plan['cases'] for k in plan['kernels'] if k['id']!=plan['baseline']]
    result=dict(status='finite-call-point-estimates',model_sha256=digest(model),
        engine_sha256=frozen['engine_sha256'],binary_sha256=digest(Path(payload)/'fragment'),
        plan_sha256=digest(Path(payload)/'input-plan.json'),records=records,comparisons=comparisons,
        compile_seconds=compile_seconds,model_seconds=model_seconds,prediction_confidence=None,
        automatic_performance_rejection=False,automatic_full_test=False,
        limits=['完整轨迹必须满足解码与调用边界规则。','当前估计采用热访存有效时序。',
                '点估计没有新代码片段的预测置信区间。','旧模型覆盖界限不适用于本入口。',
                '未知缓存状态与生产调用位置仍需小规模原生检查。'])
    write(output,result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('model','payload','short','long','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--freeze',type=Path)
    a=parser.parse_args();result=predict(a.model,a.payload,a.short,a.long,a.output,a.freeze)
    print(json.dumps(dict(status=result['status'],cells=len(result['records']),model_seconds=result['model_seconds'])))
