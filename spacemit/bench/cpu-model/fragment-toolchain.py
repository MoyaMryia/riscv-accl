"""固定片段工具的全部本地运行依赖，拒绝缺失或变化的模块。"""
import argparse
from datetime import datetime,timezone
from pathlib import Path
from common import digest,read,write

HERE=Path(__file__).resolve().parent
FILES=('common.py','binary-input.py','fragment-check.py','fragment-invocation.py',
       'fragment-state.py','fragment-fit.py','fragment-call.py','fragment-trace.c',
       'fragment-input-audit.py','fragment-predict.py','fragment-training-view.py',
       'fragment-assess.py','fragment-evaluate.py','fragment-fit-checked.py',
       'fragment-bind.py','fragment-toolchain.py')


def identities():
    return {name:digest(HERE/name) for name in FILES}


def verify(tools):
    if set(tools)!=set(FILES):raise ValueError('工具依赖清单缺失或包含未知模块。')
    for name,identity in tools.items():
        if digest(HERE/name)!=identity:raise ValueError('冻结工具依赖发生变化：'+name)


def freeze(output):
    result=dict(schema=1,status='fragment-toolchain-frozen',tools=identities(),
        recorded_at_utc=datetime.now(timezone.utc).isoformat())
    write(output,result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();freeze(args.output)
