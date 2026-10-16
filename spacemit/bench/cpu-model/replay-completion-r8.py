#!/usr/bin/env python3
"""从固定实际 ELF 重放第八轮模型，不转用旧校准界限。"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import time
from common import digest, read, write


def replay(root):
    started = time.perf_counter()
    root = Path(root)
    plan, frozen = read(root / 'plan.json'), read(root / 'frozen-model.json')
    expected = read(root / 'frozen-predictions.json')
    if digest(root / 'measure') != plan['binary_sha256'] or digest(root / 'plan.json') != frozen['training_plan_sha256']:
        raise ValueError('实际输入身份不同。')
    if digest(root / 'frozen-model.json') != expected['model_sha256']:
        raise ValueError('模型身份不同。')
    if digest(root / 'state8.py') != frozen['engine_files']['state8.py']:
        raise ValueError('冻结引擎身份不同。')
    engine_spec = importlib.util.spec_from_file_location('completion_engine', root / 'state8.py')
    state8 = importlib.util.module_from_spec(engine_spec)
    engine_spec.loader.exec_module(state8)
    spec = importlib.util.spec_from_file_location('completion_binary', root / 'binary-input.py')
    binary = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(binary)
    parameters = state8.prepare_parameters(frozen['parameters'])
    values = {}
    for row in plan['records']:
        body = binary.loop(root / 'measure', row['id'])
        values[row['id']] = state8.steady(state8.compiled(body), parameters)
    payload = json.dumps(values, sort_keys=True, separators=(',', ':')).encode()
    checksum = hashlib.sha256(payload).hexdigest()
    if values != expected['predictions'] or checksum != expected['prediction_sha256']:
        raise ValueError('实际二进制预测与冻结清单不同。')
    elapsed = time.perf_counter() - started
    return dict(schema=8, functions=len(values), prediction_sha256=checksum, model_sha256=digest(root / 'frozen-model.json'),
        predictions=values, prediction_confidence=None, host=list(os.uname()), elapsed_seconds=elapsed,
        maximum_resident_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        limits=['时间包含身份核验、ELF 解码与模型计算。', '时间不包含进程启动、动态轨迹采集、程序构建或结果写入。',
            '仅覆盖本包固定热只读标量循环。', '模型重放一致不能证明新算法精度。'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    write(args.output, replay(args.root))
