#!/usr/bin/env python3
"""重放第二轮冻结状态模型，不重新拟合或调整界限。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import time
from common import digest,read,write
import state


def main(a):
    start=time.perf_counter();root=a.root.resolve()
    for line in (root/'SHA256SUMS').read_text().splitlines():
        expected,name=line.split('  ',1);path=(root/name).resolve()
        if not path.is_relative_to(root) or digest(path)!=expected:
            raise ValueError('便携包收据不同。')
    frozen=read(root/'frozen-model.json')
    for name,expected in frozen['engine_files'].items():
        if digest(root/name)!=expected:
            raise ValueError('冻结引擎文件身份不同。')
    if digest(root/'plan.json')!=frozen['plan_sha256'] or digest(Path(state.__file__))!=frozen['engine_files']['state.py']:
        raise ValueError('实际计划或状态引擎不同。')
    prepared=state.prepare_parameters(frozen['parameters'])
    model_start=time.perf_counter()
    predictions={row['id']:state.steady(state.compiled(row),prepared) for row in read(root/'plan.json')['records']}
    model_seconds=time.perf_counter()-model_start
    if predictions!=frozen['predictions']:
        raise ValueError('预测与冻结记录不同。')
    canonical=json.dumps(predictions,sort_keys=True,separators=(',',':')).encode()
    result=dict(schema=2,model_sha256=digest(root/'frozen-model.json'),predictions=predictions,
        prediction_sha256=hashlib.sha256(canonical).hexdigest(),records=len(predictions))
    write(a.output,result)
    print(json.dumps(dict(status='passed',records=len(predictions),prediction_sha256=result['prediction_sha256'],
        model_seconds=model_seconds,total_seconds=time.perf_counter()-start,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        host=dict(zip(('sysname','nodename','release','version','machine'),os.uname())),python=sys.version)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    p.add_argument('--output',type=Path,required=True)
    main(p.parse_args())
