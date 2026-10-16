#!/usr/bin/env python3
"""发布第八轮实际二进制的标准 Python 重放包。"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from common import digest, read, seal, write
from snapshot import publish
import state8

HERE = Path(__file__).resolve().parent


def freeze(root):
    frozen = read(root / 'frozen-model.json')
    plan = read(root / 'payload/plan.json')
    if frozen['engine_files']['state8.py'] != digest(HERE / 'state8.py'):
        raise ValueError('冻结引擎身份不同。')
    parameters = state8.prepare_parameters(frozen['parameters'])
    values = {r['id']: state8.steady(state8.compiled(r), parameters) for r in plan['records']}
    checksum = hashlib.sha256(json.dumps(values, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    write(root / 'frozen-predictions.json', dict(model_sha256=digest(root / 'frozen-model.json'), prediction_sha256=checksum, predictions=values))


def bundle(root, output):
    portable = root / 'portable'
    portable.mkdir()
    for name in ('common.py', 'state8.py', 'binary-input.py', 'replay-completion-r8.py', 'fit-completion-r8.py'):
        shutil.copyfile(HERE / name, portable / name)
    for name in ('frozen-model.json', 'frozen-predictions.json', 'frozen-calibration.json', 'evaluation.json'):
        shutil.copyfile(root / name, portable / name)
    for name in ('measure', 'plan.json', 'protocol.md'):
        shutil.copyfile(root / 'payload' / name, portable / name)
    seal(portable)
    write(root / 'portable-receipt.json', publish(portable, output))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['freeze', 'bundle'])
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.action == 'bundle' and args.output is None:
        parser.error('发布便携包必须指定输出路径。')
    freeze(args.work) if args.action == 'freeze' else bundle(args.work, args.output)
