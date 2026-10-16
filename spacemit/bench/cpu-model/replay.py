#!/usr/bin/env python3
"""用标准 Python 重放冻结 CPU 模型的受控循环预测。"""
import argparse
import hashlib
import json
import os
import resource
import sys
from pathlib import Path
import time
from common import digest, read, write
from model import predict
import model


def main(a):
    total_start=time.perf_counter()
    root=a.root.resolve()
    frozen=read(root/'frozen-model.json')
    if digest(Path(model.__file__))!=frozen['engine_sha256']:
        raise ValueError('模型引擎与冻结版本不同。')
    if digest(root/'plan.json')!=frozen['plan_sha256']:
        raise ValueError('实验计划与冻结版本不同。')
    for line in (root/'SHA256SUMS').read_text().splitlines():
        expected,name=line.split('  ',1)
        path=(root/name).resolve()
        if not path.is_relative_to(root) or digest(path)!=expected:
            raise ValueError('便携包收据不同。')
    start=time.perf_counter()
    predictions={row['id']:predict(row,frozen['parameters'],128) for row in read(root/'plan.json')['records']}
    elapsed=time.perf_counter()-start
    if predictions!=frozen['predictions']:
        raise ValueError('预测与冻结记录不同。')
    canonical=json.dumps(predictions,sort_keys=True,separators=(',',':')).encode()
    result=dict(schema=1,model_sha256=digest(root/'frozen-model.json'),predictions=predictions,
                prediction_sha256=hashlib.sha256(canonical).hexdigest(),records=len(predictions))
    write(a.output,result)
    print(json.dumps(dict(status='passed',records=len(predictions),prediction_sha256=result['prediction_sha256'],model_seconds=elapsed,total_seconds=time.perf_counter()-total_start,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,host=dict(zip(('sysname','nodename','release','version','machine'),os.uname())),python=sys.version)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    p.add_argument('--output',type=Path,required=True)
    main(p.parse_args())
