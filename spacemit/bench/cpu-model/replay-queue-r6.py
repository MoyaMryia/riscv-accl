#!/usr/bin/env python3
"""从固定实际二进制重放第六轮的两个冻结模型。"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from common import digest,read,write
import state3
import state6


def replay(root):
    root=Path(root);plan=read(root/'plan.json');old=read(root/'prior-model.json');new=read(root/'frozen-model.json')
    if digest(root/'measure')!=plan['binary_sha256']:raise ValueError('实际二进制身份不同。')
    if digest(root/'prior-model.json')!=plan['prior_model_sha256'] or digest(root/'frozen-model.json')!=plan['model_sha256']:raise ValueError('冻结模型身份不同。')
    for engine,record in (('state3.py',old),('state6.py',new)):
        if digest(root/engine)!=record['engine_files'][engine]:raise ValueError('冻结引擎身份不同。')
    spec=importlib.util.spec_from_file_location('binary_input_r6',root/'binary-input.py')
    binary=importlib.util.module_from_spec(spec);spec.loader.exec_module(binary)
    values={}
    for row in plan['records']:
        actual=binary.loop(root/'measure',row['id'])
        record=dict(instructions=actual['instructions'])
        costs=[state3.steady(state3.compiled(record),state3.prepare_parameters(old['parameters'])),state6.steady(state6.compiled(record),state6.prepare_parameters(new['parameters']))]
        if costs!=[row['old_predicted_cycles'],row['predicted_cycles']]:raise ValueError('实际二进制预测与冻结清单不同。')
        values[row['id']]=costs
    payload=json.dumps(values,sort_keys=True,separators=(',',':')).encode()
    return dict(schema=6,functions=len(values),prediction_sha256=hashlib.sha256(payload).hexdigest(),model_sha256=digest(root/'frozen-model.json'),
        prior_model_sha256=digest(root/'prior-model.json'),predictions=values,prediction_confidence=None,
        limits=['仅覆盖本包的固定标量循环。','不包含动态轨迹采集成本。','旧误差界限不转用。'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();write(a.output,replay(a.root))
